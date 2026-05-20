class MIHMLyricsExtractor:
    def __init__(self, text=None, audio_path=None):
        self.text = text
        self.audio_path = audio_path

    def extract(self):
        if not self.text:
            return {
                "R_sem": None,
                "C_sem": None,
                "warning": "NO_TEXT_AVAILABLE - R_sem and C_sem not evaluated. No simulation performed."
            }

        words = [w.strip().lower() for w in self.text.split() if w.strip()]
        if not words:
            return {
                "R_sem": None,
                "C_sem": None,
                "warning": "EMPTY_TEXT - semantic variables not evaluated."
            }

        unique_ratio = len(set(words)) / max(1, len(words))
        length_norm = min(1.0, len(words) / 500.0)

        c_sem = round(max(0.0, min(1.0, 1.0 - unique_ratio * 0.5)), 6)
        r_sem = round(max(0.0, min(c_sem, length_norm)), 6)

        return {
            "R_sem": r_sem,
            "C_sem": c_sem,
            "warning": None
        }