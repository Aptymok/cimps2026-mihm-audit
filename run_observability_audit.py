import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from core.world_spectrum import get_world_spectrum
from core.montecarlo import run_montecarlo


def run_audio_extract(audio_path: str | None, nti: float):
    if not audio_path:
        return {
            "status": "NOT_EXECUTED",
            "reason": "No audio file provided. Observabilidad auditiva no ejecutada sobre WAV."
        }

    path = Path(audio_path)
    if not path.exists():
        return {
            "status": "NOT_EXECUTED",
            "reason": f"Audio file not found: {audio_path}"
        }

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "core.mihm_extract_full",
            audio_path,
            "--no-text",
            "--nti",
            str(nti),
        ],
        capture_output=True,
        text=True,
    )

    try:
        payload = json.loads(proc.stdout)
    except Exception:
        payload = {
            "status": "ERROR",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }

    return payload


async def main():
    parser = argparse.ArgumentParser(description="Run MIHM observability audit.")
    parser.add_argument("--audio", default=None, help="Optional WAV file for MIHM audio extraction.")
    parser.add_argument("--output", default="outputs/observability_report.json")
    parser.add_argument("--nti", type=float, default=0.5)
    args = parser.parse_args()

    world = await get_world_spectrum()

    montecarlo_df, n_iter = run_montecarlo(50000)
    montecarlo_summary = {
        "iterations": n_iter,
        "best_windows": montecarlo_df.nlargest(5, "mean").round(6).to_dict(orient="records"),
        "worst_windows": montecarlo_df.nsmallest(3, "mean").round(6).to_dict(orient="records"),
    }

    audio = run_audio_extract(args.audio, args.nti)

    report = {
        "status": "OBSERVABILITY_AUDIT_COMPLETE",
        "world_spectrum": world,
        "montecarlo": montecarlo_summary,
        "audio_extraction": audio,
        "validity_boundary": (
            "This audit verifies executable observability components. "
            "It does not certify scientific truth or aesthetic value."
        )
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps({
        "status": report["status"],
        "output": str(output_path),
        "audio_status": audio.get("status"),
        "world_wsi": world.get("wsi"),
        "world_nti": world.get("nti"),
        "montecarlo_iterations": n_iter,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())