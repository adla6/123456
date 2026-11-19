
from datetime import datetime, timedelta, timezone
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image

URL = "https://www.weather.gov/wwamap/png/US.png"

SNAPSHOTS = Path("snapshots")
GIFS = Path("gifs")

SNAPSHOTS.mkdir(exist_ok=True)
GIFS.mkdir(exist_ok=True)

now = datetime.now(timezone.utc)
timestamp = now.strftime("%Y%m%d_%H%M%S")

# 1. Download weather map
response = requests.get(
    URL,
    headers={
        "User-Agent": "WeatherMapArchive/1.0 contact: admin@example.com",
        "Cache-Control": "no-cache"
    },
    timeout=30
)
response.raise_for_status()

# 2. Save timestamped PNG
image = Image.open(BytesIO(response.content)).convert("RGB")

filename = SNAPSHOTS / f"US_{timestamp}.png"
image.save(filename)

image.close()

print(f"Saved PNG: {filename}")

# 3. Find snapshots from the last 24 hours
cutoff = now - timedelta(hours=24)

recent = []

for file in sorted(SNAPSHOTS.glob("US_*.png")):
    try:
        file_time = datetime.strptime(
            file.stem.replace("US_", ""),
            "%Y%m%d_%H%M%S"
        ).replace(tzinfo=timezone.utc)

        if file_time >= cutoff:
            recent.append(file)

    except ValueError:
        continue

# 4. ALWAYS generate GIF, even with one frame
if not recent:
    recent = [filename]

frames = []

for file in recent:
    with Image.open(file) as img:
        frames.append(img.convert("RGB"))

gif_name = GIFS / f"US_Warnings_{now.strftime('%Y%m%d')}.gif"

frames[0].save(
    gif_name,
    format="GIF",
    save_all=True,
    append_images=frames[1:],
    duration=500,
    loop=0,
    optimize=True
)

for frame in frames:
    frame.close()

print(f"GIF generated: {gif_name}")
print(f"Total frames: {len(recent)}")

# 5. Remove snapshots older than 24 hours
for file in SNAPSHOTS.glob("US_*.png"):
    try:
        file_time = datetime.strptime(
            file.stem.replace("US_", ""),
            "%Y%m%d_%H%M%S"
        ).replace(tzinfo=timezone.utc)

        if file_time < cutoff:
            file.unlink()
            print(f"Deleted: {file}")

    except ValueError:
        continue
