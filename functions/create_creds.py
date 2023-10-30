import boto3
import os
import json
from datetime import datetime

def get_creds(REGION, event):
    sso = boto3.client('sso', region_name=REGION)

    try:
        sso_token = event['token']
        accounts = sso.list_accounts(accessToken=sso_token)
        for j, account in enumerate(accounts['accountList']):
            account_id = account['accountId']
            roles = sso.list_account_roles(
                accessToken = sso_token, 
                accountId = account_id
            )
            for l, role in enumerate(roles['roleList']):
                role_name = role['roleName']
                sts_creds = sso.get_role_credentials(
                    accessToken=sso_token,
                    roleName=role_name,
                    accountId=account_id
                )
                message = {}
                expiration = int(sts_creds['roleCredentials']['expiration']) / 1000
                message['account_id'] = account_id
                message['role_name'] = role_name
                message['expiration'] = datetime.utcfromtimestamp(expiration).strftime('%Y-%m-%d %H:%M:%S')
                message['access_key_id'] = sts_creds['roleCredentials']['accessKeyId']
                message['access_key_secret'] = sts_creds['roleCredentials']['secretAccessKey']
                message['session_token'] = sts_creds['roleCredentials']['sessionToken']
                send_to_queue(json.dumps(message), REGION)

    except Exception as e:
        print(f'ERROR: {e}')
        pass


def send_to_queue(message, REGION):
    sqs = boto3.client('sqs', region_name=REGION)
    queue_url = os.environ['QUEUEURL']

    try:
        send_message = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message
        )
        
    except Exception as e:
        print(f'ERROR: {e}')
        pass


def lambda_handler(event, context):
    REGION = os.environ['REGION']
    get_creds(REGION, event)
