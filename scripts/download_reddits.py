import datetime
import mimetypes
import os

from botocore.exceptions import ValidationError
import praw
from praw.models import Submission

# Create an app: https://www.reddit.com/prefs/apps
# Use http://localhost:8080 as redirect uri
from app import get_subscriptions_db

HOT_POSTS_PER_SUBREDDIT = 10
TOP_POSTS_PER_SUBREDDIT = 200
MINIMUM_VOTE_COUNT = 500

username = os.environ.get("REDDIT_USERNAME")
password = os.environ.get("REDDIT_PASSWORD")
client_id = os.environ.get("REDDIT_CLIENT_ID")
client_secret = os.environ.get("REDDIT_CLIENT_SECRET")

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=password,
                     user_agent='Reddit search data extractor by /u/' + username + '',
                     username=username)

image_subs = (
    'eyebleach',
    'wholesomegifs',
    'humansbeingbros',
    'animalsbeingbros',
    'mademesmile',
    'happycowgifs',
    'getmotivated'
)
news_subs = (
    'upliftingnews',
)

subs_to_dl = {
    'news': news_subs,
    'images': image_subs
}


# Subreddit examples
# for submission in reddit.subreddit("redditdev+learnpython").top("all"):
#     print(submission)
# for submission in reddit.subreddit("all").hot(limit=25):
#     print(submission.title)
#
#
# TYPE is of news, or images
# Feed hot, or all


def write_to_dynamo():
    db = get_subscriptions_db()
    seen_ids = set()
    seen_urls = set()
    for sub_type, subs in subs_to_dl.items():
        for sub in subs:
            for submission in reddit.subreddit(sub).hot(limit=HOT_POSTS_PER_SUBREDDIT):
                print(f"Processing {sub} hot")
                seen_post = submission.id in seen_ids or submission.url in seen_urls
                if submission.score < MINIMUM_VOTE_COUNT and not seen_post:
                    continue
                item = sub_to_item(submission, sub_type, "hot")
                print(item)
                seen_ids.add(submission.id)
                seen_urls.add(submission.url)
                try:
                    db.add_subscription(Item=item)
                except ValidationError as e:
                    continue
            # time_filter – Can be one of: all, day, hour, month, week, year (default: all).
            for time_filter in ('all', 'year', 'month', 'day'):
                print(f"Processing {sub} top {time_filter}")
                for submission in reddit.subreddit(sub).top(time_filter, limit=TOP_POSTS_PER_SUBREDDIT):
                    seen_post = submission.id in seen_ids or submission.url in seen_urls
                    if submission.score < MINIMUM_VOTE_COUNT and not seen_post:
                        continue
                    item = sub_to_item(submission, sub_type, f"top-{time_filter}")
                    print(item)
                    seen_ids.add(submission.id)
                    seen_urls.add(submission.url)
                    try:
                        db.add_subscription(Item=item)
                    except ValidationError as e:
                        continue


def is_url_image(url):
    mimetype, encoding = mimetypes.guess_type(url)
    return mimetype and mimetype.startswith('image')


def sub_to_item(submission: Submission, sub_type: str, feed: str) -> dict:
    url_image = is_url_image(submission.url)
    preview = None
    if hasattr(submission, 'preview'):
        images = submission.preview.get('images')
        if images:
            source = images[0].get('source')
            preview = source.get('url')
    return {"ID": submission.id,
            "Title": submission.title,
            "Score": submission.score,
            "Url": submission.url,
            "Domain": submission.domain,
            "Permalink": submission.permalink,
            "Subreddit": str(submission.subreddit),
            "CreatedDate": datetime.datetime.utcfromtimestamp(submission.created).strftime('%Y-%m-%d'),
            "Category": sub_type,
            "Feed": feed,
            "IsImage": True if url_image else False,
            "IsVideo": submission.is_video,
            "IsGif": submission.url.endswith("gif") or 'gfycat' in submission.url or submission.url.endswith("gifv"),
            "Preview": preview
            }


if __name__ == '__main__':
    write_to_dynamo()
