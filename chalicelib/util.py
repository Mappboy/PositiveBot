import datetime


def image_slack_block(image_input: dict):
    """
    Returns an image or gif response
    See     https://app.slack.com/block-kit-builder/ for help building response
    :return: Slack Block for Random Image
    """
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": image_input.get("Title"),
                    "emoji": True
                }
            },
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": image_input.get("ID"),
                    "emoji": True
                },
                "image_url": image_input.get("Url"),
                "alt_text": "marg"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Image from <https://reddit.com/r/{image_input.get('Subreddit')}|/r/{image_input.get('Subreddit')}>"
                    },
                ]
            }
        ]
    }


def news_slack_block(news_input):
    """
    Returns news slack bot
    :return:
    """
    block = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{news_input.get('Title')}\n {news_input.get('Url')}",
                }
            }
        ]
    }
    if news_input.get("Preview"):
        block["blocks"][0].update({"accessory": {
                        "type": "image",
                        "image_url": news_input.get("Preview"),
                        "alt_text": news_input.get("ID")
                    }})
    return block


def one_week_ago_iso():
    tod = datetime.datetime.now()
    d = datetime.timedelta(days=7)
    a = tod - d
    return a.isoformat().split("T")[0]
