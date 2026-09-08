import os
import sys

os.chdir("ai_engine")
sys.path.append(".")

from ai_pipeline import resolve_video_source

presets_to_test = ["1", "person", "2", "dog", "3", "fence", "0", "webcam"]

for p in presets_to_test:
    resolved = resolve_video_source(p)
    print(f"Preset '{p}' -> {resolved}")
    if isinstance(resolved, str):
        assert os.path.exists(resolved), f"Resolved file does not exist: {resolved}"

print("\n[ALL PRESETS RESOLVED AND VALIDATED]")
