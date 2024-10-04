import requests
import os
import tweepy
import logging
import io
import json
from dotenv import load_dotenv

load_dotenv()

# LinkedIn credentials
LINKEDIN_ACCESS_TOKEN = os.environ.get('LINKEDIN_ACCESS_TOKEN')
LINKEDIN_ACCESS_TOKEN_2 = os.environ.get('LINKEDIN_ACCESS_TOKEN_2')

# Twitter credentials for first account
TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Twitter credentials for second account
TWITTER_API_KEY_2 = os.environ.get('TWITTER_API_KEY_2')
TWITTER_API_SECRET_2 = os.environ.get('TWITTER_API_SECRET_2')
TWITTER_ACCESS_TOKEN_2 = os.getenv('TWITTER_ACCESS_TOKEN_2')
TWITTER_ACCESS_TOKEN_SECRET_2 = os.getenv('TWITTER_ACCESS_TOKEN_SECRET_2')

def get_linkedin_person_urn(token):
    url = 'https://api.linkedin.com/v2/userinfo'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    logging.info(f"LinkedIn API response status code: {response.status_code}")
    logging.info(f"LinkedIn API response content: {response.text}")
    
    if response.status_code == 200:
        try:
            user_info = response.json()
            return f"urn:li:person:{user_info['sub']}"
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from LinkedIn response")
            logging.error(f"Response content: {response.text}")
            return None
        except KeyError as e:
            logging.error(f"Key 'sub' not found in LinkedIn response: {e}")
            logging.error(f"Response content: {response.text}")
            return None
    else:
        logging.error(f"Failed to fetch LinkedIn user info. Status code: {response.status_code}")
        logging.error(f"Response content: {response.text}")
        return None

def register_image_with_linkedin(image_url, token):
    register_url = 'https://api.linkedin.com/v2/assets?action=registerUpload'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": get_linkedin_person_urn(token),
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    response = requests.post(register_url, headers=headers, json=data)
    if response.status_code == 200:
        response_data = response.json()
        asset = response_data['value']['asset']
        upload_url = response_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        
        # Upload the image
        with requests.get(image_url, stream=True) as r:
            r.raise_for_status()
            upload_response = requests.put(upload_url, data=r.content, headers={'Content-Type': 'image/jpeg'})
        
        if upload_response.status_code == 201:
            return asset  # Return the full asset URN
        else:
            logging.error(f"Failed to upload image to LinkedIn. Status code: {upload_response.status_code}")
            logging.error(f"Response content: {upload_response.text}")
            return None
    else:
        logging.error(f"Failed to register image with LinkedIn. Status code: {response.status_code}")
        logging.error(f"Response content: {response.text}")
        return None

def post_to_linkedin(text, image_url):
    results = []
    for token in [LINKEDIN_ACCESS_TOKEN, LINKEDIN_ACCESS_TOKEN_2]:
        url = 'https://api.linkedin.com/v2/ugcPosts'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        person_urn = get_linkedin_person_urn(token)
        if not person_urn:
            results.append({'error': 'Failed to fetch LinkedIn person URN'})
            continue
        
        asset_urn = register_image_with_linkedin(image_url, token)
        if not asset_urn:
            results.append({'error': 'Failed to register image with LinkedIn'})
            continue
        
        # Extract the digitalmediaAsset part from the asset_urn
        asset_id = asset_urn.split(',')[0].split(':')[-1]
        
        # Replace <br> tags with \n for LinkedIn
        linkedin_text = text.replace('<br>', '\n')
        
        data = {
            'author': person_urn,
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {
                        'text': linkedin_text
                    },
                    'shareMediaCategory': 'IMAGE',
                    'media': [
                        {
                            'status': 'READY',
                            'description': {
                                'text': 'Image description'
                            },
                            'media': f'urn:li:digitalmediaAsset:{asset_id}'
                        }
                    ]
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        logging.info(f"LinkedIn post response status code: {response.status_code}")
        logging.info(f"LinkedIn post response content: {response.text}")
        
        if response.status_code == 201:
            try:
                results.append(response.json())
            except json.JSONDecodeError:
                logging.error("Failed to decode JSON from LinkedIn post response")
                results.append({'error': 'Failed to decode LinkedIn response'})
        else:
            logging.error(f"Failed to post to LinkedIn. Status code: {response.status_code}")
            logging.error(f"Response content: {response.text}")
            results.append({'error': f'Failed to post to LinkedIn: {response.text}'})
    
    return results

def post_to_twitter(text, image_url=None):
    results = []
    for credentials in [
        (TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET),
        (TWITTER_API_KEY_2, TWITTER_API_SECRET_2, TWITTER_ACCESS_TOKEN_2, TWITTER_ACCESS_TOKEN_SECRET_2)
    ]:
        try:
            api_key, api_secret, access_token, access_token_secret = credentials
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            # Replace <br> tags with \n for Twitter
            twitter_text = text.replace('<br>', '\n')

            # Truncate the text to 280 characters (Twitter's current limit)
            truncated_text = twitter_text[:280]

            if image_url:
                # Download image
                image_response = requests.get(image_url)
                if image_response.status_code != 200:
                    raise Exception(f"Failed to download image from URL. Status code: {image_response.status_code}")
                
                # Create a file-like object from the image content
                image_file = io.BytesIO(image_response.content)
                
                # Upload image
                auth = tweepy.OAuthHandler(api_key, api_secret)
                auth.set_access_token(access_token, access_token_secret)
                api = tweepy.API(auth)
                media = api.media_upload(filename="temp_image.jpg", file=image_file)
                
                # Post tweet with image
                response = client.create_tweet(text=truncated_text, media_ids=[media.media_id])
            else:
                # Post tweet without image
                response = client.create_tweet(text=truncated_text)
            
            results.append({'tweet_id': response.data['id']})
        except Exception as e:
            logging.error(f"Error posting to Twitter: {str(e)}")
            results.append({'error': f'Error posting to Twitter: {str(e)}'})
    
    return results