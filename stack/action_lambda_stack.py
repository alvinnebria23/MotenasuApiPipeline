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
from aws_cdk import aws_ec2 as ec2
from action_lambda.constant.action_lambda_constant import LambdaConstant

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
        self._create_action_lambda_layer()
        self.lambda_role = self._create_lambda_role()
        self.vpc = self._get_vpc()
        self.subnet = self._get_subnet()
        self.security_group = self._get_security_group()
        self.action_lambda = self._create_action_lambda()

    def _create_action_lambda_layer(self) -> lambda_.LayerVersion:
        """Create a common Lambda layer shared between functions.

        Sets up the common layer with code that will be available to all Lambda functions.
        """
        self.action_lambda_layer = self._create_lambda_layer(
            f"MotenasuV2ApiActionLambdaLayer{self.custom_stack_name}",
            "action_lambda",
            "This Lambda layer contains code for deploying and deleting stacks.",
        )

    def _create_action_lambda(self) -> lambda_.Function:
        """Create Lambda function for deploying and deleting stacks."""
        name = f"MotenasuV2ApiActionLambda-{self.custom_stack_name}"
        description = "This Lambda function deploys and deletes other stacks."

        lambda_env = {
            **{k: os.getenv(k) for k in ["DB_HOST", "DB_NAME", "DB_PASSWORD", "DB_PORT", "DB_USER"]},
        }
        function_layer = self._create_lambda_layer(
            f"{name}Layer{self.custom_stack_name}",
            "lambda_layer/action_lambda/lib",
            "This Lambda layer contains dependencies needed by Motenasu V2 API.",
        )
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
            layers=[function_layer, self.action_lambda_layer],
            environment=lambda_env,
            role=self.lambda_role,
            vpc=self.vpc,
            vpc_subnets={"subnets": [self.subnet]},
            security_groups=[self.security_group],
            reserved_concurrent_executions=None,
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
    
    def _create_lambda_role(self) -> iam.Role:
        """Create IAM role for Lambda functions with necessary permissions.

        Returns:
            iam.Role: Created IAM role with attached policies for Lambda execution
        """
        # Create a new IAM role for the Lambda function
        lambda_role = iam.Role(
            self,
            f"MotenasuV2ApiLambdaRole{self.custom_stack_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="IAM role for the MotenasuV2ApiLambda function",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )

        # Add S3 permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:HeadObject",
                    "s3:ListBucket"
                ],
                resources=[
                    f"arn:aws:s3:::{LambdaConstant.MOTENASU_SERVERLESS_SHARED_BUCKET}",
                    f"arn:aws:s3:::{LambdaConstant.MOTENASU_SERVERLESS_SHARED_BUCKET}/*"
                ]
            )
        )

        # Add CodePipeline permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "codepipeline:StartPipelineExecution",
                    "codepipeline:GetPipelineExecution",
                    "codepipeline:ListPipelineExecutions"
                ],
                resources=[
                    f"arn:aws:codepipeline:*:*:MotenasuApiPipeline"
                ]
            )
        )

        return lambda_role
    
    def _create_lambda_layer(self, name: str, directory: str, description: str) -> lambda_.LayerVersion:
        """Create a Lambda layer for shared dependencies.

        Args:
            name: Name of the Lambda layer
            directory: Directory containing the layer code
            description: Description of the Lambda layer

        Returns:
            lambda_.LayerVersion: Created Lambda layer with specified dependencies
        """
        return lambda_.LayerVersion(
            self,
            name,
            code=lambda_.Code.from_asset(directory),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description=description,
        )
    
    def _get_vpc(self) -> ec2.IVpc:
        """Get VPC configuration from environment variables.

        Returns:
            ec2.IVpc: VPC configuration for the stack
        """
        vpc_id = os.getenv("VPC_ID")
        availability_zone = [item.strip() for item in os.getenv("AVAILABILITY_ZONE", "").split(",") if item.strip()]

        return ec2.Vpc.from_vpc_attributes(
            self,
            "MotenasuV2ApiVPC",
            vpc_id=vpc_id,
            availability_zones=availability_zone,
        )

    def _get_subnet(self) -> ec2.ISubnet:
        """Get subnet configuration from environment variables.

        Returns:
            ec2.ISubnet: Subnet configuration for the stack
        """
        subnet_id = os.getenv("SUBNET_ID")
        return ec2.Subnet.from_subnet_id(self, "MotenasuV2ApiSubnet", subnet_id)

    def _get_security_group(self) -> ec2.ISecurityGroup:
        """Get security group configuration from environment variables.

        Returns:
            ec2.ISecurityGroup: Security group configuration for the stack
        """
        security_group_id = os.getenv("SECURITY_GROUP_ID")
        return ec2.SecurityGroup.from_security_group_id(self, "MotenasuV2ApiSecurityGroup", security_group_id)
