import requests
import os
import json

IDEOGRAM_API_KEY = os.environ.get('IDEOGRAM_API_KEY')
IDEOGRAM_API_URL = 'https://api.ideogram.ai/generate'

def generate_image(text):
    headers = {
        'Api-Key': IDEOGRAM_API_KEY,
        'Content-Type': 'application/json'
    }
    
    data = {
        "image_request": {
            "prompt": text,
            "aspect_ratio": "ASPECT_10_16",
            "model": "V_2",
            "magic_prompt_option": "AUTO"
        }
    }
    
    response = requests.post(IDEOGRAM_API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        response_data = response.json()
        if 'data' in response_data and len(response_data['data']) > 0:
            image_url = response_data['data'][0]['url']
            return image_url
        else:
            raise Exception("No image data in the response")
    else:
        raise Exception(f"Failed to generate image: {response.text}")