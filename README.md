# Digital Wedding Invitation

A responsive, single-page Sri Lankan wedding invitation for Anjali & Kavindu. The visual theme pairs a warm ivory-and-forest palette with gold details, a Kandyan poruwa photograph, and subtle lotus-inspired ornament.

## Run locally

No build step or dependencies are required. From this directory, run:

```sh
python3 -m http.server 4173 --bind 0.0.0.0
```

Then open `http://localhost:4173` in your browser. In Arena's preview, the app can be served on the same port with the live-preview tool.

## Free hosting with GitHub Pages

The workflow in `.github/workflows/deploy-pages.yml` is ready to publish the static site whenever invitation files are pushed to `main` or the Arena working branch. Pages still needs a one-time source selection in repository settings:

1. Open [Settings → Pages](https://github.com/vidu1999/digital_wedding_card/settings/pages).
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. In **Actions**, re-run the failed “Deploy wedding invitation to GitHub Pages” run (or use **Run workflow**).

After that first successful deployment, the free public site is available at **https://vidu1999.github.io/digital_wedding_card/**. Future pushes deploy automatically.

## Marketing reel

- [Download the vertical MP4 promo](assets/wedding-invitation-promo.mp4) — 1080 × 1920, 21 seconds, with an original ambient score.
- [View the reel poster](assets/wedding-invitation-promo-poster.jpg).
- Once Pages is enabled, the video is also hosted at `https://vidu1999.github.io/digital_wedding_card/assets/wedding-invitation-promo.mp4`.

To rebuild the reel after changing its scenes, install `scripts/requirements-media.txt` and run `python scripts/build_promo_video.py`.

## Included interactions

- Live countdown to the ceremony in Sri Lanka Standard Time.
- RSVP dialog with attendance, party size, and dietary notes. This front-end demo stores the latest response in the browser's local storage; connect a form service or backend before using it for real guest responses.
- Downloadable `.ics` calendar event and share/copy invitation link.
- Responsive navigation, venue directions, and reduced-motion/accessibility support.

## Update the sample invitation

Edit the names, date, schedule, venue, and RSVP deadline in `index.html`. Update the matching event date, calendar details, and RSVP copy in `script.js`. Replace `assets/poruwa-hero.png` if you have a couple or venue photo you'd like to use instead.
