# The film on the site

`/videos` is the page for the Pucksley film, **A day on the bench** (1:08): one shot of one day, a card house on a
kitchen bench, and the puck running it from first light to lights out. The home page shows it in the hero, and its
"A day on the bench" section follows the film moment by moment. Each moment's still and time button plays the film from
that moment.

## Files

Four files live in `public/videos/`:

- `pucksley-a-day.mp4` is the film.
- `pucksley-a-day-poster.jpg` is 1920x1080, the still shown before play (52.6 s: the house at night, the heating on).
- `pucksley-a-day-og.jpg` is 1200x630, the picture a shared link shows. `public/og-image.jpg` is the same picture.
- `pucksley-a-day.vtt` is what is said, with the few sounds that matter, as captions.

And the pictures taken from the film and the puck:

- `public/images/film/<name>-1280.jpg` and `-640.jpg`: one still for each moment of the day.
- `public/images/faces/<name>.webp`: the puck's faces as round pictures, from the simulator's own pictures in
  `film/screens/`, and `puck.webp`, the puck itself cut from the film.

All of them are made from the finished 1080p render, `film/renders/pucksley-1080p-1.mp4`, by:

```
python film/web.py              # whatever is missing
python film/web.py --redo       # everything again
python film/web.py videos       # one step only: videos, captions, posters, stills, faces, icons
```

The film's length, chapters and every line it says are set once in `src/lib/films.ts`. The page is
`src/pages/videos/index.astro`; the player is `src/components/FilmPlayer.astro`.

## The captions

The captions are not typed: `film/web.py captions` works out where each line really is in the mix, the same way
`film/blender/film_voice.py` places them, from the lines it has already spoken (`film/blender/cache/voice`). Nothing is
sent to a voice service. It prints each line's start and end. The few sounds a deaf viewer would otherwise miss
(birds, the jazz starting, the turn, the chime, the crickets, the end) are `SOUNDS` in `film/web.py`.

## Rules for film on this site

- Click to play, `preload="none"`. Never autoplay, never loop. Nothing is fetched until the film is started, and the
  privacy page says so.
- The film has captions and its words written out on the page ("Read what the film says").
- A button anywhere on a page can start or seek the film by pointing at the player's id:
  `<button data-film-target="film" data-film-seek="16">` jumps to 0:16 and plays;
  `<a href="#film" data-film-start="film">` plays from the start.
- Say how it was made, in one line under it (`madeOf` in `films.ts`): the house, the bench and the puck are
  computer-made, the faces on the puck are its real ones, the voices are computer voices.

## Replacing the film

Render it again (`film/blender/film_hd.sh`; see `film/README.md`), keep the name `film/renders/pucksley-1080p-1.mp4`
or change `FILMS` in `film/web.py`, then run `python film/web.py --redo` and update `seconds`, `uploaded`, `chapters`
and `transcript` in `src/lib/films.ts`, and the moments' `at` in `src/content/moments/`. The beats' times are in
`film/blender/clock.py`. If a moment's picture changed, check its time in `STILLS` in `film/web.py`.

## Encode

H.264, 1920x1080, 24 pictures a second, two-pass at 4.6 Mbit/s, AAC stereo at 160 kbit/s, with faststart: 39.8 MB.
Keep it under 50 MB, because it is committed to git. The full-size render (528 MB) is not.

## Music, voices and downloads

The music is "Simply Joyful" by William Claeson, from Epidemic Sound, licensed through the owner's subscription, as are
the sound effects. The person's voice is ElevenLabs' stock voice "Brian"; the puck's is Azure's `en-AU-AnnetteNeural`,
the voice the real puck speaks with. None of this is under the repository's MIT licence (see the README).

The page offers no download button, as on the sibling sites. Before adding one, check that the music licence allows
giving the file to other people to republish.
