#!/usr/bin/env bash
# Render the five ideas (ideas.py), three frames each, give them the film finish and put them in
# ../storyboards as idea-N-name-shot.jpg, then build the comparison sheet (ideas_sheet.py).
#   bash film/blender/ideas.sh                          # full size, on the processor
#   SCALE=50 SAMPLES=48 bash film/blender/ideas.sh house rings      # quick, just these
#   DEVICE=gpu bash film/blender/ideas.sh               # on the graphics card: about ten times quicker
set -euo pipefail
cd "$(dirname "$0")"
SCALE=${SCALE:-100}; SAMPLES=${SAMPLES:-128}; DEVICE=${DEVICE:-cpu}
BLENDER="C:/Program Files/Blender Foundation/Blender 5.3/blender.exe"
declare -A NUM=([house]=1 [bench]=2 [remotes]=3 [apart]=4 [rings]=5)
python fetch_assets.py > /dev/null
python pieces.py > /dev/null
for r in "${@:-house bench remotes apart rings}"; do
  for r1 in $r; do
    for s in wide day night; do
      n=$SAMPLES; [ "$s" = night ] && n=$((SAMPLES * 14 / 10))
      "$BLENDER" -b -P ideas.py -- --idea "$r1" --shot "$s" --scale "$SCALE" --samples "$n" --device "$DEVICE" --out "cache/idea-$r1-$s.png" 2>&1 | grep -E "Traceback|rror:|line [0-9]+" || true
      python finish.py "cache/idea-$r1-$s.png" "../storyboards/idea-${NUM[$r1]}-$r1-$s.jpg" > /dev/null
      echo "$(date +%H:%M) idea ${NUM[$r1]} $r1 $s"
    done
  done
done
python ideas_sheet.py
