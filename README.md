# AI Instagram Reel Bot — free, PC-off (GitHub Actions)

Full pipeline, no credit card, no PC needed after setup:
`Gemini script (free) -> edge-tts voice (free, no key) -> 3-4 real Pexels clips/photos (free) -> pro ffmpeg edit -> Cloudinary (free) -> Instagram Graph API Reel`

Pro look included: topic-matched visuals (the AI writes one stock search per story beat —
problem / product in use / happy result — and each clip follows the script), fast cuts every ~2.3s, color grade + vignette, Ken Burns on photos,
hook title card (first 3s), brand pill, uppercase captions, red progress bar, full-screen CTA end card + cover.

## 1. What you edit
`product.json` — product name, benefits, target, CTA, voice, hashtags, pexels_query.
Put optional background music at `assets/music.mp3` (must be royalty-free you own). Without it the reel is voice-only, which is fine.

## 2. Instagram setup (once, ~15 min, no card)
1. IG app: convert to **Business or Creator** (Settings → Account type).
2. Facebook: create a **Page**, then in Page Settings → Linked accounts → connect that IG.
3. https://developers.facebook.com → Create App → add **Instagram Graph API** product.
4. In App → API setup: add your FB Page, grant: `pages_show_list, instagram_basic, instagram_content_publish`.
5. Generate a **long-lived Page token** (60 days). Save it. You refresh it every ~55 days.
6. Get your IG business ID: call `GET graph.facebook.com/v21.0/me/accounts?access_token=TOKEN`, find page, then `GET /{page-id}?fields=instagram_business_account`.

## 3. Free keys (all no card)
- `GEMINI_API_KEY`: https://aistudio.google.com → Get API key (Google login). Optional — without it a built-in template script is used.
- `PEXELS_API_KEY`: https://www.pexels.com/api → email signup. Optional — without it a generated gradient background is used.
- Cloudinary: https://cloudinary.com → free signup → dashboard gives cloud_name / api_key / api_secret.

## 4. GitHub setup (once)
1. Create a **public** repo (public = unlimited Actions minutes free; private = 2000 min/month).
2. Upload everything in this folder, keeping paths (`scripts/`, `.github/workflows/post-reel.yml`, `product.json`, `requirements.txt`).
3. Repo → Settings → Secrets → Actions → add:
   `GEMINI_API_KEY, PEXELS_API_KEY, IG_USER_ID, FB_PAGE_TOKEN, CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET`
4. Edit schedule in `.github/workflows/post-reel.yml` if you want 2/day: `cron: "0 9,17 * * *"`.
5. Tab Actions → post-reel → **Run workflow** to test. Video is also saved as an artifact so you can watch it before it posts.

## 5. Rules that keep you unbanned
- Post only videos you own/have rights to. No reposted reels, no IG music library (API reels can't use it — your audio must be in the MP4).
- 1–3 reels/day max. 25 API posts/day hard limit.
- Token expires every 60 days — set a reminder.
- GitHub pauses cron after 60 days with zero commits — any commit restarts it. Cron can run 5–15 min late.
- Disclose ads/affiliate per your country's rules. No fake before/after or earnings claims.

## Files
- `product.json` — your product config
- `scripts/generate_script.py` — Gemini or template script → `data/script.json`
- `scripts/make_audio.py` — edge-tts voice
- `scripts/fetch_visual.py` — 3-4 portrait Pexels videos/photos or fallback
- `scripts/make_overlays.py` — Pillow hook/brand/CTA/cover cards
- `scripts/assemble.py` — pro ffmpeg cut: grade + captions + hook + progress bar + CTA
- `scripts/post_reel.py` — Cloudinary upload (video + cover) + IG container → poll → publish
