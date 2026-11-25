"""Pro reel builder: fast cuts of real stock + grade + hook/brand/CTA cards + pro captions. CPU-only."""
import glob, json, math, os, subprocess

W, H = 1080, 1920
SEG = 2.3          # cut every ~2.3s = retention editing
MAXD = 45          # keep reels snappy
FONT = "DejaVu Sans"

def run(cmd):
    print("+", " ".join(cmd)[:220])
    subprocess.run(cmd, check=True)

def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

def srt(text, total, path):
    words = [w.upper() for w in text.split()]
    chunks, i = [], 0
    while i < len(words):
        n = 3 if len(words) - i > 4 else len(words) - i
        chunks.append(" ".join(words[i:i + n]))
        i += n
    with open(path, "w") as f:
        for k, c in enumerate(chunks):
            s, e = total * k / len(chunks), total * (k + 1) / len(chunks)
            f.write(f"{k+1}\n{s//3600:02.0f}:{s%3600//60:02.0f}:{s%60:06.3f} --> "
                    f"{e//3600:02.0f}:{e%3600//60:02.0f}:{e%60:06.3f}\n{c}\n\n")

GRADE = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
         "eq=contrast=1.08:saturation=1.18:brightness=-0.02,"
         "vignette=PI/5,fps=30,setsar=1")

def seg_from_video(src, off, out):
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{off:.1f}", "-t", str(SEG),
         "-i", src, "-vf", GRADE, "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-an", out])

def seg_from_image(src, out, zoom_in=True):
    z = "1+0.10*on/70" if zoom_in else "1.10-0.10*on/70"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", src,
         "-vf", f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
                 f"zoompan=z='{z}':d=70:s=1080x1920:fps=30,{GRADE}",
         "-t", str(SEG), "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", out])

def seg_generated(idx, out):
    cols = ["0x141824", "0x1d1420", "0x101f1c", "0x201a12"]
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"color=c={cols[idx % len(cols)]}:s={W}x{H}:d={SEG}:r=30",
         "-vf", f"zoompan=z='1+0.06*on/70':d=70:s={W}x{H},eq=contrast=1.05:saturation=1.1",
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])

def main():
    os.makedirs("out", exist_ok=True)
    os.makedirs("assets/segs", exist_ok=True)
    with open("data/script.json") as f:
        d = json.load(f)
    text = d["script_text"]
    voice = "assets/voice.mp4" if os.path.exists("assets/voice.mp4") else "assets/voice.mp3"
    total = min(dur(voice), MAXD)
    srt(text, total, "assets/caps.srt")

    import json as J
    media = []
    if os.path.exists("assets/media.json"):
        try:
            media = J.load(open("assets/media.json"))
        except Exception:
            media = []
    media = [m for m in media if os.path.exists(m.get("path", ""))]
    if not media:
        vids = sorted(glob.glob("assets/clip*.mp4") + glob.glob("assets/bg.mp4"))
        imgs = sorted(glob.glob("assets/img*.jpg"))
        media = [{"kind": "video", "path": p} for p in vids] + [{"kind": "image", "path": p} for p in imgs]

    nseg = max(3, math.ceil(total / SEG))
    segs = []
    for i in range(nseg):
        out = f"assets/segs/s{i:02d}.mp4"
        if media:
            m = media[i % len(media)]
            try:
                if m["kind"] == "video":
                    try:
                        sd = dur(m["path"])
                    except Exception:
                        sd = SEG + 1
                    off = (i * 1.7) % max(0.1, sd - SEG - 0.2) if sd > SEG + 0.3 else 0
                    seg_from_video(m["path"], off, out)
                else:
                    seg_from_image(m["path"], out, zoom_in=(i % 2 == 0))
            except Exception as e:
                print(f"seg {i} fallback: {e}")
                seg_generated(i, out)
        else:
            seg_generated(i, out)
        segs.append(out)

    with open("assets/segs/list.txt", "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", "assets/segs/list.txt", "-c", "copy", "assets/base.mp4"])

    D = f"{total:.2f}"
    fc = (f"[0:v]trim=0:{D},setpts=PTS-STARTPTS,"
          f"subtitles=assets/caps.srt:force_style='FontName={FONT},FontSize=20,"
          f"PrimaryColour=&HFFFFFF,OutlineColour=&H90000000,BorderStyle=1,Outline=3,"
          f"Shadow=1,Alignment=2,MarginV=380'[sub];"
          f"[sub][1:v]overlay=50:170:enable='lt(t,3)':eof_action=pass[h];"
          f"[h][2:v]overlay=40:40:eof_action=pass[b];"
          f"[b][3:v]overlay=0:0:enable='gte(t,{total-4:.2f})':eof_action=pass[v1];"
          f"[v1]drawbox=x=0:y=0:w='iw*t/{D}':h=10:c=red:t=fill[vout]")

    cmd = ["ffmpeg", "-y", "-v", "error", "-i", "assets/base.mp4", "-i", voice]
    mus = None
    if os.path.exists("assets/music.mp3"):
        cmd += ["-i", "assets/music.mp3"]
        mus = 2
        nxt = 3
    else:
        nxt = 2
    for img in ["assets/hook.png", "assets/brand.png", "assets/cta.png"]:
        cmd += ["-loop", "1", "-i", img]
    hook_i, brand_i, cta_i = nxt, nxt + 1, nxt + 2
    fc = fc.replace("[1:v]", f"[{hook_i}:v]").replace("[2:v]", f"[{brand_i}:v]").replace("[3:v]", f"[{cta_i}:v]")
    if mus is not None:
        fc += (f";[1:a]volume=1.0,apad[voice];[{mus}:a]volume=0.12[mus];"
               f"[voice][mus]amix=inputs=2:duration=shortest[a]")
        cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", "[a]"]
    else:
        cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", "1:a"]
    cmd += ["-t", D, "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", "out/reel.mp4"]
    run(cmd)
    print(f"reel done {dur('out/reel.mp4'):.1f}s")

if __name__ == "__main__":
    main()
