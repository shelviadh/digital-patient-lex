import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_iam as iam
)
import uuid
from constructs import Construct

class DrLexResourcesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.scenario_table = dynamodb.Table(
            self, 
            "ScenarioTable",
            table_name=os.getenv("DDB_TABLE_NAME"),
            partition_key=dynamodb.Attribute(name="sid", type=dynamodb.AttributeType.NUMBER),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        insert_scenarios_to_ddb_lambda = lambda_.Function(
            self,
            "InsertScenariosFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("./lambda/sample_scenarios"),
            handler="seed_sample_scenarios.handler")

        insert_scenarios_to_ddb_lambda.add_environment("TABLE_NAME", self.scenario_table.table_name)
        self.scenario_table.grant_write_data(insert_scenarios_to_ddb_lambda)

        drlex_intent_function = lambda_.Function(
            self,
            "DrLexIntentFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("./lambda/lex_intent"),
            handler="lex_intent_function.handler")

        drlex_intent_function.add_environment("DDB_TABLE_NAME", os.getenv("DDB_TABLE_NAME"))
        self.scenario_table.grant_read_data(drlex_intent_function)

