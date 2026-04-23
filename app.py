from flask import Flask, request, Response, stream_with_context
import edge_tts
import asyncio
import uuid
import os

app = Flask(__name__)

# 🔥 Voice mapping (custom names → real voices)
VOICE_MAP = {
    "male": "en-US-AndrewNeural",
    "female": "en-US-JennyNeural",
    "child": "en-US-AnaNeural"
}

DEFAULT_VOICE = "en-IN-NeerjaNeural"

# 🔥 Long text split
def split_text(text, max_length=3000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

async def generate_audio(text, filename, voice):
    chunks = split_text(text)

    with open(filename, "wb") as f:
        for chunk in chunks:
            communicate = edge_tts.Communicate(chunk, voice)
            await communicate.save(filename)

@app.route("/")
def home():
    return "API Running 😎"

@app.route("/v1/tts", methods=["GET", "POST"])
def tts():
    if request.method == "GET":
        text = request.args.get("text")
        voice_key = request.args.get("voice")  # 🔥 FIX
        voice_key = voice_key.lower() if voice_key else None
    else:
        data = request.get_json()
        text = data.get("text") if data else None
        voice_key = data.get("voice") if data else None  # 🔥 FIX
        voice_key = voice_key.lower() if voice_key else None

    if not text:
        return {"error": "Text required"}, 400

    # 🔥 select voice
    voice = VOICE_MAP.get(voice_key, DEFAULT_VOICE)

    filename = f"{uuid.uuid4()}.mp3"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generate_audio(text, filename, voice))

    def generate():
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                yield chunk
        os.remove(filename)

    return Response(stream_with_context(generate()), mimetype="audio/mpeg")

# 🔥 Render fix (important)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)