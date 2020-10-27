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


def news_slack_block():
    """
    Returns news slack bot
    :return:
    """
    {'IsVideo': False, 'Score': Decimal('41872'),
     'Preview': 'https://preview.redd.it/kmghmhqgk8e31.jpg?auto=webp&s=bd61c05e116c41ed9ced1caa268860fdc541a45f',
     'IsImage': True, 'Url': 'https://i.redd.it/kmghmhqgk8e31.jpg', 'Feed': 'top-all', 'Title': 'Such a bro',
     'Subreddit': 'AnimalsBeingBros', 'CreatedDate': '08-03-2019', 'IsGif': False,
     'Permalink': '/r/AnimalsBeingBros/comments/clis1c/such_a_bro/', 'Domain': 'i.redd.it', 'ID': 'clis1c',
     'Category': 'images'}
    pass
