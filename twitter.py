import tweepy

# Twitter API credentials (hardcoded)
API_KEY = "sJN9Wy9v1iuNtySk3x3t1DMNG"
API_KEY_SECRET = "789S0gXymhV1jDEwyWlCMN3wVm26RvKNt4UAZE91dzPAjHvwKF"
ACCESS_TOKEN = "163796356-uNbQl5sXqsvM9NdISQzHLLreFEQb0yyb1zr2AT2B"
ACCESS_TOKEN_SECRET = "NYGAB9gR2yAHXcgdNqQfBZsWJ6shb7fZXAiTAcBvGCuPx"

# Authenticate to Twitter using OAuth1
auth = tweepy.OAuth1UserHandler(API_KEY, API_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# Tweet text and image URL
status_text = "Check out this cool image! #example"
image_url = "https://example.com/your-image.jpg"  # Replace this with your actual image URL

# Function to post the tweet with an image link
def post_tweet_with_image_link(status, image_link):
    try:
        # Posting the tweet
        api.update_status(status=f"{status} {image_link}")
        print("Successfully posted the tweet!")
    except tweepy.TweepError as e:
        print(f"Error posting tweet: {e}")

# Post the tweet
post_tweet_with_image_link(status_text, image_url)
