
import os
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

# Download latest weather map
response = requests.get(
    URL,
    headers={"User-Agent": "WeatherMapArchive/1.0", "Cache-Control": "no-cache"},
    timeout=30
)
response.raise_for_status()

# Save timestamped PNG
image = Image.open(BytesIO(response.content)).convert("RGB")
filename = SNAPSHOTS / f"US_{timestamp}.png"
image.save(filename)

print(f"Saved: {filename}")

# Generate daily GIF at midnight UTC
if now.hour == 0:
    cutoff = now 

    files = sorted(SNAPSHOTS.glob("US_*.png"))
    recent = []

    for file in files:
        file_time = datetime.strptime(
            file.stem.replace("US_", ""),
            "%Y%m%d_%H%M%S"
        ).replace(tzinfo=timezone.utc)

        if file_time >= cutoff:
            recent.append(file)

    if recent:
        frames = [Image.open(f).convert("RGB") for f in recent]

        gif_name = GIFS / f"US_Warnings_{now.strftime('%Y%m%d')}.gif"

        frames[0].save(
            gif_name,
            save_all=True,
            append_images=frames[1:],
            duration=500,
            loop=0,
            optimize=True
        )

        for frame in frames:
            frame.close()

        print(f"Created GIF: {gif_name}")
        print(f"Frames: {len(recent)}")

# Remove snapshots older than 24 hours
for file in SNAPSHOTS.glob("US_*.png"):
    file_time = datetime.strptime(
        file.stem.replace("US_", ""),
        "%Y%m%d_%H%M%S"
    ).replace(tzinfo=timezone.utc)

    if file_time < now - timedelta(hours=24):
        file.unlink()
        print(f"Deleted old snapshot: {file}")
