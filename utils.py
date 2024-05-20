
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
 