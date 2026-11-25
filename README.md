# HappyNest Blanc Belle — 360° Virtual Tour

Live site: [https://tour.happynestfarm.in](https://tour.happynestfarm.in)

A [Pannellum](https://pannellum.org/) tour of HappyNest Blanc Belle, a luxury farm stay in Sohna, Haryana. It is also embedded on [happynestfarm.in](https://happynestfarm.in/#virtual-tour).

Hosted on Cloudflare Pages (project `farmtour`). The custom domain is a proxied CNAME: `tour.happynestfarm.in` → `farmtour.pages.dev`.

## What’s in this branch

The previous `main` branch stored 12K JPEG panoramas (about 534 MB of originals). This branch is the deployable site:

- 35 scenes as Pannellum **multires WebP cube tiles** (2048 px faces, 512 px tiles — equivalent to a 6K equirect)
- Low-resolution preview stills and fallback faces for a fast first view
- A room list, human-readable hotspot labels, title / Open Graph tags, a real favicon and `404.html`
- A service worker that is network-first for HTML/JSON, with a 40 MB cap on cached tiles
- Neighbor rooms are warmed with small fallback faces only — the tour no longer downloads every panorama on first load

## Local preview

```bash
python3 -m http.server 8080 --directory .
# open http://127.0.0.1:8080/
```

## Regenerating tiles

Masters (the original 11904×5952 JPEGs) are **not** in this branch. They still exist on `main` under `assets/`. To rebuild tiles:

```bash
git checkout main -- assets/*.jpg
python3 tools/generate_tiles.py \
  --src-dir assets \
  --out-dir assets/tiles \
  --jobs 3
python3 tools/build_tour_json.py
```

See `tools/generate_tiles.py`. It uses `ffmpeg` `v360` and Pillow.

## Proposed follow-up (not done here)

The 534 MB of camera masters should not live in Git history long-term. Good options:

- **Git LFS** for `assets/*.jpg` on a `masters` branch, or
- **Cloudflare R2** (or similar object storage) as the source of truth for masters, with only the generated tiles committed / uploaded to Pages

Do not force-push or rewrite `main`; it still holds the original files and may have been used as a Pages source. This branch drops the unused scenes `RoofThree`, `GroundFloorDrawingRoom`, and `DarkGreyRoomTwoWashroom`, and `.DS_Store`.

## Embed

The marketing site should load the iframe only after a click, with:

```
allow="accelerometer; gyroscope; fullscreen; xr-spatial-tracking"
```

so the phone gyro control works inside the embed. That change lives on the `feat/tour-iframe-click-to-load` branch of `HappyNest-website`.
