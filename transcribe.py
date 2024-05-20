import pandas as pd
import argparse
import requests
import time
import json 
import os 
import datetime


GLADIA_API_KEY = os.getenv('GLADIA_API_KEY')


def generate_csv(json_data):
     # Initialize a list to hold our data tuples
    data_tuples = []
    
     # Iterate over each utterance in the provided JSON data
    for utterance in json_data['result']['transcription']['utterances']:
        text = utterance['text']
        speaker = utterance['speaker']
        timestamp = utterance['start']
        
        # Append each found tuple to the list
        data_tuples.append((text, speaker, timestamp))
        
    # Create a DataFrame from the list of tuples
    df = pd.DataFrame(data_tuples, columns=['text', 'speaker', 'timestamp'])

    # Convert the 'timestamp' column to datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Return the completed DataFrame
    return df


def upload_audio(file_path, audio_extension, api_key=GLADIA_API_KEY):
    """
    Uploads an audio file to the Gladia API.

    Args:
        file_path (str): The path to the audio file.
        api_key (str): Your Gladia API token.
    """

    print('called upload_audio')
    
    # Prepare the headers for the request
    headers = {
        'x-gladia-key': api_key
    }

    # Prepare the file data as a dictionary where the key matches the name in the form data
    files = {
        'audio': ('test_audio', open(file_path, 'rb'), f'audio/{audio_extension}')
    } 

    print(files)
    url = 'https://api.gladia.io/v2/upload'

    try:
        response = requests.post(url, headers=headers, files=files)
        print("Response from server:")
        response_data = json.loads(response.text)
        print(response_data['audio_url'])

        return response_data['audio_url']
    except Exception as e:
        print(f"An error occurred: {e}")


def request_transcription_from_audio_url(audio_url, api_key=GLADIA_API_KEY):
    headers = {
        'Content-Type': 'application/json',
        'x-gladia-key': api_key
    }

    print('called request_transcription_from_audio_url')

    # Prepare the JSON payload for the request.
    data = {
        'audio_url': audio_url,
        "diarization": True
    }

    # Specify the URL for the transcription API endpoint.
    url = 'https://api.gladia.io/v2/transcription'

    try:
        # Send the POST request with the JSON data.
        response = requests.post(url, headers=headers, json=data)
        print(response.text)
        response_data = json.loads(response.text)
        return response_data['result_url']
    except Exception as e:
        print(f"An error occurred: {e}")


def get_transcription(result_url, api_key=GLADIA_API_KEY):
    # Set up the headers including your API key.
    headers = {
        'x-gladia-key': api_key
    }

    # Specify the URL for the transcription API endpoint including the specific resource ID.
    url = result_url

    try:
        # Send the GET request.
        response = requests.get(url, headers=headers)

        # print(response.text)
        transcription = json.loads(response.text)
        return transcription
    
    except Exception as e:
        print(f"An error occurred: {e}")

def transcribe(audio_file, audio_extension):
    """
    Wrapper function that uploads an audio file to the Gladia API, preprocesses transcription and dumps to postgres.
    """
    # Upload audio
    audio_url = upload_audio(audio_file, audio_extension)

    print(audio_file)

    # Request transcription
    result_url = request_transcription_from_audio_url(audio_url)

    # Get transcription
    transcription = ""

    print('called transcribe')

    while True: 
        poll_response = get_transcription(result_url)

        print(poll_response)

        if poll_response['status'] == 'queued':
            time.sleep(1)
            print("Polling for results...")

        elif poll_response['status'] == 'done':
            transcription = poll_response
            print("Transcription done.")
            break

    # Preprocess
    df = generate_csv(transcription)
    print(df.head())

    current_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    filename = "output.csv"

    # TODO : Use a better naming scheme to keep track of multiple transcriptions
    # filename = f"data/transcription_{current_timestamp}.csv"

    # Export to Postgres and dump as csv
    df.to_csv(filename)

    return df


def main():
    # Dont remove, following code is useful to use the script as a CLI
    parser = argparse.ArgumentParser(description="Upload an audio file to the Gladia API.")
    parser.add_argument('file_path', type=str, help='The path to the audio file to upload.')
    parser.add_argument('file_type', type=str, help='The file type of the audio file to upload.')
    args = parser.parse_args()

    # Upload audio
    audio_url = upload_audio(args.file_path, args.file_type)

    # Request transcription
    result_url = request_transcription_from_audio_url(audio_url)

    # Get transcription
    transcription = ""

    while True:
        poll_response = get_transcription(result_url)

        if poll_response['status'] == 'queued':
            time.sleep(1)
            print("Polling for results...")

        elif poll_response['status'] == 'done':
            transcription = poll_response
            print("Transcription done.")
            break

    # Preprocess
    df = generate_csv(transcription)
    print(df.head())

    # Export to Postgres and dump as csv
    df.to_csv('data/output.csv')


if __name__ == '__main__':
    main()