import requests
import os
import json
import logging

IDEOGRAM_API_KEY = os.environ.get('IDEOGRAM_API_KEY')
IDEOGRAM_API_URL = 'https://api.ideogram.ai/generate'

logger = logging.getLogger(__name__)

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
    
    logger.info(f"Sending request to Ideogram API with prompt: {text[:50]}...")
    
    try:
        response = requests.post(IDEOGRAM_API_URL, headers=headers, json=data)
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        
        response_data = response.json()
        logger.info(f"Received response from Ideogram API: {json.dumps(response_data, indent=2)}")
        
        if 'data' in response_data and len(response_data['data']) > 0:
            image_url = response_data['data'][0]['url']
            logger.info(f"Successfully generated image URL: {image_url}")
            return image_url
        else:
            logger.error("No image data in the response")
            raise Exception("No image data in the response")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to Ideogram API failed: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_image: {str(e)}")
        raise