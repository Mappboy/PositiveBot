import datetime
import os

import boto3
import praw

# Create an app: https://www.reddit.com/prefs/apps
# Use http://localhost:8080 as redirect uri


POSTS_PER_SUBREDDIT = 100
MINIMUM_VOTE_COUNT = 200

username = os.environ.get("REDDIT_USERNAME")
password = os.environ.get("REDDIT_PASSWORD")
client_id = os.environ.get("REDDIT_CLIENT_ID")
client_secret = os.environ.get("REDDIT_CLIENT_SECRET")

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=password,
                     user_agent='Reddit search data extractor by /u/' + username + '',
                     username=username)

print("Authentication for " + str(reddit.user.me()) + " is verified. Proceeding.\r\n")

image_subs = (
    'wholesomememes',
    'eyebleach',
    'wholesomegifs',
    'humansbeingbros',
    'animalsbeingbros',
    'mademesmile',
    'happycowgifs'
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


def create_subscriptions_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.create_table(
        TableName='Subscriptions',
        KeySchema=[
            {
                'AttributeName': 'ID',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'CreatedDate',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'ID',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'CreatedDate',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table


def write_to_dynamo(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Subscriptions')
    for sub_type, sub in subs_to_dl.items():
        for submission in reddit.subreddit(sub).hot(25):
            table.put_item(Item=sub_to_item(submission, sub_type, "hot"))
        for submission in reddit.subreddit(sub).top(POSTS_PER_SUBREDDIT):
            table.put_item(Item=sub_to_item(submission, sub_type, "top"))


def sub_to_item(submission, sub_type: str, feed: str) -> dict:
    return {"ID": submission.id,
            "Title": submission.title,
            "Score": submission.score,
            "Url": submission.url,
            "Domain": submission.domain,
            "Permalink": submission.permalink,
            "Subreddit": submission.subreddit,
            "CreatedDate": datetime.datetime.utcfromtimestamp(submission.created).strftime('%m-%d-%Y'),
            "Category": sub_type,
            "Feed": feed
            }


"""
https://app.slack.com/block-kit-builder/T013V2CJC9E#%7B%22blocks%22:%5B%7B%22type%22:%22header%22,%22text%22:%7B%22type%22:%22plain_text%22,%22text%22:%22This%20is%20a%20header%20block%22,%22emoji%22:true%7D%7D,%7B%22type%22:%22image%22,%22title%22:%7B%22type%22:%22plain_text%22,%22text%22:%22I%20Need%20a%20Marg%22,%22emoji%22:true%7D,%22image_url%22:%22https://assets3.thrillist.com/v1/image/1682388/size/tl-horizontal_main.jpg%22,%22alt_text%22:%22marg%22%7D,%7B%22type%22:%22context%22,%22elements%22:%5B%7B%22type%22:%22mrkdwn%22,%22text%22:%22*This*%20is%20:smile:%20markdown%22%7D,%7B%22type%22:%22image%22,%22image_url%22:%22https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg%22,%22alt_text%22:%22cute%20cat%22%7D,%7B%22type%22:%22image%22,%22image_url%22:%22https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg%22,%22alt_text%22:%22cute%20cat%22%7D,%7B%22type%22:%22image%22,%22image_url%22:%22https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg%22,%22alt_text%22:%22cute%20cat%22%7D,%7B%22type%22:%22plain_text%22,%22text%22:%22Author:%20K%20A%20Applegate%22,%22emoji%22:true%7D%5D%7D,%7B%22type%22:%22section%22,%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22This%20is%20a%20section%20block%20with%20a%20button.%22%7D,%22accessory%22:%7B%22type%22:%22button%22,%22text%22:%7B%22type%22:%22plain_text%22,%22text%22:%22Click%20Me%22,%22emoji%22:true%7D,%22value%22:%22click_me_123%22,%22url%22:%22https://google.com%22,%22action_id%22:%22button-action%22%7D%7D%5D%7D
{
	"blocks": [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "A message *with some bold text* and _some italicized text_."
			}
		},
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "This is a header block",
				"emoji": true
			}
		},
		{
			"type": "image",
			"title": {
				"type": "plain_text",
				"text": "I Need a Marg",
				"emoji": true
			},
			"image_url": "https://assets3.thrillist.com/v1/image/1682388/size/tl-horizontal_main.jpg",
			"alt_text": "marg"
		},
		{
			"type": "context",
			"elements": [
				{
					"type": "mrkdwn",
					"text": "*This* is :smile: markdown"
				},
				{
					"type": "image",
					"image_url": "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg",
					"alt_text": "cute cat"
				},
				{
					"type": "image",
					"image_url": "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg",
					"alt_text": "cute cat"
				},
				{
					"type": "image",
					"image_url": "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg",
					"alt_text": "cute cat"
				},
				{
					"type": "plain_text",
					"text": "Author: K A Applegate",
					"emoji": true
				}
			]
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "This is a section block with a button."
			},
			"accessory": {
				"type": "button",
				"text": {
					"type": "plain_text",
					"text": "Click Me",
					"emoji": true
				},
				"value": "click_me_123",
				"url": "https://google.com",
				"action_id": "button-action"
			}
		}
	]
}"""
