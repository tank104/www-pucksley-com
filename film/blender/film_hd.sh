#!/usr/bin/env bash
# The Pucksley film at full quality: 1080p, 24 frames a second, 96 samples (192 looked no different),
# with the sound of the low-quality cut. About 1,540 frames at roughly 14 seconds each on this PC's
# graphics card: about six hours, one Blender at a time (the user's rule, 2026-11-17).
#
#   bash film/blender/film_hd.sh           # render what is missing, finish, join, put the sound on
#   DRY=1 bash film/blender/film_hd.sh     # only say how many frames are there
#
# It can be stopped and started again: every frame is its own file in cache/film-hd, and only missing ones
# are rendered. If Blender stops by itself it is started again, up to six times. The PC is kept awake while frames are written.
# Before it: face_capture.py and face_frames.py --fps 24 (the talking face), and the sound (film_all.sh).
set -uo pipefail
cd "$(dirname "$0")"
SAMPLES=${SAMPLES:-96}; OUT=${OUT:-../renders/pucksley-1080p-1.mp4}
BLENDER="C:/Program Files/Blender Foundation/Blender 5.3/blender.exe"
WANT=$(python -c "import clock; print(int(round(clock.END * 24)) + 1)")
count() { ls cache/film-hd 2>/dev/null | grep -c '\.png$' || true; }
if [ -n "${DRY:-}" ]; then echo "film-hd: $(count) of $WANT frames"; exit 0; fi
mkdir -p cache/film-hd
python keep_awake.py "cache/film-hd" > /dev/null 2>&1 &
[ -d cache/face-seq-24 ] || python face_frames.py --fps 24
side() {      # one Blender, started again if it stops before every frame is there
  for try in 1 2 3 4 5 6; do
    [ "$(count)" -ge "$WANT" ] && return 0
    echo "$(date +%H:%M) $(count) of $WANT frames there; Blender ${1:-forwards}, run $try" >> cache/film-hd-run.log
    "$BLENDER" -b -P film.py -- --fps 24 --scale 100 --samples "$SAMPLES" --device gpu --folder film-hd --resume ${1:-} >> cache/film-hd.log 2>&1 || true
  done
}
side
echo "$(date +%H:%M) $(count) of $WANT frames" >> cache/film-hd-run.log
[ "$(count)" -ge "$WANT" ] || { echo "only $(count) of $WANT frames: see cache/film-hd.log"; exit 1; }
python film_music.py && python film_effects.py && python film_voice.py > /dev/null
python film_join.py --src film-hd --fps 24 --crf 15 --out "$OUT"
