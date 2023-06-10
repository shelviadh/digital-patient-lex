from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_lex as lex,
    aws_lambda as lambda_,
    aws_dynamodb as ddb
)
import uuid
import os
from constructs import Construct

class DrlexCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        CUSTOM_SUFFIX_SLR = str(uuid.uuid1())[:8]
        lex_service_linked_role = iam.CfnServiceLinkedRole(
            self,
            "DrLexServiceLinkedRole",
            aws_service_name="lexv2.amazonaws.com",
            custom_suffix=CUSTOM_SUFFIX_SLR
        )

        print("ACCOUNT ID FROM STACK: {}", Stack.of(self).account)
        lex_service_linked_role_arn = "arn:aws:iam::{}:role/aws-service-role/lexv2.amazonaws.com/AWSServiceRoleForLexV2Bots_{}".format(
            Stack.of(self).account,
            CUSTOM_SUFFIX_SLR)

        # drlex_data_privacy = { "ChildDirected" : False}

        # english_us_bot_locale = lex.CfnBot.BotLocaleProperty(
        #     locale_id="en_US",
        #     nlu_confidence_threshold=123
        # )

        # drlex_bot = lex.CfnBot(self,"DrLexBot",
        #                     idle_session_ttl_in_seconds=3600,
        #                     name="DrLexBot-cdk",
        #                     role_arn=lex_service_linked_role_arn,
        #                     data_privacy=drlex_data_privacy)

        # drlex_bot.add_depends_on(lex_service_linked_role)
        
