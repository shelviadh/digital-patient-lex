import os
import json
import boto3
import random
from datetime import datetime, timedelta
import time

dynamodb = boto3.resource('dynamodb')
runtime = boto3.client("sagemaker-runtime")
logs_client = boto3.client('logs')
enable_debug_mode = True
DDB_TABLE_NAME = os.environ['DDB_TABLE_NAME']


def handler(event, context):
    """
    lambda_handler is our entrypoint function when our lambda function is called

    :param event: This is the invocation event object
    :param context: This is the invocation context object.
    :return: returns a response to Lex.
    """

    #Handle debug mode
    if(enable_debug_mode):
        print("Debug mode is enabled, I will be very verbose!")
        print(event)
    
    # Determine the intent name we're working with
    intent_name = event['sessionState']['intent']['name']

    # GetScenario (Greeting the patient to select a scenario)
    if(intent_name == "GetScenario"):
        scenarioId = random.randint(0, 2)
        
        if (enable_debug_mode):
            print(f"Running scenario number {scenarioId}")
        
        sobj = get_scenario_by_id(scenarioId)
        return response_builder(intent_name, sobj["problem"], scenarioId)
        
    if("scenarioId" not in event["sessionState"]["sessionAttributes"] or 
        event["sessionState"]["sessionAttributes"]["scenarioId"] == "-1"):
        
        if (intent_name == "FallbackIntent"):
            fallback_to_uneeq_instruction = '{"instructions": {"personalityEngine": {"enabled": true}}'
            return response_builder(intent_name, "Hmm let me think", contentType="CustomPayload", instructions=fallback_to_uneeq_instruction, sid=-1)    
    

    scenarioId = event["sessionState"]["sessionAttributes"]["scenarioId"]
    sobj = get_scenario_by_id(scenarioId)
    
    if(intent_name == "DoesItHurt"):
        if(enable_debug_mode):
            print("Running does it hurt")
        
        patient_response_to_doctor = sobj["pain"]
        
    if(intent_name == "IsItBleeding"):
        if(enable_debug_mode):
            print("Running are you bleeding")
        
        patient_response_to_doctor = sobj["bleeding"]
        
    if(intent_name == "WhichBodyPart"):
        if(enable_debug_mode):
            print("Running which body part")
        
        patient_response_to_doctor = sobj["bodypart"]
        
    if(intent_name == "HowOften"):
        if(enable_debug_mode):
            print("Running how often does this happen")
        
        patient_response_to_doctor = sobj["frequency"]
        
    if(intent_name == "WhatHappened"):
        if(enable_debug_mode):
            print("Running what happened")
        
        patient_response_to_doctor = sobj["cause"]
        
    if(intent_name == "SummarizeConvo"):
        if(enable_debug_mode):
            print("Summarizing whole conversation with AI model")
        
        patient_response_to_doctor = summarize_convo(event)
        print(f"Summary: {patient_response_to_doctor}")
        
    if(intent_name == "DoctorAnswers"):
        if(enable_debug_mode):
            print("User is answering patient")
        
        patient_response_to_doctor = "Alright, thank you"
            
    return response_builder(intent_name, patient_response_to_doctor, scenarioId)
    
    
def get_scenario_by_id(sid):
    table = dynamodb.Table(DDB_TABLE_NAME)      
    
    # we use 'get_item' to fetch an item from our table by it's "hash key"
    response = table.get_item(
        Key={
            'sid': int(sid)
        }
    )
    
    if "Item" in response:
        return response["Item"]
    else:
        return None
    
def response_builder(intent_name, response_msg, contentType="PlainText", instructions="", sid = -1):
    
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
                    "contentType": contentType,
                    "content": response_msg
                }
            ]
        }
    
    # if (intent_name == "FallbackIntent"):
    #     r["messages"][0]["content"] = {
    #         "instructions": {
    #             "personalityEngine": {
    #                 "enabled": "true"
    #             }
    #         }
    #     }
    # return our built response to the caller.
    print(f"Response: {r}")
    return r

def summarize_convo(event):
    sessionId = event["sessionId"]
    print(f"Summarize for sessionId: {sessionId}")
    query = f'''fields inputTranscript, messages.0.content as botReply, sessionId 
                | filter sessionId = '{sessionId}'
                | sort sessionId, @timestamp asc
                | limit 30'''
                
    print(f"CloudWatch Query: {query}")
    log_group = '/aws/lexv2/prod'

    start_query_response = logs_client.start_query(
        logGroupName=log_group,
        startTime=int((datetime.today() - timedelta(hours=3)).timestamp()),
        endTime=int(datetime.now().timestamp()),
        queryString=query,
    )

    query_id = start_query_response['queryId']
    log_response = None

    while log_response == None or log_response['status'] == 'Running':
        print('Waiting for query to complete ...')
        time.sleep(1)
        log_response = logs_client.get_query_results(
            queryId=query_id
        )
        
    
    print(log_response)
    if len(log_response["results"]) == 0:
        return "Summary not yet available, please try again in a few mins!"
    
    all_transcript = log_response["results"]
    conversation_transcript = []
    for transcript in all_transcript:
        if transcript[0]["field"] == "inputTranscript" and transcript[0]["value"] != "summarize":
            doctorText = transcript[0]["value"]
        else:
            doctorText=""
            patientText=""
            continue
        
        if transcript[1]["field"] == "botReply":
            patientText = transcript[1]["value"]
        else:
            patientText = ""
            
        conversation_transcript.append(f"doctor: {doctorText}")
        conversation_transcript.append(f"patient: {patientText}")
        
    conversation_transcript_text = "\n".join(conversation_transcript)
    print(f"whole convo: {conversation_transcript_text}")
    json_transcript = {"inputs": conversation_transcript_text}

    endpoint_name = "jumpstart-example-huggingface-summariza-2023-02-20-11-23-43-560"
    content_type = "application/x-text"
    payload = json.dumps(json_transcript).encode('utf-8')
    
    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType=content_type,
        Body=payload
    )
    
    result = json.loads(response['Body'].read())
    return result["summary_text"]