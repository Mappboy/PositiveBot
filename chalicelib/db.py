from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError


class DynamoDBTeam(object):
    def __init__(self, table_resource):
        self._table = table_resource

    def add_team(self, team_id, name, access_token):
        response = self._table.put_item(Item={
            "team_id": team_id,
            "name": name,
            "access_token": access_token
        })
        return response

    def get_team(self, team_id):
        try:
            response = self._table.get_item(Key={'team_id': team_id})
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response.get('Item')

    def delete_team(self, team_id):
        pass

    def update_team(self, team_id, name, access_token):
        response = self.get_team(team_id)
        item = response['Item']

        # update
        item['name'] = name
        item['access_token'] = access_token

        # put (idempotent)
        response = self._table.put_item(Item=item)
        return response


class DynamoDBSubscription(object):
    def __init__(self, table_resource):
        self._table = table_resource

    def _add_to_filter_expression(self, expression, condition):
        if expression is None:
            return condition
        return expression & condition

    def add_subscription(self, Item: dict):
        assert "ID" in Item
        assert "Url" in Item
        assert "Category" in Item
        response = self._table.put_item(Item=Item)
        return response

    def get_subscriptions(self, ID: str):
        try:
            response = self._table.get_item(
                Key={
                    'ID': ID,
                },
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response.get('Item')

    def list_subscriptions(self, category=None, feed=None, is_image=None, is_gif=None, is_video=None, latest=None):
        scan_params = {}
        filter_expression = None
        if category is not None:
            filter_expression = self._add_to_filter_expression(
                filter_expression, Attr('Category').begins_with(category)
            )
        if feed is not None:
            filter_expression = self._add_to_filter_expression(
                filter_expression, Attr('Feed').eq(feed)
            )
        if is_image is not None:
            filter_expression = self._add_to_filter_expression(
                filter_expression, Attr('IsImage').eq(is_image)
            )
        if is_gif is not None:
            filter_expression = self._add_to_filter_expression(
                filter_expression, Attr('IsImage').eq(is_gif)
            )
        if is_video is not None:
            filter_expression = self._add_to_filter_expression(
                filter_expression, Attr('ISVideo').eq(is_video)
            )
        if filter_expression:
            scan_params['FilterExpression'] = filter_expression
        response = self._table.scan(**scan_params)
        return response.get('Items')
