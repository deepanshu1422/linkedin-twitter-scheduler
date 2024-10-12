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
import boto3
from botocore.exceptions import NoCredentialsError
import uuid
import markdown
import re
from html import unescape

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

# DigitalOcean Spaces configuration
s3 = boto3.client('s3',
    endpoint_url=f"https://{os.environ.get('DIGITALOCEAN_SPACE_NAME')}",
    aws_access_key_id=os.environ.get('DIGITALOCEAN_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('DIGITALOCEAN_SECRET_ACCESS_KEY')
)

def upload_to_digitalocean(file):
    try:
        file_name = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        s3.upload_fileobj(
            file,
            os.environ.get('DIGITALOCEAN_BUCKET_NAME'),
            file_name,
            ExtraArgs={'ACL': 'public-read'}
        )
        return f"https://{os.environ.get('DIGITALOCEAN_BUCKET_NAME')}.{os.environ.get('DIGITALOCEAN_SPACE_NAME')}/{file_name}"
    except NoCredentialsError:
        logger.error("DigitalOcean credentials not available")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info("Accessing index route")
    if request.method == 'POST':
        text = request.form['text']
        logger.info(f"Received new post request: {text[:50]}...")
        
        image_url = None
        image_option = request.form.get('imageOption')
        image_prompt = request.form.get('imagePrompt')
        
        if image_option == 'upload' and 'image' in request.files and request.files['image'].filename != '':
            image = request.files['image']
            image_url = upload_to_digitalocean(image)
            logger.info(f"Image uploaded to DigitalOcean: {image_url}")
        elif image_option == 'generate' or image_prompt:
            prompt = image_prompt or text
            logger.info(f"Generating image with prompt: {prompt[:50]}...")
            image_url = generate_image(prompt)
            logger.info(f"Image generated successfully: {image_url}")
        
        post_datetime = find_next_available_slot()
        utc_datetime = post_datetime.astimezone(pytz.UTC)
        
        # Get user options
        post_for_deepanshu = 'post_for_deepanshu' in request.form
        post_for_aryan = 'post_for_aryan' in request.form
        
        result = collection.insert_one({
            'text': text,
            'scheduled_time': utc_datetime,
            'status': 'Scheduled',
            'image_url': image_url,
            'image_prompt': image_prompt,
            'post_for_deepanshu': post_for_deepanshu,
            'post_for_aryan': post_for_aryan
        })
        logger.info(f"Inserted new post with ID: {result.inserted_id}")
        
        return redirect(url_for('index'))

    # Fetch all content from MongoDB
    all_content = list(collection.find())
    
    # Separate scheduled and posted content
    scheduled_content = []
    posted_content = []
    
    ist = pytz.timezone('Asia/Kolkata')
    for content in all_content:
        utc_time = content['scheduled_time'].replace(tzinfo=pytz.UTC)
        ist_time = utc_time.astimezone(ist)
        content['ist_time'] = ist_time.strftime("%Y-%m-%d %I:%M %p IST")
        content['status'] = content.get('status', 'Scheduled')
        content['display_text'] = markdown.markdown(content['text'])  # Convert markdown to HTML for display
        
        if content['status'] == 'Scheduled':
            scheduled_content.append(content)
        else:
            posted_content.append(content)
    
    # Sort scheduled content by scheduled time
    scheduled_content.sort(key=lambda x: x['scheduled_time'])
    
    # Sort posted content by scheduled time in reverse order (most recent first)
    posted_content.sort(key=lambda x: x['scheduled_time'], reverse=True)
    
    # Combine the lists with scheduled content at the top and posted content at the bottom
    content_list = scheduled_content + posted_content
    
    logger.info(f"Fetched {len(content_list)} posts from database")
    
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
        # Use the original markdown text
        text = content['text']
        
        # Convert markdown to HTML
        html_content = markdown.markdown(text)
        
        # Convert HTML to plain text while preserving formatting
        plain_text = html_to_plain_text(html_content)
        
        image_url = content.get('image_url')
        
        if not image_url:
            prompt = content.get('image_prompt') or plain_text
            logger.info(f"Generating image for content: {prompt[:50]}...")
            image_url = generate_image(prompt)
            logger.info(f"Image generated successfully: {image_url}")
            
            # Update the content with the generated image URL
            collection.update_one(
                {'_id': ObjectId(content_id)},
                {'$set': {'image_url': image_url}}
            )
        else:
            logger.info(f"Using existing image: {image_url}")

        # Get user options
        post_for_deepanshu = content.get('post_for_deepanshu', True)
        post_for_aryan = content.get('post_for_aryan', True)

        linkedin_results = []
        twitter_results = []

        if post_for_deepanshu:
            logger.info("Posting to LinkedIn (Deepanshu)...")
            linkedin_results.append(post_to_linkedin(plain_text, image_url, user=1))
            logger.info("Posting to Twitter (Deepanshu)...")
            twitter_results.append(post_to_twitter(plain_text, image_url, user=1))

        if post_for_aryan:
            logger.info("Posting to LinkedIn (Aryan)...")
            linkedin_results.append(post_to_linkedin(plain_text, image_url, user=2))
            logger.info("Posting to Twitter (Aryan)...")
            twitter_results.append(post_to_twitter(plain_text, image_url, user=2))

        logger.info(f"LinkedIn post results: {linkedin_results}")
        logger.info(f"Twitter post results: {twitter_results}")
        
        # Prepare detailed status information
        linkedin_status = {f"account_{i+1}": "Success" if 'id' in result else "Error" for i, result in enumerate(linkedin_results)}
        twitter_status = {f"account_{i+1}": "Success" if 'tweet_id' in result else "Error" for i, result in enumerate(twitter_results)}
        
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

def html_to_plain_text(html_content):
    # Replace <br> and </p> tags with newlines
    text = re.sub(r'<br\s*/?>', '\n', html_content)
    text = re.sub(r'</p>', '\n', text)
    
    # Replace <li> tags with bullet points
    text = re.sub(r'<li>', '• ', text)
    
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Remove extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text

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
            linkedin_status = {f"account_{i+1}": "Success" if result.get('id') else "Error" for i, result in enumerate(linkedin_results)}
            twitter_status = {f"account_{i+1}": "Success" if result.get('tweet_id') else "Error" for i, result in enumerate(twitter_results)}
            
            all_statuses = list(linkedin_status.values()) + list(twitter_status.values())
            overall_status = 'Partial Success' if any(status == 'Success' for status in all_statuses) else 'Error'
            if all(status == 'Success' for status in all_statuses):
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

@app.route('/change_image/<content_id>', methods=['GET', 'POST'])
def change_image(content_id):
    content = collection.find_one({'_id': ObjectId(content_id)})
    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                image_url = upload_to_digitalocean(image)
                collection.update_one(
                    {'_id': ObjectId(content_id)},
                    {'$set': {'image_url': image_url}}
                )
                logger.info(f"Image updated for content ID: {content_id}")
        return redirect(url_for('index'))
    return render_template('change_image.html', content=content)

@app.route('/remove_image/<content_id>')
def remove_image(content_id):
    collection.update_one(
        {'_id': ObjectId(content_id)},
        {'$unset': {'image_url': ''}}
    )
    logger.info(f"Image removed for content ID: {content_id}")
    return redirect(url_for('index'))

@app.route('/regenerate_image/<content_id>', methods=['POST'])
def regenerate_image(content_id):
    content = collection.find_one({'_id': ObjectId(content_id)})
    if not content:
        return jsonify({'error': 'Content not found'}), 404
    
    prompt = request.form.get('prompt', content['text'])
    try:
        logger.info(f"Regenerating image for content ID: {content_id} with prompt: {prompt[:50]}...")
        new_image_url = generate_image(prompt)
        logger.info(f"New image generated: {new_image_url}")
        
        update_result = collection.update_one(
            {'_id': ObjectId(content_id)},
            {'$set': {'image_url': new_image_url}}
        )
        
        if update_result.modified_count == 1:
            logger.info(f"Image URL updated for content ID: {content_id}")
            return jsonify({'success': True, 'new_image_url': new_image_url})
        else:
            logger.error(f"Failed to update image URL for content ID: {content_id}")
            return jsonify({'error': 'Failed to update image URL'}), 500
    except Exception as e:
        logger.error(f"Error regenerating image: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-cron', methods=['GET'])
def run_cron():
    # Verify the request using a secret key
    secret_key = request.args.get('key')
    if secret_key != os.environ.get('CRON_SECRET_KEY'):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        results = process_scheduled_posts()
        return jsonify({"message": "Cron job completed", "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)