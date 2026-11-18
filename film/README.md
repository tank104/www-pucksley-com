# The Pucksley film

"A day on the bench": one shot, one day, 68 seconds. A white card model of a house stands on a kitchen bench among real
things (a pot, a cup, a plant), with the puck in front of it. Somebody talks to the puck from first light to lights out,
and the house answers in light. `SCRIPT.md` is the script, the shot list and what was decided.

It was made in the Pucksley repository (on the `tank104/Create-Video` branch, under `video/`) and moved here on
18 November 2026, so that the film lives with the site that shows it, as the sibling sites' films do.

## What is here

| Path | What |
|---|---|
| `SCRIPT.md` | The script and shot list, what was decided and what is still open |
| `blender/clock.py` | When everything happens. The picture, the voices, the music, the effects and the join all read it |
| `blender/film.py`, `puckkit.py`, `pieces.py` | The set, the puck and the house, built and lit in Blender |
| `blender/film_voice.py`, `eleven.py`, `azure_tts.py` | The two voices: ElevenLabs "Brian" asks, Azure "Annette" answers |
| `blender/film_music.py`, `epidemic.py`, `film_effects.py` | The music and the sound effects, from Epidemic Sound |
| `blender/face_capture.py`, `face_frames.py` | The talking face on the puck's screen, animated by Openspline to each of Annette's lines |
| `blender/film_join.py`, `finish.py` | The film finish (halation, curve, vignette, grain), the closing card, and the sound put on |
| `blender/film_all.sh`, `film_hd.sh` | The low-quality cut (960x540, 12 a second), and the full 1080p film |
| `blender/ideas.py`, `ideas.sh`, `mix.sh`, `*_sheet.py` | The five ideas and three mixes the film was chosen from |
| `storyboards/` | Those ideas and mixes, rendered, with their comparison sheets |
| `screens/` | The puck's faces, drawn by the firmware's simulator. `31` to `35` are the film's own (06:42, "Simply Joyful", the pasta timer, the banner) |
| `fonts/` | Nunito, the puck's typeface, for the closing card and the sheets (SIL Open Font License) |
| `web.py` | The site's copies: the web film, its captions, posters, stills, faces and icons (see `docs/videos.md`) |

## What is not here

Not in git, because of their size (about six gigabytes) or their licences:

- `blender/cache/`: every rendered frame, the voices already spoken, the downloaded music and sound effects, and the
  Poly Haven textures and models (CC0, fetched by `blender/fetch_assets.py`).
- `renders/`: the finished films. `pucksley-1080p-1.mp4` (1080p, 24 a second, 528 MB) is the one the site's copy is
  made from; `pucksley-low-cut-1.mp4` and `-2.mp4` are the low-quality cuts.
- `screens/30_talking_face.png`: a still of the talking face, which is a photograph of a real person from Openspline's
  set of faces.

## Making it again

Needs Blender 5.3, Python 3.12 with NumPy and Pillow, ffmpeg, and keys for ElevenLabs, Azure Speech and Epidemic
Sound in the file named by `FILM_KEYS` (or `D:/tmp/Keys.txt`): see the top of `eleven.py`, `azure_tts.py` and
`epidemic.py`. The keys are never in this repository.

```
bash film/blender/film_all.sh      # the low-quality cut: the picture, the music, the effects, the voices, joined
bash film/blender/film_hd.sh       # the 1080p film: about six hours of rendering, and it can be stopped and started
python film/web.py --redo          # then the site's copies
```

The film's own screens (`screens/31` to `35`) were drawn by a one-off `film` mode in the Pucksley repository's
simulator, made for the film and not kept; they are here as pictures only.
