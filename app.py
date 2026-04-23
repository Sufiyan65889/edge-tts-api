from flask import Flask, request, Response, stream_with_context
import edge_tts
import asyncio
import uuid
import os

app = Flask(__name__)

VOICE = "en-IN-PrabhatNeural"

# 🔥 Long text split function
def split_text(text, max_length=3000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

async def generate_audio_chunks(text, filename):
    chunks = split_text(text)
    
    with open(filename, "wb") as f:
        for chunk in chunks:
            communicate = edge_tts.Communicate(chunk, VOICE)
            await communicate.save(filename)

@app.route("/v1/tts", methods=["GET", "POST"])
def tts():
    if request.method == "GET":
        text = request.args.get("text")
    else:
        data = request.get_json()
        text = data.get("text") if data else None

    if not text:
        return {"error": "Text required"}, 400

    filename = f"{uuid.uuid4()}.mp3"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generate_audio_chunks(text, filename))

    def generate():
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                yield chunk
        os.remove(filename)

    return Response(stream_with_context(generate()), mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run()
