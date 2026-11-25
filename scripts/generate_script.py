import json, os, re, sys
import requests

PRODUCT = "product.json"
OUT = "data/script.json"

def template():
    with open(PRODUCT) as f:
        p = json.load(f)
    name = p["product_name"]
    b = p["benefits"][:3]
    hook = f"Stop scrolling if you have this problem with {name.lower()}"
    text = (
        f"{hook}. "
        f"If you are {p['target']}, listen. "
        f"{name}: {p['one_liner']}. "
        f"One, {b[0]}. Two, {b[1]}. Three, {b[2]}. "
        f"{p['cta']}."
    )
    caption = f"{hook}\n\n{name}: {p['one_liner']}\n\n{p['cta']}\n\n" + " ".join("#"+h for h in p["hashtags"])
    visuals = [
        p.get("pexels_query", "lifestyle"),
        f"{p['target']} portrait",
        f"{b[0]} closeup",
    ]
    return {"hook": hook, "script_text": text, "caption": caption, "visuals": visuals}

def gemini(p):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    prompt = (
        "Write a 20-30 second Instagram Reel script that sells a product. "
        "Return ONLY valid JSON with keys: hook (max 12 words, punchy, first 2 seconds), "
        "script_text (55-75 words, spoken, simple English, problem then 3 benefits then CTA), "
        "caption (3 lines + CTA + 5-8 hashtags), "
        "visuals (array of exactly 3 short stock-video search queries, 2-5 words each, "
        "no brand names, portrait-friendly: beat 1 = the problem, beat 2 = product in use, "
        "beat 3 = happy result).\n\n"
        f"Product: {p['product_name']}\nDoes: {p['one_liner']}\nFor: {p['target']}\n"
        f"Benefits: {'; '.join(p['benefits'])}\nCTA: {p['cta']}"
    )
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + key,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
        r.raise_for_status()
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        m = re.search(r"\{.*\}", txt, re.S)
        d = json.loads(m.group(0) if m else txt)
        assert "hook" in d and "script_text" in d and "caption" in d
        v = d.get("visuals")
        if not isinstance(v, list) or not [s for s in v if isinstance(s, str) and s.strip()]:
            d["visuals"] = [p.get("pexels_query", "lifestyle")]
        else:
            d["visuals"] = [s.strip() for s in v if isinstance(s, str) and s.strip()][:3]
        return d
    except Exception as e:
        print(f"Gemini failed, using template. Reason: {e}", file=sys.stderr)
        return None

def main():
    os.makedirs("data", exist_ok=True)
    with open(PRODUCT) as f:
        p = json.load(f)
    d = gemini(p) or template()
    # keep it short enough for 60s reel
    words = d["script_text"].split()
    if len(words) > 85:
        d["script_text"] = " ".join(words[:85])
    with open(OUT, "w") as f:
        json.dump(d, f, indent=2)
    print(f"script: {d['hook']}")

if __name__ == "__main__":
    main()
