# prototype-ai

# Setup virtual environment
`python -m venv env`

# Install dependencies
`pip install -r requirements.txt`

# Setup Environment variables
```
OPEN_AI_PROJECT_ID = ""
OPEN_AI_ORGANIZATION_ID = ""
OPEN_AI_API_KEY = ""
GLADIA_API_KEY = ""
POSTGRES_PASSWORD = ""
POSTGRES_USER = ""
POSTGRES_HOST = ""
POSTGRES_DB_NAME = ""
POSTGRES_PORT = ""
```

# Start the flask server
`python main.py`

# Note

- The script will automatically generate some temporary files and keep on overwriting them. Currently `index.html`, `output.csv` and `temp.wav` will be the temp files.

- For current version, the ai generated posts that will be saved to database consist of the some hardcoded fields for now like the `author_id`, `image_id`, `status`, and `type`.