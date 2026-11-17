#!/usr/bin/env bash
# Ideas 1 and 2 together, three ways (zoomin, zoomout, together in ideas.py), three frames each, finished
# and put in ../storyboards as mix-X-name-N.jpg, then the comparison sheet (mix_sheet.py).
#   bash film/blender/mix.sh                       # quick: half size, on the processor
#   SCALE=100 SAMPLES=64 bash film/blender/mix.sh  # full size
set -euo pipefail
cd "$(dirname "$0")"
SCALE=${SCALE:-50}; SAMPLES=${SAMPLES:-48}; DEVICE=${DEVICE:-cpu}
BLENDER="C:/Program Files/Blender Foundation/Blender 5.3/blender.exe"
declare -A LET=([zoomin]=a [zoomout]=b [together]=c) N=([wide]=1 [day]=2 [night]=3)
python pieces.py > /dev/null
for r in "${@:-zoomin zoomout together}"; do
  for r1 in $r; do
    for s in wide day night; do
      "$BLENDER" -b -P ideas.py -- --idea "$r1" --shot "$s" --scale "$SCALE" --samples "$SAMPLES" --device "$DEVICE" --out "cache/mix-$r1-$s.png" 2>&1 | grep -E "Traceback|rror:|line [0-9]+" || true
      python finish.py "cache/mix-$r1-$s.png" "../storyboards/mix-${LET[$r1]}-$r1-${N[$s]}.jpg" > /dev/null
      echo "$(date +%H:%M) mix ${LET[$r1]} $r1 ${N[$s]}"
    done
  done
done
python mix_sheet.py
