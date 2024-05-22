
from minio import Minio
from minio.error import S3Error
import requests 
import uuid
import os 

S3_URL = os.getenv("S3_URL")
S3_USERNAME = os.getenv("S3_USERNAME")
S3_PASSWORD = os.getenv("S3_PASSWORD")
S3_BUCKET = os.getenv("S3_BUCKET")

minio_client = Minio(
            S3_URL,
            access_key=S3_USERNAME,
            secret_key=S3_PASSWORD,
            secure=True
        )

def generate_html(posts):
    # Only for testing : Generates HTML page with the currently generated posts and stores them as 'index.html' file
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Social Media Posts</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f9;
                margin: 0;
                padding: 20px;
            }
            .post {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 8px;
                margin-bottom: 20px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .title {
                font-size: 24px;
                color: #333;
                font-weight: bold;
            }
            .caption {
                font-size: 16px;
                color: #666;
                margin-top: 10px;
            }
            img {
                width: 100%;
                max-width: 600px;
                height: auto;
                display: block;
                margin: 0 auto 10px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
    """
    
    # Loop through each post using the provided iteration style
    for key, val in posts.items():
        html_content += f"""
        <div class="post">
            <div class="title">{key}</div>
            <div class="caption">{val['content']}</div>
            <img src="{val['image_url']}" alt="Image for {key}">
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(html_content)
 

def upload_to_minio(image_url,
                    bucket=S3_BUCKET,
                    ):
    try:
        object_name = str(uuid.uuid4())
        # Get image from Dalle generated URL
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)

        # Upload the file 
        minio_client.put_object(
            bucket,
            object_name,
            data=response.raw,
            length=int(response.headers.get('content-length')),
            content_type=response.headers.get('content-type')
        )
        print(f"Image is successfully uploaded with id='{object_name}' to bucket '{bucket}'.")
        return object_name
    except S3Error as e:
        print(f"File upload failed: {e}")
        return '' # Returns an empty string in case the upload was unsuccessful


def download_image_from_url(url):
    try:
        # Download the image from url
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.raw
    except requests.RequestException as e:
        print(f"Error downloading the image: {e}")
    except Exception as e:
        print(e)


def list_objects_in_bucket(bucket_name=S3_BUCKET):
    """
    List all objects in a MinIO bucket

    :param bucket_name: Name of the bucket to list objects from
    """
    try:
        # List objects in the bucket
        objects = minio_client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            print(f"Object: {obj.object_name} - Size: {obj.size} bytes")
    except S3Error as e:
        print(f"Error occurred: {e}")

list_objects_in_bucket()