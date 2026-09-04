import os
import time

THUMBNAIL_DIR = "static/thumbnails"

def cleanup_old_thumbnails(max_age_seconds: int = 86400):
    """Deletes cached JPEG thumbnails older than 24 hours to prevent disk bloat."""
    if not os.path.exists(THUMBNAIL_DIR):
        return
    
    now = time.time()
    count = 0
    for filename in os.listdir(THUMBNAIL_DIR):
        filepath = os.path.join(THUMBNAIL_DIR, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    count += 1
                except Exception as e:
                    print(f"[Cleanup Error] Could not remove {filename}: {e}")
    if count > 0:
        print(f"[Housekeeping] Cleaned up {count} expired thumbnail(s).")