import os
from random import choice

from chalice import Chalice
from slack import WebClient
from slack.errors import SlackApiError

app = Chalice(app_name='PositiveBot')

affirmations = []
affirm_file = os.path.join(
    os.path.dirname(__file__), 'chalicelib', 'affirmations.txt')
with open(affirm_file, "r") as affirm_file:
    affirmations += [_.rstrip("\n") for _ in affirm_file.readlines()]

slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
# Create a SlackClient for your bot to use for Web API requests
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(slack_bot_token)


@app.route('/')
def index():
    return {"message": "hello"}


@app.route('/slack/event', methods=["POST"])
def events():
    """
    Process slack event hooks
    Future ideas levenshtein distance, sentiment
    :return:
    """
    json_content = app.current_request.json_body
    if "challenge" in json_content:
        return {"challenge": app.current_request.json_body['challenge']}
    if "event" in app.current_request.json_body:
        print(app.current_request.json_body)
        event = app.current_request.json_body.get("event", {})
        print(event)
        event_type = event.get("type", None) if isinstance(event, dict) else None
        message = event.get("text", None) if isinstance(event, dict) else None
        if event_type and event_type == "message" and message and message.lower() == "positive":
            channel = event.get("channel", None)
            user = event.get("user", None)
            try:
                text = choice(affirmations)
                if channel:
                    response = client.chat_postMessage(
                        channel=channel,
                        text=text)
                    return {'message':text, "status": "ok"}
                elif user:
                    response = client.chat_postMessage(
                        user=user,
                        text=text)
                    return {'message':text, "status": "ok"}
                else:
                    return dict(
                        text=choice(affirmations))
            except SlackApiError as e:
                # Todo add Chalice Exception
                # You will get a SlackApiError if "ok" is False
                assert e.response["ok"] is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
                return {"error": f"Got an error {e.response['error']}"}
