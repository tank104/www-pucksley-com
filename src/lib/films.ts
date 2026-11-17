// The film on the site: where its files are, and the facts the pages and the structured data need.
// Structural, like NAV_ITEMS in site.ts, so it lives in code and not in the content JSON.
//
// The files in public/videos/ are made from the finished 1080p render by film/web.py
// (see docs/videos.md). The times are film/blender/clock.py's; the lines are film/blender/film_voice.py's.

export type Chapter = { t: number; label: string };
export type Line = { who: 'You' | 'Pucksley'; line: string };

export type Film = {
  slug: string;
  title: string;
  blurb: string;
  description: string;
  mp4: string;
  poster: string;
  og: string;
  captions: string;
  /** Running time in seconds, closing card included. */
  seconds: number;
  /** ISO date the file was made, for the VideoObject data. */
  uploaded: string;
  /** Where each part starts, in seconds: the moment the puck is tapped. */
  chapters: Chapter[];
  /** Every line spoken, for people who cannot play it. */
  transcript: Line[];
  /** One line on how it was made, shown under the film on /videos. */
  madeOf: string;
};

/** "A day on the bench": one shot, one day, the card house on the kitchen bench (film/SCRIPT.md). */
export const A_DAY: Film = {
  slug: 'a-day',
  title: 'A day on the bench',
  blurb: 'One puck, the whole house, from first light to lights out.',
  description:
    'One shot and one day: a card model of a house on a real kitchen bench, with the puck in front of it. Somebody talks to Pucksley from first light to lights out, and the house answers in light: music in the kitchen, a pasta timer, the TV off, a lamp on, the heating up, the PC shut down, and good night.',
  mp4: '/videos/pucksley-a-day.mp4',
  poster: '/videos/pucksley-a-day-poster.jpg',
  og: '/videos/pucksley-a-day-og.jpg',
  captions: '/videos/pucksley-a-day.vtt',
  seconds: 68,
  uploaded: '2026-11-18',
  chapters: [
    { t: 0, label: 'First light' },
    { t: 9.8, label: 'Jazz in the kitchen' },
    { t: 19.8, label: 'Two rooms' },
    { t: 25.8, label: 'Pasta' },
    { t: 35.8, label: 'TV off, lamp on' },
    { t: 44.8, label: 'Heating' },
    { t: 50.8, label: 'The PC' },
    { t: 57.8, label: 'Good night' },
  ],
  transcript: [
    { who: 'You', line: "What's the weather doing this afternoon?" },
    { who: 'Pucksley', line: 'Clearing by two. Take a jacket till then.' },
    { who: 'You', line: 'Play some jazz in the kitchen.' },
    { who: 'Pucksley', line: 'Jazz, in the kitchen.' },
    { who: 'You', line: 'Group the kitchen with the ensuite.' },
    { who: 'Pucksley', line: 'Done. Both rooms.' },
    { who: 'You', line: 'Set a timer for pasta. Ten minutes.' },
    { who: 'Pucksley', line: 'Ten minutes. Starting now.' },
    { who: 'Pucksley', line: "Your pasta's ready." },
    { who: 'You', line: 'Turn off the downstairs TV.' },
    { who: 'Pucksley', line: "It's off." },
    { who: 'You', line: 'Lamp on.' },
    { who: 'You', line: 'Turn the heating up half a degree.' },
    { who: 'Pucksley', line: 'Twenty-one and a half.' },
    { who: 'You', line: 'Shut down the PC.' },
    { who: 'Pucksley', line: 'Shut down the PC? Turn for yes.' },
    { who: 'You', line: 'Everything off. Good night.' },
    { who: 'Pucksley', line: 'Good night.' },
  ],
  madeOf:
    'The house, the bench and the puck were built and lit in a computer, and filmed as one shot. The faces on the puck’s screen are its real ones, drawn by its own firmware. Both voices are computer voices: the person is ElevenLabs’ “Brian”, and the puck is Azure’s “Annette”, the voice the real puck speaks with. The music is “Simply Joyful” by William Claeson.',
};

export const FILMS = [A_DAY];

/** 68 → "1:08". Chapter times read down, so 9.8 → "0:09". */
export const runningTime = (seconds: number) => {
  const s = Math.round(seconds);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
};
export const chapterTime = (seconds: number) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;

/** "1 minute 8 seconds": the running time as it is said. */
export const spokenTime = (seconds: number) => {
  const s = Math.round(seconds);
  const m = Math.floor(s / 60);
  const rest = `${s % 60} seconds`;
  return m ? `${m} minute${m > 1 ? 's' : ''} ${rest}` : rest;
};

export const videoObject = (film: Film, site: URL) => ({
  '@context': 'https://schema.org',
  '@type': 'VideoObject',
  name: film.title,
  description: film.description,
  thumbnailUrl: [new URL(film.poster, site).href],
  uploadDate: film.uploaded,
  duration: `PT${Math.round(film.seconds)}S`,
  contentUrl: new URL(film.mp4, site).href,
});
