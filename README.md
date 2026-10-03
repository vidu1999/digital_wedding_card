# Digital Wedding Invitation

A responsive, single-page Sri Lankan wedding invitation for Anjali & Kavindu. The visual theme pairs a warm ivory-and-forest palette with gold details, a Kandyan poruwa photograph, and subtle lotus-inspired ornament.

## Run locally

No build step or dependencies are required. From this directory, run:

```sh
python3 -m http.server 4173 --bind 0.0.0.0
```

Then open `http://localhost:4173` in your browser. In Arena's preview, the app can be served on the same port with the live-preview tool.

## Free hosting with GitHub Pages

This public repository is configured to publish the invitation with GitHub Pages. The workflow in `.github/workflows/deploy-pages.yml` deploys the static site whenever the invitation files are pushed to `main` or the Arena working branch. After the first successful workflow run, the site is available at:

**https://vidu1999.github.io/digital_wedding_card/**

You can watch deployment progress under the repository's **Actions** tab. No paid hosting or build service is required.

## Included interactions

- Live countdown to the ceremony in Sri Lanka Standard Time.
- RSVP dialog with attendance, party size, and dietary notes. This front-end demo stores the latest response in the browser's local storage; connect a form service or backend before using it for real guest responses.
- Downloadable `.ics` calendar event and share/copy invitation link.
- Responsive navigation, venue directions, and reduced-motion/accessibility support.

## Update the sample invitation

Edit the names, date, schedule, venue, and RSVP deadline in `index.html`. Update the matching event date, calendar details, and RSVP copy in `script.js`. Replace `assets/poruwa-hero.png` if you have a couple or venue photo you'd like to use instead.
