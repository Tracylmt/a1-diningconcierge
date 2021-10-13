import json
import logging
import random
# I need requests to query in OpenSearch
# I upload a zip package of requests to AWS Lambda function environment
import requests
from requests.auth import HTTPBasicAuth
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# OpenSearch query info
opensearch_host = 'https://search-restaurants-zvk7jnqfg6krgykwbjskmtveiu.us-west-2.es.amazonaws.com'
index = 'restaurants'
opensearch_url = str(opensearch_host + '/' + index + '/' + '_search')
headers = {'Content-Type': "application/json", 'Accept': "application/json"}

# use request to query by area and cuisine in OpenSearch
def get_openSearch(cuisine, area):
    data = {
      "size": 20,
      "query": {
        "bool": { "should": [ 
           { "match": { "area": area } }, 
           { "match": { "cuisine": cuisine } } 
        ]}
      }
    }
    r = requests.get(opensearch_url, json=data, headers=headers, auth = HTTPBasicAuth('master', 'Master1!'))
    response_dict = json.loads(r.text)
    return response_dict['hits']['hits']

# use boto3 to get restaurant data from DynamoDB using id
def get_dynamoDB(rest_id):
    dynamodb = boto3.resource('dynamodb')
    yelp_table = dynamodb.Table('yelp-restaurants')
    response = yelp_table.query(KeyConditionExpression=Key('id').eq(rest_id))
    return response['Items'][0]

# return 3 random restaurant of user chosen cuisine and location
def getRandomRestaurant(info_dict):
    area = info_dict['area']
    cuisine = info_dict['cuisine']
    rest_dict = get_openSearch(cuisine, area)
    # pick 3 random restaurant from selected restaurant list
    rand = random.sample(range(1, len(rest_dict)), 3)
    recommand_list = []
    for randidx in rand:
        restaurant = get_dynamoDB(rest_dict[randidx]['_source']['id'])
        recommand_list.append(restaurant)
    
    return SNSmessage(info_dict, recommand_list)
        
# format SNS message
def SNSmessage(info_dict, recommand_list):
    area = info_dict['area']
    cuisine = info_dict['cuisine']
    peopleNum = info_dict['peopleNum']
    diningTime = info_dict['diningTime']
    phoneNum = info_dict['phoneNum']
    msg = "Dining Concierge-\nHello! Here are your " + area + " " + cuisine + " restaurant suggestions for " + peopleNum + " people, for " + diningTime + ": \n"
    for idx, restaurant in enumerate(recommand_list):
        msg += str(idx+1) + ". " + restaurant['name'] + " at " + restaurant['display_address'] + ". phone number: " \
            + restaurant['display_phone'] + ", rating: " + restaurant['rating'] + "; \n"
    msg += "Enjoy your meal!"
    return msg

# use boto3 to send sms message
def sendMessage(msg, phoneNum, recipient):
    client = boto3.client("sns")
    
    phone_num = ""
    #precoess phoneNum
    if len(phoneNum) == 10:
        phone_num = "+1" + phoneNum
    elif len(phoneNum) == 11 and phoneNum[0] == '1':
        phone_num = "+" + phoneNum
    elif len(phoneNum) == 12:
        phone_num = phoneNum
    else:
        logger.debug('Invalid Phone Number')
    
    logger.debug(phone_num)
    logger.debug(msg)
    
    # Send sms message.
    response1 = client.publish(
        PhoneNumber=phone_num,
        Message=msg
    )
    
    # codes added becaused SMS texting reach sandbox limit 
    # try send message to email
    CHARSET = "UTF-8"
    SENDER = "yl4632@columbia.edu"
    AWS_REGION = "us-west-2"
    SUBJECT = "Dining Conciege Bot Restaurant Suggestions"
    
    client = boto3.client('ses',region_name=AWS_REGION)
    response2 = client.send_email(
        Destination={
            'ToAddresses': [
                recipient,
            ],
        },
        Message={
            'Body': {
                'Text': {
                    'Charset': CHARSET,
                    'Data': msg,
                },
            },
            'Subject': {
                'Charset': CHARSET,
                'Data': SUBJECT,
            },
        },
        Source=SENDER
    )
    
    return response2

""" --- Main handler --- """

def lambda_handler(event, context):
    # triggered event is from Queue received message
    
    records = event['Records']
    for record in records:
        attributes = record['messageAttributes']

        info_dict = {'area': attributes['Area']['stringValue'],
                     'cuisine': attributes['Cuisine']['stringValue'],
                     'peopleNum': attributes['PeopleNum']['stringValue'],
                     'diningTime': attributes['DiningTime']['stringValue'],
                     'phoneNum': attributes['PhoneNum']['stringValue'], 
                     'email': attributes['Email']['stringValue'],
        }
    
        message = getRandomRestaurant(info_dict)
        logger.debug(message)
    
        response = sendMessage(message, info_dict['phoneNum'], info_dict['email'])
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
