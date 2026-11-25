import json, subprocess, os

with open("product.json") as f:
    voice = json.load(f).get("voice", "en-US-AriaNeural")
with open("data/script.json") as f:
    text = json.load(f)["script_text"]

os.makedirs("assets", exist_ok=True)
# edge-tts CLI is the simplest reliable call (no key needed)
subprocess.run(
    ["edge-tts", "--voice", voice, "--text", text, "--write-media", "assets/voice.mp3"],
    check=True,
)
print("voice ok")
