"""
Positive Bot Slack Code
TODO:
    - We should use message queues so we can send acknowledge reciepts to Slack and not get timeouts
    - Add feedback button to remove from db
    - Validate token see https://api.slack.com/interactivity/slash-commands
    - Add submit type
    - Add quotes
    - Add update subreddits function
    - Add GetMotivated sub
"""
import json
import logging
import os
from random import choice
from urllib.parse import parse_qs

import boto3
import requests
from chalice import Chalice
from chalice.app import SQSEvent, Response
from slack import WebClient
from slack.errors import SlackApiError

from chalicelib import db
from chalicelib.util import image_slack_block, news_slack_block

app = Chalice(app_name='PositiveBot')
app.log.setLevel(logging.INFO)

slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]

_TEAM_DB = None
_SUB_DB = None
_SUBS_QUEUE = None
_EVENTS_QUEUE = None


def get_team_db():
    global _TEAM_DB
    if _TEAM_DB is None:
        _TEAM_DB = db.DynamoDBTeam(
            boto3.resource('dynamodb').Table(
                os.environ['TEAM_TABLE_NAME'])
        )
    return _TEAM_DB


def get_subscriptions_db():
    global _SUB_DB
    if _SUB_DB is None:
        _SUB_DB = db.DynamoDBSubscription(
            boto3.resource('dynamodb').Table(
                os.environ['SUBSCRIPTIONS_TABLE_NAME'])
        )
    return _SUB_DB


def get_events_queue(sqs=None):
    global _EVENTS_QUEUE
    if _EVENTS_QUEUE is None:
        if sqs is None:
            sqs = boto3.resource('sqs')
        _QUEUE = sqs.get_queue_by_name(QueueName=os.environ['EVENTS_QUEUE_NAME'])
    return _EVENTS_QUEUE


def get_subscriptions_queue(sqs=None):
    global _SUBS_QUEUE
    if _SUBS_QUEUE is None:
        if sqs is None:
            sqs = boto3.resource('sqs')
        _SUBS_QUEUE = sqs.get_queue_by_name(QueueName=os.environ['SUBSCRIPTIONS_QUEUE_NAME'])
    return _SUBS_QUEUE


@app.route('/')
def index():
    return {"message": "hello"}


@app.on_sqs_message(queue=os.environ['SUBSCRIPTIONS_QUEUE_NAME'])
def subscriptions_handler(event: SQSEvent):
    for message in event:
        app.log.info("Message: %s", message.to_dict())
        message_body = json.loads(message.body)
        app.log.info(message_body.get("command"))
        handle_news(message_body)

    app.log.info("Event: %s", event.to_dict())


def handle_news(message: dict):
    app.log.info("Handling news message")
    latest_news = message.get("text") == "latest"
    if latest_news:
        news = get_subscriptions_db().list_subscriptions(category='news', latest=latest_news)
        # Drop latest
        if not news:
            news = get_subscriptions_db().list_subscriptions(category='news')
    else:
        news = get_subscriptions_db().list_subscriptions(category='news')
    if not news:
        return {"response_type": "ephemeral",
                "text": "Oops I broke"}
    slack_block = news_slack_block(choice(news))
    app.log.info(slack_block)
    response_url = message.get("response_url")[0]
    try:
        resp = requests.post(url=response_url, json=slack_block)
        if not resp.ok:
            app.log.error(f"Failed to post message {response_url} {slack_block} ")
        else:
            app.log.info(f"Sent message {response_url} {slack_block} ")
    except Exception as e:
        app.log.error(f"Unexpected error {e}")


@app.route('/news', methods=["GET", "POST"],
           content_types=['application/x-www-form-urlencoded'])
def get_news():
    """
    Takes in latest or random from text
    :return:
    """
    try:
        parsed = parse_qs(app.current_request.raw_body.decode())
        response = get_subscriptions_queue().send_message(
            MessageBody=json.dumps(parsed))
        if response:
            app.log.info("Message sent to queue: %s" % response)
            return Response(body='',
                            status_code=200,
                            headers={'Content-Type': 'text/plain'})
    except Exception as e:
        app.log.error(e)
        return {"text": "Something has gone wrong with the service"}


@app.route('/images', methods=["GET", "POST"],
           content_types=['application/x-www-form-urlencoded'])
def get_images():
    images = get_subscriptions_db().list_subscriptions(category='images', is_image=True)
    if not images:
        return {"response_type": "ephemeral",
                "text": "Oops I broke"}
    slack_block = image_slack_block(choice(images))
    app.log.info(slack_block)
    return slack_block


@app.route('/gifs', methods=["GET", "POST"],
           content_types=['application/x-www-form-urlencoded'])
def get_gifs():
    gifs = get_subscriptions_db().list_subscriptions(category='images', is_gif=True)
    if not gifs:
        return {"response_type": "ephemeral",
                "text": "Oops I broke"}
    return image_slack_block(choice(gifs))


@app.route('/videos', methods=["GET", "POST"], content_types=['application/x-www-form-urlencoded'])
def get_videos():
    videos = get_subscriptions_db().list_subscriptions(category='images', is_video=True)
    if not videos:
        return {"response_type": "ephemeral",
                "text": "Oops I broke"}
    return image_slack_block(choice(videos))


@app.route('/slack/event', methods=["POST"])
def events():
    """
    Process slack event hooks
    Future ideas levenshtein distance, sentiment
    :return:
    """
    # We should just submit for processing to sqs
    if app.current_request.headers.get('x-slack-retry-num'):
        return {'message': 'ok'}
    json_content = app.current_request.json_body
    if "challenge" in json_content:
        return {"challenge": app.current_request.json_body['challenge']}
    if "event" in app.current_request.json_body:
        team_id = app.current_request.json_body["authorizations"][0]["team_id"]
        team_access_token = get_team_db().get_team(team_id).get("access_token")
        # Fallback
        client = WebClient(team_access_token) if team_access_token else WebClient(slack_bot_token)
        app.log.info(app.current_request.json_body)
        event = app.current_request.json_body.get("event", {})
        event_type = event.get("type", None) if isinstance(event, dict) else None
        message = event.get("text", None) if isinstance(event, dict) else None
        if event_type and event_type == "message" and message and message.lower() == "positive":
            # Todo this should be it's own function
            # Only load affirmations if we need them
            affirmations = []
            affirm_file = os.path.join(
                os.path.dirname(__file__), 'chalicelib', 'affirmations.txt')
            with open(affirm_file, "r") as affirm_file:
                affirmations += [_.rstrip("\n") for _ in affirm_file.readlines()]

            channel = event.get("channel", None)
            channel_type = event.get("channel_type", None)
            user = event.get("user", None)
            text = choice(affirmations)
            # refactor this to remove repeated code
            if channel and channel_type != "im":
                try:
                    app.log.info(f"Channel = {channel}")
                    response = client.chat_postMessage(
                        channel=channel,
                        text=text)
                    return {'message': text, "status": "ok"}
                except SlackApiError as e:
                    if e.response["error"] == 'channel_not_found':
                        response = client.chat_postMessage(
                            channel=user,
                            text=text)
                        return {'message': text, "status": "ok"}
                    else:
                        app.log.info(f"Unknown error {e.response['error']}")
                        return {'message': text, "status": "ok"}
            else:
                try:
                    resp = client.conversations_open(user=user)
                    app.log.info(f"resp = {resp}")
                    response = client.chat_postMessage(
                        channel=resp.get("channel"),
                        text=text)
                    return {'message': text, "status": "ok"}
                except SlackApiError as e:
                    if e.response["error"] == 'channel_not_found':
                        response = client.chat_postMessage(
                            channel=user,
                            text=text)
                        return {'message': text, "status": "ok"}
                    else:
                        app.log.info(f"Unknown error {e.response['error']}")
                return {'message': text, "status": "ok"}
        return {"message": "Nothing to respond", "status": "ok"}


@app.route("/slack/oauth_redirect", methods=["GET"])
def post_install():
    # Verify the "state" parameter
    state_param = app.current_request.query_params.get('state')
    # Retrieve the auth code from the request params
    code_param = app.current_request.query_params.get('code')

    # An empty string is a valid token for this request
    client = WebClient()

    # Request the auth tokens from Slack
    response = client.oauth_v2_access(
        client_id=client_id,
        client_secret=client_secret,
        code=code_param
    )
    # Save the bot token to an environmental variable or to your data store
    # for later use
    team = response.get("team")
    team_id = team.get("id")
    team_name = team.get("name")
    access_token = response.get("access_token")
    if not all([team_id, team_name, access_token]):
        app.log.info(response)
        return {"Missing value in response": response}
    if get_team_db().get_team(team_id):
        get_team_db().update_team(team_id, team_name, access_token)
    else:
        get_team_db().add_team(team_id, team_name, access_token)
    # Don't forget to let the user know that OAuth has succeeded!
    return {"message": "Installation is completed!"}
