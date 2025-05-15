import os
from typing import Dict, Optional

# AWS CDK imports
from aws_cdk import (
    Duration,
    Stack,
)
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

class ActionLambdaStack(Stack):
    """AWS CDK Stack for Lambda function that deploys and deletes other stacks."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        # Add description for cloud formation's stack
        kwargs["description"] = "This stack deploys and deletes other stacks."
        super().__init__(scope, construct_id, **kwargs)
        # Initialize stack name at the beginning
        stack_name_env = os.getenv("STACK_NAME", "")
        self.custom_stack_name = f"{stack_name_env}" if stack_name_env else ""

        # Create Lambda function
        self.action_lambda = self._create_action_lambda()

    def _create_action_lambda(self) -> lambda_.Function:
        """Create Lambda function for deploying and deleting stacks."""
        name = f"MotenasuV2ApiActionLambda-{self.custom_stack_name}"
        description = "This Lambda function deploys and deletes other stacks."

        # Create Lambda function
        lambda_function = lambda_.Function(
            self,
            name,
            function_name=name,
            description=description,
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("action_lambda"),
            handler="lambda_function.handler",
            timeout=Duration.minutes(5),
            memory_size=256,
        )

        # Grant permissions to deploy and delete stacks
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    # Stack operations
                    "cloudformation:CreateStack",
                    "cloudformation:DeleteStack",
                    "cloudformation:DescribeStacks",
                    "cloudformation:ListStacks",
                    "cloudformation:UpdateStack",
                    "cloudformation:ValidateTemplate",
                    
                    # Stack set operations
                    "cloudformation:CreateStackSet",
                    "cloudformation:DeleteStackSet",
                    "cloudformation:DescribeStackSet",
                    "cloudformation:ListStackSets",
                    "cloudformation:UpdateStackSet",
                    
                    # Stack instance operations
                    "cloudformation:CreateStackInstances",
                    "cloudformation:DeleteStackInstances",
                    "cloudformation:DescribeStackInstance",
                    "cloudformation:ListStackInstances",
                    
                    # Change set operations
                    "cloudformation:CreateChangeSet",
                    "cloudformation:DeleteChangeSet",
                    "cloudformation:DescribeChangeSet",
                    "cloudformation:ExecuteChangeSet",
                    "cloudformation:ListChangeSets",
                    
                    # Template operations
                    "cloudformation:GetTemplate",
                    "cloudformation:GetTemplateSummary",
                    "cloudformation:SetStackPolicy",
                    "cloudformation:GetStackPolicy",
                    
                    # Stack events and resources
                    "cloudformation:DescribeStackEvents",
                    "cloudformation:DescribeStackResources",
                    "cloudformation:ListStackResources",
                    
                    # Stack drift operations
                    "cloudformation:DetectStackDrift",
                    "cloudformation:DescribeStackDriftDetectionStatus",
                    "cloudformation:ListStackResources",
                    
                    # Stack policy operations
                    "cloudformation:SetStackPolicy",
                    "cloudformation:GetStackPolicy",
                    
                    # Stack parameter operations
                    "cloudformation:DescribeStackParameters",
                    "cloudformation:GetTemplateSummary"
                ],
                resources=["*"]
            )
        )

        # Add S3 permissions
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                resources=[
                    "arn:aws:s3:::motenasu-api-pipeline",
                    "arn:aws:s3:::motenasu-api-pipeline/*"
                ]
            )
        )

        return lambda_function