import math
from pathlib import Path
from typing import Dict, Optional

import numpy as np


class MIHMAcousticExtractor:
    WEIGHTS = {
        "F_s": 0.100,
        "G_f": 0.100,
        "C_s": 0.100,
        "R_sem": 0.100,
        "C_sem": 0.100,
        "Phi": 0.100,
        "I_mc": 0.083,
        "E_r": 0.083,
        "V_i": 0.083,
        "D_i": 0.075,
        "D_cog": 0.075,
    }

    CORE = ["F_s", "D_i", "E_r", "C_s", "D_cog", "G_f"]

    def __init__(self, audio_path: str):
        self.audio_path = Path(audio_path)
        if not self.audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")

        try:
            import librosa
            self.librosa = librosa
        except Exception as exc:
            raise ImportError(
                "librosa is required for real MIHM audio extraction. "
                "Install with: pip install librosa soundfile scipy"
            ) from exc

        self.y, self.sr = self.librosa.load(str(self.audio_path), sr=None, mono=False)

        if self.y.ndim == 1:
            self.y_mono = self.y
            self.channels = 1
        else:
            self.channels = self.y.shape[0]
            self.y_mono = np.mean(self.y, axis=0)

        self.duration = self.librosa.get_duration(y=self.y_mono, sr=self.sr)

    @staticmethod
    def _clamp(value: float) -> float:
        if value is None or np.isnan(value) or np.isinf(value):
            return None
        return float(max(0.0, min(1.0, value)))

    @staticmethod
    def _safe_mean(values, default=None):
        arr = np.asarray(values)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return default
        return float(np.mean(arr))

    @staticmethod
    def _safe_std(values, default=None):
        arr = np.asarray(values)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return default
        return float(np.std(arr))

    def extract_all(self) -> Dict[str, Optional[float]]:
        librosa = self.librosa
        y = self.y_mono
        sr = self.sr

        if len(y) < sr:
            raise ValueError("Audio too short for stable extraction.")

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        try:
            tempo_result = librosa.feature.rhythm.tempo(
                onset_envelope=onset_env,
                sr=sr,
                aggregate=None
            )
        except AttributeError:
            tempo_result = librosa.beat.tempo(
                onset_envelope=onset_env,
                sr=sr,
                aggregate=None
            )
        except AttributeError:
            tempo_result = librosa.beat.tempo(
                onset_envelope=onset_env,
                sr=sr,
                aggregate=None
            )
        tempo = self._safe_mean(tempo_result, default=0.0)

        rms = librosa.feature.rms(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        onset_events = librosa.onset.onset_detect(y=y, sr=sr, units="time")

        rms_mean = self._safe_mean(rms, 0.0)
        rms_std = self._safe_std(rms, 0.0)
        zcr_mean = self._safe_mean(zcr, 0.0)
        centroid_mean = self._safe_mean(centroid, 0.0)
        bandwidth_mean = self._safe_mean(bandwidth, 0.0)
        contrast_mean = self._safe_mean(contrast, 0.0)

        onset_count = len(onset_events)
        onset_rate = onset_count / max(1.0, self.duration)

        # F_s — fricción sistémica: rugosidad física aproximada por zcr + brillo + contraste
        fs = (
            min(1.0, zcr_mean / 0.20) * 0.35
            + min(1.0, centroid_mean / 6000.0) * 0.35
            + min(1.0, contrast_mean / 40.0) * 0.30
        )

        # G_f — gradiente de fricción: variación temporal de energía/onsets
        rms_delta = np.mean(np.abs(np.diff(rms))) if len(rms) > 1 else 0.0
        gf = min(1.0, rms_delta * 40.0 + np.std(onset_env) / 10.0)

        # C_s — coherencia sistémica: estabilidad energética y cromática
        chroma_stability = 1.0 - min(1.0, self._safe_std(chroma, 0.0))
        rms_stability = 1.0 - min(1.0, rms_std / max(1e-6, rms_mean + rms_std))
        cs = max(0.0, min(1.0, 0.55 * chroma_stability + 0.45 * rms_stability))

        # D_cog — desfase cognitivo: irregularidad de intervalos entre onsets
        if len(onset_events) >= 3:
            intervals = np.diff(onset_events)
            dcog = min(1.0, np.std(intervals) / max(1e-6, np.mean(intervals)))
        else:
            dcog = 0.0

        # E_r — energía relacional: tempo + energía + onsets
        er = (
            min(1.0, tempo / 180.0) * 0.40
            + min(1.0, rms_mean * 8.0) * 0.30
            + min(1.0, onset_rate / 8.0) * 0.30
        )

        # D_i — densidad de interacción: eventos por segundo + ancho espectral
        di = min(1.0, onset_rate / 10.0) * 0.65 + min(1.0, bandwidth_mean / 8000.0) * 0.35

        # Phi — campo cognitivo: espacialidad. Si es mono, limitada.
        if self.channels >= 2 and getattr(self.y, "ndim", 1) > 1:
            left = self.y[0]
            right = self.y[1]
            min_len = min(len(left), len(right))
            if min_len > 0:
                corr = np.corrcoef(left[:min_len], right[:min_len])[0, 1]
                if np.isnan(corr):
                    phi = 0.5
                else:
                    phi = 1.0 - abs(corr)
            else:
                phi = 0.5
        else:
            phi = 0.15

        # I_mc — interacción multicanal: canalidad + complejidad espectral
        imc = min(1.0, self.channels / 2.0) * 0.40 + min(1.0, contrast_mean / 35.0) * 0.60

        # V_i — vector intencional: dominancia de señal/centro aproximada por claridad cromática
        chroma_energy = np.mean(chroma, axis=1)
        if np.sum(chroma_energy) > 0:
            vi = float(np.max(chroma_energy) / np.sum(chroma_energy))
            vi = min(1.0, vi * 4.0)
        else:
            vi = None

        # Semántica queda fuera si no hay letra/transcripción.
        r_sem = None
        c_sem = None

        return {
            "F_s": round(self._clamp(fs), 6),
            "G_f": round(self._clamp(gf), 6),
            "C_s": round(self._clamp(cs), 6),
            "R_sem": r_sem,
            "C_sem": c_sem,
            "Phi": round(self._clamp(phi), 6),
            "I_mc": round(self._clamp(imc), 6),
            "E_r": round(self._clamp(er), 6),
            "V_i": round(self._clamp(vi), 6) if vi is not None else None,
            "D_i": round(self._clamp(di), 6),
            "D_cog": round(self._clamp(dcog), 6),
        }

    @classmethod
    def is_valid_emission(cls, mihm_raw: dict) -> bool:
        return all(mihm_raw.get(k) is not None for k in cls.CORE)

    @classmethod
    def compute_ihg(cls, mihm_raw: dict, nti: float = 0.5) -> dict:
        weighted_sum = 0.0

        for key, weight in cls.WEIGHTS.items():
            value = mihm_raw.get(key)
            if value is not None:
                weighted_sum += weight * value

        def penalty(a, b, weight=0.10):
            av = mihm_raw.get(a)
            bv = mihm_raw.get(b)
            if av is None or bv is None:
                return 0.0
            if av > 0.60 and bv < 0.40:
                return weight * av * (1 - bv)
            return 0.0

        penalties = [
            penalty("F_s", "C_s"),
            penalty("D_i", "E_r"),
            penalty("D_cog", "R_sem"),
            penalty("G_f", "V_i"),
        ]

        penalty_sum = min(0.5, sum(penalties))
        ihg_raw = weighted_sum - penalty_sum
        ihg_final = ihg_raw * (1 - nti) if nti < 0.4 else ihg_raw

        return {
            "weighted_sum": round(weighted_sum, 6),
            "penalty_sum": round(penalty_sum, 6),
            "ihg_raw": round(ihg_raw, 6),
            "ihg_final": round(ihg_final, 6),
        }
