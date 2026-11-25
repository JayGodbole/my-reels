"""Upload reel to Cloudinary (free, no card) then publish as IG Reel via Graph API."""
import hashlib, json, os, sys, time
import requests

API = "https://graph.facebook.com/v21.0"

def cloudinary_upload(path, cloud, key, secret):
    ts = int(time.time())
    sig = hashlib.sha1(f"timestamp={ts}{secret}".encode()).hexdigest()
    with open(path, "rb") as f:
        r = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud}/video/upload",
            data={"api_key": key, "timestamp": ts, "signature": sig},
            files={"file": f},
            timeout=300,
        )
    r.raise_for_status()
    return r.json()["secure_url"]

def ig_create_container(ig_id, token, video_url, caption, cover_url=None):
    data = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": token,
    }
    if cover_url:
        data["cover_url"] = cover_url
    r = requests.post(f"{API}/{ig_id}/media", data=data, timeout=60)
    r.raise_for_status()
    return r.json()["id"]

def ig_poll(container, token, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(f"{API}/{container}",
                         params={"fields": "status_code", "access_token": token}, timeout=30)
        r.raise_for_status()
        s = r.json().get("status_code")
        print(f"container status: {s}")
        if s == "FINISHED":
            return
        if s == "ERROR":
            raise RuntimeError("IG container failed - check video format/URL")
        time.sleep(15)
    raise RuntimeError("IG container timed out")

def ig_publish(ig_id, token, container):
    r = requests.post(f"{API}/{ig_id}/media_publish",
                      data={"creation_id": container, "access_token": token}, timeout=60)
    r.raise_for_status()
    return r.json()["id"]

def main():
    for v in ["IG_USER_ID", "FB_PAGE_TOKEN", "CLOUDINARY_CLOUD_NAME",
              "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"]:
        if not os.environ.get(v):
            sys.exit(f"missing secret: {v}")
    with open("data/script.json") as f:
        caption = json.load(f)["caption"]
    url = cloudinary_upload("out/reel.mp4",
        os.environ["CLOUDINARY_CLOUD_NAME"], os.environ["CLOUDINARY_API_KEY"],
        os.environ["CLOUDINARY_API_SECRET"])
    print(f"video url: {url}")
    cover_url = None
    if os.path.exists("assets/cover.jpg"):
        try:
            with open("assets/cover.jpg", "rb") as f:
                import hashlib as _h, time as _t
                ts = int(_t.time())
                sig = _h.sha1(f"timestamp={ts}{os.environ['CLOUDINARY_API_SECRET']}".encode()).hexdigest()
                r = requests.post(
                    f"https://api.cloudinary.com/v1_1/{os.environ['CLOUDINARY_CLOUD_NAME']}/image/upload",
                    data={"api_key": os.environ["CLOUDINARY_API_KEY"], "timestamp": ts, "signature": sig},
                    files={"file": f}, timeout=120)
                r.raise_for_status()
                cover_url = r.json()["secure_url"]
                print(f"cover url: {cover_url}")
        except Exception as e:
            print(f"cover upload skipped: {e}")
    ig_id, token = os.environ["IG_USER_ID"], os.environ["FB_PAGE_TOKEN"]
    c = ig_create_container(ig_id, token, url, caption, cover_url)
    print(f"container: {c}")
    ig_poll(c, token)
    mid = ig_publish(ig_id, token, c)
    print(f"PUBLISHED media id: {mid}")

if __name__ == "__main__":
    main()
