from flask import Flask, render_template, request, jsonify, redirect, url_for, current_app
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
import sys

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
    logger.info("Accessing index route")
    if request.method == 'POST':
        text = request.form['text']
        logger.info(f"Received new post request: {text[:50]}...")
        
        # Store the text as-is, without replacing newlines
        text_to_store = text
        
        # Find the next available slot
        post_datetime = find_next_available_slot()
        
        # Convert to UTC for storage
        utc_datetime = post_datetime.astimezone(pytz.UTC)
        
        # Insert content into MongoDB
        result = collection.insert_one({
            'text': text_to_store,
            'scheduled_time': utc_datetime,
            'status': 'Scheduled'  # Set initial status
        })
        logger.info(f"Inserted new post with ID: {result.inserted_id}")
        
        return redirect(url_for('index'))

    # Fetch all content from MongoDB, sorted by scheduled time
    content_list = list(collection.find().sort('scheduled_time', 1))
    logger.info(f"Fetched {len(content_list)} posts from database")
    
    # Convert UTC times to IST for display
    ist = pytz.timezone('Asia/Kolkata')
    for content in content_list:
        utc_time = content['scheduled_time'].replace(tzinfo=pytz.UTC)
        ist_time = utc_time.astimezone(ist)
        content['ist_time'] = ist_time.strftime("%Y-%m-%d %I:%M %p IST")
        content['status'] = content.get('status', 'Scheduled')
    
    return render_template('index.html', content_list=content_list)

@app.route('/generate_and_post', methods=['POST'])
def generate_and_post():
    content_id = request.form['content_id']
    logger.info(f"Received generate_and_post request for content ID: {content_id}")
    
    # Fetch content from MongoDB
    content = collection.find_one({'_id': ObjectId(content_id)})
    
    if not content:
        logger.error(f"Content not found for ID: {content_id}")
        return jsonify({'error': 'Content not found'}), 404
    
    try:
        # Use the text as-is
        text = content['text']
        logger.info(f"Generating image for content: {text[:50]}...")
        image_url = generate_image(text)
        logger.info(f"Image generated successfully: {image_url}")

        logger.info("Posting to LinkedIn...")
        linkedin_results = post_to_linkedin(text, image_url)
        logger.info(f"LinkedIn post results: {linkedin_results}")

        logger.info("Posting to Twitter...")
        twitter_results = post_to_twitter(text, image_url)
        logger.info(f"Twitter post results: {twitter_results}")
        
        # Prepare detailed status information
        linkedin_status = {f"account_{i+1}": "Success" if 'id' in result else "Error" for i, result in enumerate(linkedin_results)}
        twitter_status = {f"account_{i+1}": "Success" if 'tweet_id' in result else "Error" for i, result in enumerate(twitter_results)}
        
        # Fix: Convert dict_values to list before concatenation
        all_statuses = list(linkedin_status.values()) + list(twitter_status.values())
        overall_status = 'Partial Success' if any(status == 'Success' for status in all_statuses) else 'Error'
        if all(status == 'Success' for status in all_statuses):
            overall_status = 'Success'
        
        # Update the post status
        update_result = collection.update_one(
            {'_id': ObjectId(content_id)},
            {'$set': {
                'status': overall_status,
                'post_results': {
                    'linkedin': linkedin_status,
                    'twitter': twitter_status,
                    'image_url': image_url
                }
            }}
        )
        logger.info(f"Post status updated. Update result: {update_result.modified_count} document(s) modified")
        
        return jsonify({
            'status': overall_status,
            'linkedin_results': linkedin_results,
            'twitter_results': twitter_results,
            'image_url': image_url
        })
    except Exception as e:
        logger.error(f"Error in generate_and_post: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/delete_content/<content_id>')
def delete_content(content_id):
    logger.info(f"Deleting content with ID: {content_id}")
    result = collection.delete_one({'_id': ObjectId(content_id)})
    logger.info(f"Delete result: {result.deleted_count} document(s) deleted")
    return redirect(url_for('index'))

@app.route('/edit_content/<content_id>', methods=['GET', 'POST'])
def edit_content(content_id):
    logger.info(f"Accessing edit_content route for content ID: {content_id}")
    content = collection.find_one({'_id': ObjectId(content_id)})
    if request.method == 'POST':
        text = request.form['text']
        logger.info(f"Updating content: {text[:50]}...")
        
        # Store the text as-is, without replacing newlines
        result = collection.update_one(
            {'_id': ObjectId(content_id)},
            {'$set': {'text': text}}
        )
        logger.info(f"Update result: {result.modified_count} document(s) modified")
        return redirect(url_for('index'))
    
    ist = pytz.timezone('Asia/Kolkata')
    content['ist_time'] = content['scheduled_time'].replace(tzinfo=pytz.UTC).astimezone(ist).strftime("%Y-%m-%d %I:%M %p IST")
    return render_template('edit_content.html', content=content)

@app.route('/api/process_scheduled_posts', methods=['GET'])
def process_scheduled_posts():
    with app.app_context():
        logger.info("Processing scheduled posts")
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Find posts scheduled for the current time or earlier
        logger.info(f"Searching for posts scheduled up to {now} IST")
        scheduled_posts = collection.find({
            'scheduled_time': {'$lte': now.astimezone(pytz.UTC)},
            'status': 'Scheduled'  # Only process posts that are still scheduled
        })
        
        results = []
        for post in scheduled_posts:
            logger.info(f"Processing post: {post['_id']}")
            try:
                # Use the text as-is
                text = post['text']
                logger.info(f"Generating image for post: {text[:50]}...")
                image_url = generate_image(text)
                logger.info(f"Image generated: {image_url}")

                logger.info("Posting to LinkedIn...")
                linkedin_results = post_to_linkedin(text, image_url)
                logger.info(f"LinkedIn results: {linkedin_results}")

                logger.info("Posting to Twitter...")
                twitter_results = post_to_twitter(text, image_url)
                logger.info(f"Twitter results: {twitter_results}")
                
                # Prepare detailed status information
                linkedin_status = {f"account_{i+1}": "Success" if 'id' in result else "Error" for i, result in enumerate(linkedin_results)}
                twitter_status = {f"account_{i+1}": "Success" if 'tweet_id' in result else "Error" for i, result in enumerate(twitter_results)}
                
                overall_status = 'Partial Success' if any(status == 'Success' for status in linkedin_status.values() + twitter_status.values()) else 'Error'
                if all(status == 'Success' for status in linkedin_status.values() + twitter_status.values()):
                    overall_status = 'Success'
                
                # Update the post status
                update_result = collection.update_one(
                    {'_id': post['_id']},
                    {'$set': {
                        'status': overall_status,
                        'post_results': {
                            'linkedin': linkedin_status,
                            'twitter': twitter_status,
                            'image_url': image_url
                        }
                    }}
                )
                logger.info(f"Post status updated. Update result: {update_result.modified_count} document(s) modified")
                
                results.append({
                    'post_id': str(post['_id']),
                    'status': overall_status,
                    'linkedin': linkedin_status,
                    'twitter': twitter_status
                })
            except Exception as e:
                logger.error(f"Error processing scheduled post {post['_id']}: {str(e)}", exc_info=True)
                # Update the post status to indicate an error
                collection.update_one(
                    {'_id': post['_id']},
                    {'$set': {'status': 'Error'}}
                )
                results.append({
                    'post_id': str(post['_id']),
                    'status': 'Error',
                    'error': str(e)
                })
        
        logger.info(f"Processed {len(results)} scheduled posts")
        return results

@app.route('/trigger_cron', methods=['GET'])
def trigger_cron():
    results = process_scheduled_posts()
    return jsonify(results)

@app.route('/find_next_slot', methods=['GET'])
def find_next_slot():
    return jsonify({'next_slot': find_next_available_slot().isoformat()})

def find_next_available_slot(start_time=None):
    logger.info("Finding next available slot")
    ist = pytz.timezone('Asia/Kolkata')
    now = start_time or datetime.now(ist)
    slot_times = [10, 17, 21]  # 10 AM, 5 PM, 9 PM
    
    current_date = now.date()
    while True:
        for hour in slot_times:
            slot = ist.localize(datetime.combine(current_date, datetime.min.time().replace(hour=hour)))
            if slot <= now:
                continue
            if not collection.find_one({'scheduled_time': slot.astimezone(pytz.UTC)}):
                logger.info(f"Next available slot found: {slot}")
                return slot
        current_date += timedelta(days=1)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)