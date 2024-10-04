from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from ideogram_generator import generate_image
from social_media_poster import post_to_linkedin, post_to_twitter
import os
from dotenv import load_dotenv
import logging
import requests
from datetime import datetime, timedelta
import pytz

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['content_database']
collection = db['posts']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        
        # Find the next available slot
        post_datetime = find_next_available_slot()
        
        # Convert to UTC for storage
        utc_datetime = post_datetime.astimezone(pytz.UTC)
        
        # Insert content into MongoDB
        result = collection.insert_one({
            'text': text,
            'scheduled_time': utc_datetime
        })
        
        return redirect(url_for('index'))

    # Fetch all content from MongoDB, sorted by scheduled time
    content_list = list(collection.find().sort('scheduled_time', 1))
    
    # Convert UTC times to IST for display
    ist = pytz.timezone('Asia/Kolkata')
    for content in content_list:
        utc_time = content['scheduled_time'].replace(tzinfo=pytz.UTC)
        ist_time = utc_time.astimezone(ist)
        content['ist_time'] = ist_time.strftime("%Y-%m-%d %I:%M %p IST")
    
    return render_template('index.html', content_list=content_list)

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

@app.route('/delete_content/<content_id>')
def delete_content(content_id):
    collection.delete_one({'_id': ObjectId(content_id)})
    return redirect(url_for('index'))

@app.route('/edit_content/<content_id>', methods=['GET', 'POST'])
def edit_content(content_id):
    content = collection.find_one({'_id': ObjectId(content_id)})
    if request.method == 'POST':
        text = request.form['text']
        
        collection.update_one(
            {'_id': ObjectId(content_id)},
            {'$set': {'text': text}}
        )
        return redirect(url_for('index'))
    
    ist = pytz.timezone('Asia/Kolkata')
    content['ist_time'] = content['scheduled_time'].replace(tzinfo=pytz.UTC).astimezone(ist).strftime("%Y-%m-%d %I:%M %p IST")
    return render_template('edit_content.html', content=content)

@app.route('/api/process_scheduled_posts', methods=['GET'])
def process_scheduled_posts():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Find posts scheduled for the current hour
    start_of_hour = now.replace(minute=0, second=0, microsecond=0)
    end_of_hour = start_of_hour + timedelta(hours=1)
    
    scheduled_posts = collection.find({
        'scheduled_time': {
            '$gte': start_of_hour.astimezone(pytz.UTC),
            '$lt': end_of_hour.astimezone(pytz.UTC)
        },
        'posted': {'$ne': True}
    })
    
    results = []
    for post in scheduled_posts:
        try:
            image_url = generate_image(post['text'])
            linkedin_result = post_to_linkedin(post['text'], image_url)
            twitter_result = post_to_twitter(post['text'], image_url)
            
            # Mark the post as posted
            collection.update_one(
                {'_id': post['_id']},
                {'$set': {'posted': True, 'post_results': {
                    'linkedin': linkedin_result,
                    'twitter': twitter_result,
                    'image_url': image_url
                }}}
            )
            
            results.append({
                'post_id': str(post['_id']),
                'status': 'success',
                'linkedin': linkedin_result,
                'twitter': twitter_result
            })
        except Exception as e:
            logging.error(f"Error processing scheduled post {post['_id']}: {str(e)}")
            results.append({
                'post_id': str(post['_id']),
                'status': 'error',
                'error': str(e)
            })
    
    return jsonify(results)

def find_next_available_slot():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    slot_times = [10, 17, 21]  # 10 AM, 5 PM, 9 PM
    
    current_date = now.date()
    while True:
        for hour in slot_times:
            slot = ist.localize(datetime.combine(current_date, datetime.min.time().replace(hour=hour)))
            if slot <= now:
                continue
            if not collection.find_one({'scheduled_time': slot.astimezone(pytz.UTC)}):
                return slot
        current_date += timedelta(days=1)

if __name__ == '__main__':
    # This is used when running locally. Gunicorn uses the app variable directly
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))