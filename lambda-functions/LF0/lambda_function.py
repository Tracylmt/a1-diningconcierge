import json
import boto3
import uuid

# use access key and secret key to achieve cross-account connection to Lex Bot
# Cannot provide this information in the submission
client = boto3.client('lex-runtime', region_name='us-west-2',aws_access_key_id = '********', aws_secret_access_key = '***************')
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
    
