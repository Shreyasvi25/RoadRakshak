from typing import Dict


def process_frame(frame: bytes) -> Dict:
    """Stub implementation for the Person 1 computer vision pipeline.

    Replace this with the real process_frame() once the vision model is ready.
    """
    return {
        "vehicles": 3,
        "violations": [],
        "accident": False,
        "severity": "low",
        "annotated_frame": frame,
        "snapshot_path": None,
    }
