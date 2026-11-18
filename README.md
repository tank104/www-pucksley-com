# www.pucksley.com

The website for [Pucksley](https://github.com/tank104/Pucksley), the open-source voice assistant you can hold: a round
puck for the kitchen bench, and a hub at home that runs Claude with tools for the house.

**[www.pucksley.com](https://www.pucksley.com)** · [Pucksley on GitHub](https://github.com/tank104/Pucksley) ·
[Build your own](https://www.pucksley.com/get-started/) · [MIT licence](LICENSE)

An Astro + Tailwind static site: one scrolling home page that follows the film, a getting-started page, `/videos`, a
privacy page and a 404. No analytics, no cookies, no third-party scripts. It also holds the source of the film itself
(`film/`) and the logos (`design/`).

## Run it

Needs Node 22.12 or later.

```
npm install
npm run dev        # http://localhost:4336
npm run build      # static build to dist/
npm run preview    # serve the build
npm run check      # type-check the Astro and TypeScript files
```

The dev server is on port 4336 so it can run beside the sibling sites (4331 to 4335).

`npm run dev` and `npm run preview` do not run the early access Function (`api/waitlist`), so locally the form shows
its "that did not go through" message and the address to write to.

## What is where

| What | Where |
|---|---|
| The home page's words: hero, the day's intro, how it works, where it thinks, build your own, the email form, footer links | `src/content/pages/home.json` |
| The film's day, one moment per file, in order | `src/content/moments/` |
| What it runs: one plugin per file | `src/content/plugins/` |
| The questions | `src/content/faq/` |
| Site name, contact address, footer, copyright | `src/content/settings/site.json` |
| The getting-started instructions | `src/pages/get-started.astro` |
| The film: its files, length, chapters and every line it says | `src/lib/films.ts` |
| Nav items, GitHub links, the board's name | `src/lib/site.ts` |
| The look: colours, type, every section's style | `src/styles/global.css` (tokens at the top, repeated in `tailwind.config.mjs`) |
| The logo | `src/lib/logo.ts`, made by `design/logo.py` |

The JSON under `src/content/` is read at build time by `src/lib/content.ts`, in the same
`reader.singletons` / `reader.collections` shape as the sibling sites, so a git-based CMS can be added later without
changing the components.

**The getting-started page follows the project's README.** When the setup steps change in
[tank104/Pucksley](https://github.com/tank104/Pucksley#readme), change `src/pages/get-started.astro` with them, and
check every claim on the home page against the README too.

## The look

- **The light grounds are the film's card house on the kitchen bench**: card white and the bench's warm stone. **The
  dark is the puck**: its black glass, and the yellow its screen lights up in (`COL_YELLOW` in the firmware), the colour
  the house turns when the music starts. Yellow is for what is lit and for the one thing to press, never for text on a
  light ground.
- **The film's day is shown in the film's own light**, moment by moment, from first light to lights out
  (`[data-light]` in `global.css`).
- **One typeface, Nunito**, because it is the puck's own: every face on its screen and the film's closing card are set
  in it.
- **The puck's faces are its real ones**, drawn by the firmware's simulator (`film/screens/`). The ones that still show
  the orange spark are left out: it is close to Claude's own mark, and the film's script already asks for it to go.
- Films are click to play, never autoplay (`FilmPlayer.astro`).

## The logo

`design/logo.py` draws four marks (dial, eyes, house, p), each with the wordmark "Pucksley" in Nunito Black turned into
outlines, and writes them to `design/logos/` with a review sheet (`design/logos/sheet.html`). The site uses **eyes**:
the two bars of the puck's Home face, read as a face. To use another, change `CHOSEN` in `design/logo.py` and run:

```
python design/logo.py          # design/logos/*.svg, src/lib/logo.ts
python film/web.py icons --redo   # favicon.svg and apple-touch-icon.png from the chosen mark
```

## The film

`film/` is the source of "A day on the bench": the script and shot list (`film/SCRIPT.md`), the Blender and sound
scripts (`film/blender/`), the storyboards, and the puck's screens. Its rendered frames, downloaded sound and textures
and full-size renders (about six gigabytes) are not in git. See [`docs/videos.md`](docs/videos.md) for how the web
copies in `public/videos/` are made, and [`film/README.md`](film/README.md) for the film itself.

## Hosting

Azure Static Web Apps, set up with Bicep (`infra/`) and deployed by GitHub Actions (`.github/workflows/`), the same
shape as the sibling sites, with a `pk-*` naming convention, in the owner's Personal Azure subscription.

| | stg | prd |
|---|---|---|
| Resource group | `pk-www-stg` | `pk-www-prd` |
| Static Web App | `pk-stg-www-swa-ae` (eastasia) | `pk-prd-www-swa-ae` (eastasia) |
| Custom hostname | `stg-www.pucksley.com` | `www.pucksley.com` (the default: `pucksley.com` and the `azurestaticapps.net` address redirect to it) |
| Deploy trigger | push to `main` | by hand (Actions, Deploy prd, Run workflow), from `main` only |
| GitHub Environment | `stg` | `prd` |
| OIDC app registration | `pk-www-stg-github` | `pk-www-prd-github` |

Each environment's Bicep (`infra/main.bicep`) makes the Static Web App, App Insights, the storage table the email form
writes to (`api/waitlist`), and its own CNAME in the pucksley.com zone. prd also points the bare `pucksley.com` at its
Static Web App, with an Azure DNS alias record (an apex cannot be a CNAME).

The workflows then register each hostname on its Static Web App, once, without waiting: Azure validates it and issues
the certificate in the background. `www` and `stg-www` validate by their CNAME. The apex validates by a token, which
the prd workflow publishes as a TXT record at `@`. Last, the prd workflow makes `www` the Static Web App's default
domain, so every other hostname redirects there (301). Registering `www` again would undo that, which is why each
hostname is registered only once.

**The zone** is an Azure DNS zone in the Personal subscription's `global` resource group, made by `infra/zone.bicep`.
The domain is registered at OnlyDomains, with its nameservers set to the zone's
(`az network dns zone show -g global -n pucksley.com --query nameServers`). The zone file holds only what is not the
website's: pucksley.com has no email, so it publishes a null MX and a DMARC `p=reject`, and no one can send mail as
it. The website's records (`www`, `stg-www`, the apex A and TXT records) are written by the pipelines above.

**The identities.** `infra/bootstrap.ps1` makes everything the workflows stand on, and can be run again safely: the
zone, the two resource groups, an app registration per environment with a federated credential for that GitHub
Environment, and three roles each (Contributor on its own resource group, DNS Zone Contributor on the pucksley.com zone,
and "Pucksley www DNS Deployer", deployment operations only, on `global`, for the cross-group CNAME). It also sets the
repository's `AZURE_TENANT_ID` and `AZURE_SUBSCRIPTION_ID` variables and each environment's `AZURE_CLIENT_ID`, and
limits the `prd` environment to `main`.

Pull requests from this repository run the build and a what-if against stg. Pull requests from forks run the build
only: they get no Azure sign-in. `main` is protected: changes arrive by pull request, `test` must pass, and there are
no force-pushes or deletion. Only the maintainer can merge, and every pull request asks them for a review
([`.github/CODEOWNERS`](.github/CODEOWNERS)).

## Contributing

Issues and pull requests are welcome, here for the website and at
[tank104/Pucksley](https://github.com/tank104/Pucksley) for the puck, the hub and its plugins. For the site, run
`npm run check` and `npm run build` before you open a pull request, and keep the copy to what the project's README
says Pucksley does.

## Licence

The code in this repository is under the [MIT licence](LICENSE). That does not cover:

- **the Pucksley name and logos** (`design/logos/`, `src/lib/logo.ts`, the icons in `public/`), which identify the
  project: use them to refer to Pucksley, not as your own;
- **the film and every picture taken from it** (`public/videos/`, `public/images/film/`, `public/og-image.jpg`, the
  posters and `film/storyboards/`), which carry licensed music ("Simply Joyful" by William Claeson, Epidemic Sound) and
  computer voices (ElevenLabs, Azure), all rights reserved;
- **the Nunito typeface** (`film/fonts/`, and the `@fontsource-variable/nunito` package), under the SIL Open Font
  License (`film/fonts/OFL.txt`).
