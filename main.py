from flask import Flask, request, jsonify
from transcribe import transcribe, upload_audio
from topic_model import TopicModel
import pandas as pd
from utils import generate_html
from waitress import serve

app = Flask(__name__)

@app.route('/analyze-audio', methods=['POST'])
def transcription():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file part"}), 400

    audio_file = request.files['audio_file']
    audio_extension = audio_file.filename.split('.')[-1]

    if audio_file:
        file_path = f"temp.{audio_extension}"
        audio_file.save(file_path)

        data = transcribe(file_path, audio_extension)

        # If transcription is successful, start topic modeling
        if data is not None:
            topic_model = TopicModel(data['text'].values)
            posts = topic_model.get_posts()
            generate_html(posts)

    return jsonify({"error": "Invalid file"}), 400


if __name__ == '__main__':
    # Production server
    serve(app, host="0.0.0.0", port=8080)

    # Debug server
    # app.run(debug=True)
