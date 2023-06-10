import os
import boto3
import random

dynamodb = boto3.resource('dynamodb')
enable_debug_mode = True
DDB_TABLE_NAME = os.environ['DDB_TABLE_NAME']


def handler(event, context):
    """
    lambda_handler is our entrypoint function when our lambda function is called

    :param event: This is the invocation event object
    :param context: This is the invocation context object.
    :return: returns a response to Lex.
    """
    #
    #
    #Handle debug mode
    if(enable_debug_mode):
        print("Debug mode is enabled, I will be very verbose!")
        print(event)
    
    #
    #
    # Determine the intent name we're working with
    intent_name = event['sessionState']['intent']['name']
    
    #
    # ****
    # Let's find out what "intent" we're working with at the moment.
    # ****
    #
    
    #
    # 
    # GetScenario (Greeting the patient to select a scenario)
    if(intent_name == "GetScenario"):
        #
        # We're going to select a random number which will be the scenario we 
        # load.
        scenarioId = random.randint(0, 2)
        
        #
        # Echo that out to logging if debugging is enabled.
        if (enable_debug_mode):
            print(f"Running scenario number {scenarioId}")
        
        #
        # fetch the scenario from DynamoDB
        sobj = get_scenario_by_id(scenarioId)

        #
        # build a response object and return it to Lex.
        return response_builder(intent_name, sobj["problem"], scenarioId)
        
    #
    #
    # If we're not working with the intent "GetScenario" and we don't have a 
    # scenarioId set in our Amazon Lex session state, then this means our 
    # doctor has asked about the patient's symptoms before greeting them (selecting
    # a scenario). So let's prompt them to interact with the "GetScenario" intent
    # first.
    if("scenarioId" not in event["sessionState"]["sessionAttributes"] or 
        event["sessionState"]["sessionAttributes"]["scenarioId"] == "-1"):
        return response_builder(intent_name, "You're all business hu? How about asking me generally \"What seems to be the problem?\" first?", -1)    
    
    
    #
    #
    # Now that we know we have a scenario ID, let's get that scenario ready.
    scenarioId = event["sessionState"]["sessionAttributes"]["scenarioId"]
    sobj = get_scenario_by_id(scenarioId)
    
    #
    #
    # Let's initialise a variable to store our response from the patient to the doctor.
    patient_response_to_doctor = "Sorry, I don't understand. Can you ask that differently?"
    
    #
    #
    # Handle the doctor's question of "does it hurt?"
    if(intent_name == "DoesItHurt"):
        if(enable_debug_mode):
            print("Running does it hurt")
        
        patient_response_to_doctor = sobj["pain"]
        
    #
    #
    # Handle the doctor's question of "are you bleeding?"
    if(intent_name == "IsItBleeding"):
        if(enable_debug_mode):
            print("Running are you bleeding")
        
        patient_response_to_doctor = sobj["bleeding"]
        
    #
    #
    # Handle the doctor's question of "Where are you hurt?"
    if(intent_name == "WhichBodyPart"):
        if(enable_debug_mode):
            print("Running which body part")
        
        patient_response_to_doctor = sobj["bodypart"]
        
    #
    #
    # Handle the doctor's question of "how often does this occur?"
    if(intent_name == "HowOften"):
        if(enable_debug_mode):
            print("Running how often does this happen")
        
        patient_response_to_doctor = sobj["frequency"]
        
    #
    #
    # Handle the doctor's question of "what happened?"
    if(intent_name == "WhatHappened"):
        if(enable_debug_mode):
            print("Running what happened")
        
        patient_response_to_doctor = sobj["cause"]
            
    
    #
    #
    # Now we have everything we need to respond to the doctor via Lex.
    return response_builder(intent_name, patient_response_to_doctor, scenarioId)
    
    
def get_scenario_by_id(sid):
    """
    get_scenario_by_id fetches our scenario from DynamoDB

    :param sid: This is the ID of the Scenario that you are running currently
    :return: returns the Scenario object requested or a None object if the scenario is not found.
    """
    
    # Now we're going to grab our table resource for querying against
    table = dynamodb.Table(DDB_TABLE_NAME)      
    
    # we use 'get_item' to fetch an item from our table by it's "hash key"
    response = table.get_item(
        Key={
            'sid': int(sid)
        }
    )
    
    # If our response object contains a property called "Item", then it means 
    # we successfully found the item we are looking for. If not, it's typical 
    # to return a "None" object for the caller to handle, indicating we cannot
    # find the item in the database.
    if "Item" in response:
        return response["Item"]
    else:
        return None
    
def response_builder(intent_name, response_msg, sid = -1):
    """
    response_builder helps you quickly build a basic but valid response for 
    Amazon Lex to consume.

    :param intent_name: This is the name of the intent in scope.
    :param response_msg: This is the message you want Lex to read back to the customer
    :param sid: This is the ID of the Scenario that you are running currently, -1 by default.

    :return:
    """
    
    # Below is a minimal JSON response object for Amazon Lex.
    r = {
            "sessionState": {
                "sessionAttributes": {
                    "scenarioId": f"{sid}"
                },
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "confirmationState": "Confirmed",
                    "name": intent_name,
                    "state": "Fulfilled"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": response_msg
                }
            ]
        }
        
    # return our built response to the caller.
    return r
