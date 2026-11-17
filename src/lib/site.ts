// Structural nav. The marketing content is one scrolling page, so most of these are anchors on `/`;
// /get-started and /videos are the other pages worth a place here. Root-relative (`/#day`, not
// `#day`) so they also work from the other pages.
export const NAV_ITEMS = [
  { label: 'A day', href: '/#day' },
  { label: 'How it works', href: '/#how' },
  { label: 'What it runs', href: '/#runs' },
  { label: 'Get started', href: '/get-started/' },
  { label: 'Questions', href: '/#questions' },
  { label: 'The film', href: '/videos/' },
] as const;

// Where the code is. Pucksley itself (the puck's firmware, the hub, the plugins) and this website are
// two public repositories, both MIT-licensed.
const PROJECT = 'https://github.com/tank104/Pucksley';
const WEBSITE = 'https://github.com/tank104/www-pucksley-com';
export const GITHUB = {
  project: PROJECT,
  readme: `${PROJECT}#readme`,
  status: `${PROJECT}#status-what-has-and-hasnt-been-checked`,
  issues: `${PROJECT}/issues`,
  licence: `${PROJECT}/blob/main/LICENSE`,
  plugins: `${PROJECT}/blob/main/docs/PLUGINS.md`,
  protocol: `${PROJECT}/blob/main/docs/PROTOCOL.md`,
  architecture: `${PROJECT}/blob/main/docs/ARCHITECTURE.md`,
  compose: `${PROJECT}/blob/main/hub/docker-compose.yml`,
  website: WEBSITE,
  websiteIssues: `${WEBSITE}/issues`,
} as const;

/** The board a puck is built on. */
export const BOARD = 'Waveshare ESP32-S3-Touch-AMOLED-1.75C';

/**
 * The light of the day in the film, used as each moment's ground on the home page: the bench at first
 * light, in the morning sun, at midday, in the afternoon, at sunset, at night, and with the lights out.
 */
export const LIGHTS = ['dawn', 'morning', 'midday', 'afternoon', 'sunset', 'night', 'out'] as const;
export type Light = (typeof LIGHTS)[number];
