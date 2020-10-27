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
                        "text": f"Image from <www.reddit.com/r/{image_input.get('Subreddit')}|/r/{image_input.get('Subreddit')}>"
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
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": news_input.get("Title"),
                    "emoji": True
                }
            },
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": news_input.get("ID"),
                    "emoji": True
                },
                "image_url": news_input.get("Preview"),
                "alt_text": "marg"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Image from <www.reddit.com/r/{news_input.get('Subreddit')}|/r/{news_input.get('Subreddit')}>"
                    },
                ]
            }
        ]
    }
