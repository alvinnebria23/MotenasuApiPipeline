#!/usr/bin/env python3
import os
from dotenv import load_dotenv

import aws_cdk as cdk
from stack.action_lambda_stack import ActionLambdaStack

load_dotenv(override=True)

#Set stack name
stack_name_env = os.getenv("STACK_NAME", "")
custom_stack_name = f"-{stack_name_env}" if stack_name_env else ""

app = cdk.App()
ActionLambdaStack(app, f"ActionLambdaStack{custom_stack_name}")

app.synth()