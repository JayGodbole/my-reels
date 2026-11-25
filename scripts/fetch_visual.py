"""Download topic-matched vertical visuals: one Pexels search per script beat."""
import json, os
import requests

os.makedirs("assets", exist_ok=True)
manifest = "assets/media.json"
if os.path.exists(manifest) and os.path.getsize(manifest) > 10:
    print("media exists, skip")
    raise SystemExit(0)

key = os.environ.get("PEXELS_API_KEY", "").strip()
with open("product.json") as f:
    fallback = json.load(f).get("pexels_query", "lifestyle")
try:
    with open("data/script.json") as f:
        queries = json.load(f).get("visuals") or [fallback]
    queries = [q for q in queries if isinstance(q, str) and q.strip()][:3] or [fallback]
except Exception:
    queries = [fallback]

items = []  # {"kind":"video"|"image", "path":..., "query":...}

def dl(url, path):
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"saved {path} ({len(r.content)//1024}KB)")

def pick_video(files):
    files = [x for x in files if x.get("link")]
    files.sort(key=lambda x: x.get("width", 0))
    return (next((x for x in files if x.get("width", 0) <= 720 and x.get("width", 0) < x.get("height", 9999)), None)
        or next((x for x in files if x.get("width", 0) < x.get("height", 9999)), None)
        or (files[0] if files else None))

if key:
    n = 0
    # beat 1..3 -> one clip each, in order, so cuts follow the story
    for qi, q in enumerate(queries):
        if n >= 3:
            break
        try:
            r = requests.get("https://api.pexels.com/videos/search",
                params={"query": q, "orientation": "portrait", "size": "medium", "per_page": 4},
                headers={"Authorization": key}, timeout=30)
            r.raise_for_status()
            for v in r.json().get("videos", []):
                pick = pick_video(v.get("video_files", []))
                if not pick:
                    continue
                try:
                    dl(pick["link"], f"assets/clip{n}.mp4")
                    items.append({"kind": "video", "path": f"assets/clip{n}.mp4", "query": q})
                    n += 1
                    break  # one clip per beat
                except Exception as e:
                    print(f"clip skip ({q}): {e}")
        except Exception as e:
            print(f"pexels video failed ({q}): {e}")
    # fill up to 4 with portrait photos, same per-beat order
    try:
        if len(items) < 4:
            m = len(items)
            for q in queries:
                if m >= 4:
                    break
                r = requests.get("https://api.pexels.com/v1/search",
                    params={"query": q, "orientation": "portrait", "per_page": 3},
                    headers={"Authorization": key}, timeout=30)
                r.raise_for_status()
                for p in r.json().get("photos", []):
                    url = p.get("src", {}).get("large") or p.get("src", {}).get("medium")
                    if not url:
                        continue
                    try:
                        dl(url, f"assets/img{m}.jpg")
                        items.append({"kind": "image", "path": f"assets/img{m}.jpg", "query": q})
                        m += 1
                        break  # one photo per beat
                    except Exception as e:
                        print(f"img skip ({q}): {e}")
    except Exception as e:
        print(f"pexels photo failed: {e}")
else:
    print("no PEXELS_API_KEY — assemble will use styled generated backgrounds")

with open(manifest, "w") as f:
    json.dump(items, f, indent=2)
print(f"media items: {len(items)} {[i.get('query') for i in items]}")
