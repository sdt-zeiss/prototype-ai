from openai import OpenAI
import os 

OPEN_AI_PROJECT_ID = os.getenv('OPEN_AI_PROJECT_ID')
OPEN_AI_ORGANIZATION_ID = os.getenv('OPEN_AI_ORGANIZATION_ID')
OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')

client = OpenAI( 
    organization=OPEN_AI_ORGANIZATION_ID,
    project=OPEN_AI_PROJECT_ID,
    api_key=OPEN_AI_API_KEY
)

def prompt_chatgpt(messages, model='gpt-3.5-turbo'):
    return client.chat.completions.create(
      model=model,
      messages=messages
    )

def prompt_dalle(prompt):
    url = client.images.generate(
      model="dall-e-3",
      prompt=prompt,
      size="1024x1024",
      quality="standard",
      n=1,
    ).data[0].url
    print(f"Generated Image: {url}")
    return url