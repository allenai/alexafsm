"""Interface to DynamoDB"""

import boto3


class DynamoDB:
    table = None

    def __init__(self, table_name: str = None):
        if not DynamoDB.table:
            assert table_name is not None, 'Using DynamoDB without initializing it!'
            DynamoDB.table = boto3.resource('dynamodb').Table(table_name)

    def register_new_user(self, user_id: str):
        DynamoDB.table.put_item(Item={
            'userId': user_id
        })

    def get_user_info(self, user_id: str) -> dict:
        return DynamoDB.table.get_item(Key={'userId': user_id}).get('Item')

    def set_user_info(self, user_id: str, **kwargs):
        DynamoDB.table.update_item(
            Key={
                'userId': user_id
            },
            UpdateExpression='SET ' + ', '.join([f'{k} = :{k}' for k in kwargs.keys()]),
            ExpressionAttributeValues=dict((':' + k, v) for k, v in DynamoDB.table.items())
        )
