from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from ideogram_generator import generate_image
from social_media_poster import post_to_linkedin, post_to_twitter
import os
from dotenv import load_dotenv
import logging
import requests

load_dotenv()
logging.basicConfig(level=logging.ERROR)  # Changed to ERROR level

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# MongoDB connection
client = MongoClient(os.environ.get('MONGO_URI'))
db = client['content_database']
collection = db['posts']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_and_post', methods=['POST'])
def generate_and_post():
    content_id = request.form['content_id']
    
    # Fetch content from MongoDB
    content = collection.find_one({'_id': ObjectId(content_id)})
    
    if not content:
        return jsonify({'error': 'Content not found'}), 404
    
    try:

        image_url = generate_image(content['text'])
        # Post to LinkedIn
        linkedin_result = post_to_linkedin(content['text'], image_url)

        # Post to Twitter
        twitter_result = post_to_twitter(content['text'], image_url)
        
        errors = []
        if 'error' in linkedin_result:
            errors.append(f"LinkedIn error: {linkedin_result['error']}")
        if 'error' in twitter_result:
            errors.append(f"Twitter error: {twitter_result['error']}")
        
        if errors:
            return jsonify({'errors': errors}), 500
        
        return jsonify({
            'linkedin_result': linkedin_result,
            'twitter_result': twitter_result,
            'image_url': image_url
        })
    except Exception as e:
        logging.error(f"Error in generate_and_post: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/insert_content', methods=['GET', 'POST'])
def insert_content():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        
        # Insert content into MongoDB
        result = collection.insert_one({
            'title': title,
            'text': text
        })
        
        return redirect(url_for('index'))
    
    return render_template('insert_content.html')

@app.route('/view_content')
def view_content():
    # Fetch all content from MongoDB
    content_list = list(collection.find())
    return render_template('view_content.html', content_list=content_list)

@app.route('/get_linkedin_profile')
def get_linkedin_profile():
    url = 'https://api.linkedin.com/v2/me'
    headers = {
        'Authorization': f'Bearer {os.environ.get("LINKEDIN_ACCESS_TOKEN")}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        profile_data = response.json()
        person_urn = profile_data.get('id')
        return jsonify({'person_urn': f'urn:li:person:{person_urn}'})
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch LinkedIn profile: {str(e)}")
        return jsonify({'error': f'Failed to fetch LinkedIn profile: {str(e)}'}), 400

@app.route('/test_linkedin_profile')
def test_linkedin_profile():
    from social_media_poster import get_linkedin_person_urn
    urn = get_linkedin_person_urn()
    if urn:
        return jsonify({'success': True, 'linkedin_urn': urn})
    else:
        return jsonify({'success': False, 'error': 'Failed to fetch LinkedIn URN'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)