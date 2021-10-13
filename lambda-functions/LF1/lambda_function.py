import math
import dateutil.parser
import datetime
import time
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#reference some parts from tutorial code OrderFlowersCodeHook

#queue url variable
queue_url = "https://sqs.us-west-2.amazonaws.com/280871252988/DiningQueue"

""" --- Helper Functions --- """

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_dining_request(cityarea, cuisine, dinenum, date, time, phone, email):
    city_areas = ['manhattan', 'queens', 'brooklyn', 'bronx', 'staten island']
    cuisine_type = ['chinese', 'japanese', 'korean', 'thai', 'italian', 'mexican', 'american']
    if cityarea is not None and cityarea.lower() not in city_areas:
        return build_validation_result(False,
                                       'cityarea',
                                       'This is not a valid NYC borough. Please choose between Manhattan, Queens, Brooklyn, Bronx, Staten Island.')
    if cuisine is not None and cuisine.lower() not in cuisine_type:
        return build_validation_result(False,
                                       'cuisine',
                                       'We do not have {} cuisine, would you like to choose between Chinese, Japanese, Korean, Thai, '
                                       'Italian, Mexican, or American cuisine?'.format(cuisine))
    if dinenum is not None:
        dinenum = parse_int(dinenum)
        if math.isnan(dinenum) or dinenum <= 0:
            return build_validation_result(False, 
                                           'dinenum', 
                                           'Not a valid number, choose a integer number greater than 0.')
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'date', 'I did not understand that, what date would you like to dine?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'date', 'You should pick a date from tomorrow onwards. What day would you like to dine?')

    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'time', None)

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'time', None)

    if phone is not None:
        if len(phone) < 10 or (len(phone) == 11 and phone[0] != '1') or (len(phone) == 12 and (phone[0] != '+' or phone[1] != '1')) or len(phone) > 12:
            return build_validation_result(False, 'phone', 'Invalid number. Please choose a valid US phone number.')
    
    if email is not None:
        if '@' not in email:
            return build_validation_result(False, 'phone', 'Invalid email address. Please choose a valid email.')
            
    return build_validation_result(True, None, None)

"""  ----------send message to SQS ----------- """

def msg_attribute(intent_request):
    cityarea = get_slots(intent_request)["cityarea"]
    cuisine = get_slots(intent_request)["cuisine"]
    dinenum = get_slots(intent_request)["dinenum"]
    date = get_slots(intent_request)["date"]
    time = get_slots(intent_request)["time"]
    phone = get_slots(intent_request)["phone"]
    email = get_slots(intent_request)["email"]
    
    attribute = {
            'Area': {
                'DataType': 'String',
                'StringValue': cityarea
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': cuisine
            },
            'PeopleNum': {
                'DataType': 'Number',
                'StringValue': dinenum
            },
            'DiningTime': {
                'DataType': 'String',
                'StringValue': date + ' ' + time
            },
            'PhoneNum': {
                'DataType': 'Number',
                'StringValue': phone
            },
            'Email': {
                'DataType': 'String',
                'StringValue': email
            }
        }
    return attribute

# send Lex dining message to Queue
def send_msg(intent_request):
    sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=1,
        MessageAttributes=msg_attribute(intent_request),
        MessageBody=(
            'Information about restaurant suggestion.'
        )
    )
    return response['MessageId']

""" --- Functions that control the bot's behavior --- """

def dining_suggestion(intent_request):
    """
    Performs fulfillment for dining suggestion intent.
    """

    cityarea = get_slots(intent_request)["cityarea"]
    cuisine = get_slots(intent_request)["cuisine"]
    dinenum = get_slots(intent_request)["dinenum"]
    date = get_slots(intent_request)["date"]
    time = get_slots(intent_request)["time"]
    phone = get_slots(intent_request)["phone"]
    email = get_slots(intent_request)["email"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_dining_request(cityarea, cuisine, dinenum, date, time, phone, email)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
        
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        
        return delegate(output_session_attributes, get_slots(intent_request))
    
    #push to sms
    response = send_msg(intent_request)
    
    # fulfillment for dining suggestion
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'You are all set. Expect suggestions about {} cuisine in {} area shortly on your phone!'.format(cuisine, cityarea)})
                  
def greeting(intent_request):
    """
    Performs fulfillment for greeting intent.
    """
    
    # fulfillment for greeting
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Hi there, how can I help?'})

def thankyou(intent_request):
    """
    Performs fulfillment for thank you intent.
    """
    
    # fulfillment for thank you
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'You’re welcome.'})

""" --- Intents --- """

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggestion(intent_request)
    if intent_name == 'GreetingIntent':
        return greeting(intent_request)
    if intent_name == 'ThankYouIntent':
        return thankyou(intent_request)
    
    raise Exception('Intent with name ' + intent_name + ' not supported')

""" --- Main handler --- """

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    logger.debug(event)
    
    return dispatch(event)