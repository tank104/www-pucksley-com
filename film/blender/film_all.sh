#!/usr/bin/env bash
# The whole low-quality cut of the Pucksley film: the picture (960x540, 12 frames a second), the music, the
# effects, the voices, joined into ../renders/pucksley-low-cut-N.mp4.
#   bash film/blender/film_all.sh                    # render what is missing, then the sound and the join
#   OUT=../renders/pucksley-low-cut-2.mp4 bash film/blender/film_all.sh
#   RANGE="--from 50 --to 58" bash film/blender/film_all.sh    # after a change to those seconds: delete
#                                                               # their frames from cache/film first
#   DEVICE=cpu bash film/blender/film_all.sh         # leave the graphics card alone (about ten times slower)
# A change to the sound alone needs no rendering: the frames are kept, and only missing ones are rendered.
set -euo pipefail
cd "$(dirname "$0")"
OUT=${OUT:-../renders/pucksley-low-cut-1.mp4}; DEVICE=${DEVICE:-gpu}
BLENDER="C:/Program Files/Blender Foundation/Blender 5.3/blender.exe"
python fetch_assets.py > /dev/null
python pieces.py > /dev/null
"$BLENDER" -b -P film.py -- --scale 50 --samples 32 --device "$DEVICE" --folder film --resume ${RANGE:-} 2>&1 | grep -E "Traceback|rror:|line [0-9]+" | grep -v HIPEW || true
python film_music.py
python film_effects.py
python film_voice.py
python film_join.py --out "$OUT"
