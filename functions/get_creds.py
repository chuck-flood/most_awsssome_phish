import boto3
import json
import os

REGION = os.environ['REGION']
TABLE_NAME = os.environ['TABLENAME']

def dump_table():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    return table.scan()['Items']


def get_item(account_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    response = None
    response = table.get_item(Key={'account_id': account_id})['Item']
 
    return response


def lambda_handler(event, context):
    if event["queryStringParameters"] is not None:
        try:
            account_id = event["queryStringParameters"]['account_id']
            response = get_item(account_id)
            response = {
                'statusCode': 200,
                'body': json.dumps(response)
                }
        except:
            response = {
                'statusCode': 200,
                'body': 'Error: Incorrect Query String or Account ID not found.  Expected format account_id=<account_id>'
                }
    else:
        response = dump_table()
        response = {
            'statusCode': 200,
            'body': json.dumps(response)
            }

    return response