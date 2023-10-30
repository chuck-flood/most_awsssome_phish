import boto3
import botocore
from os import environ

class OutputNotFoundException(Exception):
  pass


def check_token(sso_oidc_client, oidc_application, device_code):
    try:
        print( oidc_application, device_code)
        token_response = sso_oidc_client.create_token(
        clientId=oidc_application[0],
        clientSecret=oidc_application[1],
        grantType="urn:ietf:params:oauth:grant-type:device_code",
        deviceCode=device_code
        )
        aws_sso_token = token_response.get('accessToken')
        return aws_sso_token
    except botocore.exceptions.ClientError as e:
        print(f'No Token Found Error: {e}')
        raise OutputNotFoundException(e)


def lambda_handler(event, context):
    sso_oidc_client = boto3.client('sso-oidc', region_name=environ['REGION'])
    print(event)    
    if event['sessionCaptured'] is False:
        oicd_app = event['oidc_app']
        device_code_app = event['deviceCode']
        token = check_token(sso_oidc_client, oicd_app, device_code_app)
        if token: 
            event['token'] = token
            event['sessionCaptured'] = True
            
            return event