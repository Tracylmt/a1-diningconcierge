import json
import boto3
import uuid

client = boto3.client('lex-runtime', region_name='us-west-2',aws_access_key_id = 'AKIAUCZJ3GP6LI7ZMHAR', aws_secret_access_key = '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')
# client = boto3.client('lex-runtime')
last_response = None

def lambda_handler(event, context):
    
    print("event:")
    print(event)
    print("context:")
    print(context)
    
    response = client.post_text(
        botName='DiningConcierger',
        botAlias='DiningBot',
        userId="qwert",
        inputText=event['messages'][0]['unstructured']['text'],
    )
    last_response = response
    
    # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # msg = {"id": event['id'], "text": response['message'], "timestamp": now}
    
    # return {
    #     'statusCode': 200,
    #     'headers': {
    #         'Access-Control-Allow-Headers': 'Content-Type',
    #         'Access-Control-Allow-Origin': '*',
    #         'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    #     },
    #     'body': json.dumps(event['messages'][0]['unstructured']['text'])
    # }
    
    return {
      "messages": [
        {
          "type": "unstructured",
          "unstructured": {
            # "text": json.dumps(response)
            "text": response['message']
          }
        }
      ]
    }
    
