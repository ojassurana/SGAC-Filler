from openai import OpenAI

client = OpenAI(api_key='')
import base64

def get_captcha_text(image_path="captcha.png"):
    """
    Extract captcha text from an image using OpenAI's vision model.
    
    Args:
        image_path (str): Path to the captcha image file
        api_key (str): OpenAI API key
        
    Returns:
        str: The extracted captcha text
    """
    # Set your OpenAI API key

    # Read and encode the image
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Create the message payload
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's the exact captcha text? (ONLY GIVE THE TEXT, NO OTHER TEXT)"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_image}"
                    }
                }
            ]
        }
    ]

    # Send the request to the GPT-4.1 Mini model
    response = client.chat.completions.create(model="gpt-4.1-mini",
    messages=messages)

    # Return the response with no spaces
    return response.choices[0].message.content.replace(" ", "")
