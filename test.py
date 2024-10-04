import tweepy

# Twitter API credentials
API_KEY = 'D3VoNR3byUqoMxHM2hwRVhMmk'
API_KEY_SECRET = 'K2qoQh9CXAV6OiR9yWTRNdpn2j5OpCoz9Ssu9FCsda1JQdQDzn'
ACCESS_TOKEN = '163796356-MwOPQSsHpHiAeTR0sGiy4V9M0RmiBFW87I3daCOB'
ACCESS_TOKEN_SECRET = 'xZhK1I2oaMrZ7X8OM5amQeNpM58yMQg8E2I6KlxBAWeKq'

# # Authenticate to Twitter
# auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
# auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
# api = tweepy.API(auth)
#
# # File path to the media you want to upload (image or video)
# media_file_path = 'tesr.png'  # Update the file path
#
# # The text of the tweet
# tweet_text = "This is a tweet with an image!"
#
# # Upload media to Twitter
# media = api.media_upload(media_file_path)
#
# # Post tweet with media
# api.update_status(status=tweet_text, media_ids=[media.media_id])


import tweepy

client = tweepy.Client(consumer_key=API_KEY,consumer_secret=API_KEY_SECRET,access_token=ACCESS_TOKEN,access_token_secret=ACCESS_TOKEN_SECRET)

image_url = "https://ideogram.ai/api/images/ephemeral/UuWdIFLGQpynI-2jGHzELA.png?exp=1728117358&sig=465e19ea36f4070190965e3fd4ac7219da0b9813c7844874417dccd3e609ef78"


client.create_tweet(text="Hello World" )


print("Tweet posted successfully!")
