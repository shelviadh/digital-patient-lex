from __future__ import print_function

import json
import decimal
import os
import boto3

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


# Get the service resource.
dynamodb = boto3.resource('dynamodb')

# set environment variable
TABLE_NAME = os.environ['TABLE_NAME']

def handler(event, context):
    scenarios_to_ddb = []
    table = dynamodb.Table(TABLE_NAME)
    
    with open('sample_scenarios.json', 'r') as json_file:
        sample_scenarios_data = json.load(json_file)
        for scenario in sample_scenarios_data:
            scenarios_to_ddb.append(scenario)
        
    with table.batch_writer() as batch:
        for scenario in scenarios_to_ddb:
            batch.put_item(Item=scenario)
            print("PutItem succeeded:")
            print(json.dumps(scenario, indent=4, cls=DecimalEncoder))
    
    return {
        'statusCode': 200,
    }