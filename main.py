from flask import Flask, request, jsonify
from transcribe import transcribe, upload_audio
from topic_model import TopicModel
import pandas as pd
from waitress import serve
from rag import answer_query
from flask_cors import CORS
from indexer import preprocess_comments
import os

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


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
            return jsonify({"posts": posts}), 200
        else:
            return jsonify({"error": "Transcription failed"}), 400
    else:
        return jsonify({"error": "Invalid file"}), 400


@app.route('/analyze-url', methods=['POST'])
def transcribe_url():
    print(request, request.json)
    if 'audio_url' not in request.json:
        return jsonify({"error": "No audio url part"}), 400

    audio_url = request.json['audio_url']

    if audio_url:
        data = transcribe("", "", audio_url)
        # If transcription is successful, start topic modeling
        if data is not None:
            topic_model = TopicModel(data['text'].values)
            posts = topic_model.get_posts()
            return jsonify({"posts": posts}), 200
        else:
            return jsonify({"error": "Transcription failed"}), 400
    else:
        return jsonify({"error": "Invalid file"}), 400


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({"error": "Question is required"}), 400

    # Run the RAG pipeline
    result = answer_query(question)

    return jsonify({"answer": result})


@app.route('/preprocess-comments', methods=['POST'])
def prepare_vectors():
    try:
        connection_string = "postgresql+psycopg://webapp:KdcCAQydYH4yMYnYqAA58GOhxSYFefMZZssLpQHsv1cV@postgres-16.sliplane.app:5432/prototype" # Hardcoding for now
        preprocess_comments(connection_string)
        return jsonify({"status": "success", "message": "Comments added to the vectorstore successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Production server
    serve(app, host="0.0.0.0", port=8080)

    # Debug server
    # app.run(debug=True)
