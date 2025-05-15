import json
import logging
import time
import boto3
from typing import Dict, Any
from constant.action_lambda_constant import ActionConstant, LambdaConstant, SiteMasterConstant, StatusCodeConstant
from repository.site_master_repository import SiteMasterRepository
from util.database_util import DatabaseUtil

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Initialize database connection
DatabaseUtil.initialize()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to deploy or destroy CloudFormation stacks
    """
    try:
        action = event.get(ActionConstant.ACTION)
        site_master_id = event.get(SiteMasterConstant.SITE_MASTER_ID)

        logger.info(f"Action: {action}, SITE_MASTER_ID: {site_master_id}")
        
        if not site_master_id:
            return {
                'statusCode': StatusCodeConstant.BAD_REQUEST,
                'body': json.dumps({
                    'message': 'site_master_id is required in request body'
                })
            }
        
        if action == ActionConstant.DEPLOY:
            return deploy_stacks(event, site_master_id)
        elif action == ActionConstant.DESTROY:
            return destroy_stacks(site_master_id)
        else:
            logger.error(f"Invalid action: {action}")
            return {
                'statusCode': StatusCodeConstant.BAD_REQUEST,
                'body': json.dumps({
                    'message': 'Invalid action. Use "deploy" or "destroy" in the request body'
                })
            }
            
    except Exception as e:
        error_message = f"Error during stack operation: {str(e)}"
        logger.exception(error_message)
        
        return {
            'statusCode': StatusCodeConstant.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                'message': 'Operation failed',
                'error': str(e)
            })
        }

def deploy_stacks(event: Dict[str, Any], site_master_id: str) -> Dict[str, Any]:
    """Deploy CloudFormation stacks and upload .env file to S3."""
    try:
        site_master_id = event.get(SiteMasterConstant.SITE_MASTER_ID)
        jwt_expiry_minutes = event.get(LambdaConstant.JWT_TOKEN_EXPIRY_IN_MINUTES)
        if not site_master_id:
            return {
                'statusCode': StatusCodeConstant.BAD_REQUEST,
                'body': json.dumps({
                    'message': 'site_master_id is required in request body'
                })
            }
        
        logger.info(f"Attempting to deploy stack: {site_master_id}")
        
        # Initialize AWS clients first
        s3_client = boto3.client('s3')

        # Check S3 bucket first
        env_file_key = f'motenasu-api/config/client_env/{site_master_id}.env'
        try:
            s3_client.head_object(
                Bucket=LambdaConstant.MOTENASU_SERVERLESS_SHARED_BUCKET,
                Key=env_file_key
            )
            logger.info(f".env file exists in S3 for site master id {site_master_id}")
            
            return {    
                'statusCode': StatusCodeConstant.SUCCESS,
                'body': json.dumps({
                    'message': f'env file exists in S3 for site master id {site_master_id}',
                })
            }
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"Calling pipeline for site master id {site_master_id}")
                # Call MotenasuApiPipeline
                try:
                    # Now that we know the file exists, proceed with database check
                    site_master_data = SiteMasterRepository().get_site_master_by_id(site_master_id)
                    manager_domain = site_master_data.get(SiteMasterConstant.MANAGER_DOMAIN) if site_master_data else None
                    db_host = site_master_data.get(SiteMasterConstant.DB_HOST) if site_master_data else None
                    db_name = site_master_data.get(SiteMasterConstant.DB_NAME) if site_master_data else None
                    db_password = site_master_data.get(SiteMasterConstant.DB_PASSWORD) if site_master_data else None
                    db_port = site_master_data.get(SiteMasterConstant.DB_PORT) if site_master_data else None
                    db_user = site_master_data.get(SiteMasterConstant.DB_USER) if site_master_data else None

                    if not manager_domain:
                        return {
                            'statusCode': StatusCodeConstant.NOT_FOUND,
                            'body': json.dumps({
                                'message': f'No manager_domain found for site master ID {site_master_id}'
                            })
                        }
                    
                    stack_name = manager_domain.replace(".", "-")

                    logger.info(f"Starting MotenasuApiPipeline for site_master_id: {site_master_id}")
                    codepipeline_client = boto3.client('codepipeline')
                    response = codepipeline_client.start_pipeline_execution(
                        name='MotenasuApiPipeline',
                        clientRequestToken=f"trigger-{site_master_id}-{int(time.time())}"  # Unique token for each execution
                    )
                    execution_id = response['pipelineExecutionId']
                    logger.info(f"Pipeline execution started: {execution_id}")

                    # Upload .env file to S3
                    try:
                        # Create .env file content
                        env_content = f"""
# Environment variables for {site_master_id}
STACK_NAME={stack_name}

DB_HOST={db_host}
DB_NAME={db_name}
DB_PASSWORD={db_password}
DB_PORT={db_port}
DB_USER={db_user}

JWT_TOKEN_EXPIRY_IN_MINUTES={jwt_expiry_minutes}
"""

                        s3_client.put_object(
                            Bucket=LambdaConstant.MOTENASU_SERVERLESS_SHARED_BUCKET,
                            Key=f'motenasu-api/config/lambda_trigger/{execution_id}/{site_master_id}.env',
                            Body=env_content.encode('utf-8'),
                            ContentType='text/plain'
                        )
                        logger.info(f"Successfully uploaded .env file to S3 for site master id {site_master_id}")
                    except Exception as e:
                        logger.error(f"Failed to upload .env file to S3: {str(e)}")
                        return {
                            'statusCode': StatusCodeConstant.INTERNAL_SERVER_ERROR,
                            'body': json.dumps({
                                'message': 'Failed to upload .env file to S3',
                                'error': str(e)
                            })
                        }  
                    
                except Exception as e:
                    logger.error(f"Failed to start pipeline: {str(e)}")
                    return {
                        'statusCode': StatusCodeConstant.INTERNAL_SERVER_ERROR,
                        'body': json.dumps({
                            'message': 'Failed to start MotenasuApiPipeline',
                            'error': str(e)
                        })
                    }
            else:
                # Some other S3 error occurred
                logger.error(f"Error checking .env file in S3: {str(e)}")
                return {
                    'statusCode': StatusCodeConstant.INTERNAL_SERVER_ERROR,
                    'body': json.dumps({
                        'message': 'Error checking .env file in S3',
                        'error': str(e)
                    })
                }
    except Exception as e:
        error_message = f"Error during stack deployment: {str(e)}"
        logger.exception(error_message)

        return {
            'statusCode': StatusCodeConstant.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                'message': 'Stack deployment failed',
                'error': str(e)
            })
        }

def destroy_stacks(site_master_id: str) -> Dict[str, Any]:
    """Delete CloudFormation stacks."""
    try:
        # Get stack name from database
        try:
            stack_name = None
            site_master_data = SiteMasterRepository().get_site_master_by_id(site_master_id)
            manager_domain = site_master_data.get(SiteMasterConstant.MANAGER_DOMAIN) if site_master_data else None
             
            if manager_domain:
                stack_name = manager_domain.replace(".", "-")
            else:
                return {
                    'statusCode': StatusCodeConstant.NOT_FOUND,
                    'body': json.dumps({
                        'message': f'No manager domain found for site master ID {site_master_id}'
                    })
                }

            logger.info(f"Found stack name {stack_name} for site_master_id {site_master_id}")
            
            # Initialize CloudFormation client
            import boto3
            cloudformation_client = boto3.client('cloudformation')
            
            # Check if stack exists
            cloudformation_client.describe_stacks(StackName=stack_name)
            logger.info(f"Stack {stack_name} exists, proceeding with deletion")
            
            # Delete the stack
            cloudformation_client.delete_stack(StackName=stack_name)
            logger.info(f"Stack {stack_name} deletion initiated")
            
            return {
                'statusCode': StatusCodeConstant.SUCCESS,
                'body': json.dumps({
                    'message': f'Stack {stack_name} deletion initiated successfully',
                    'stack_name': stack_name,
                    'site_master_id': site_master_id
                })
            }
            
        except Exception as e:
            logger.error(f"Error getting stack name from database: {str(e)}")
            return {
                'statusCode': StatusCodeConstant.INTERNAL_SERVER_ERROR,
                'body': json.dumps({
                    'message': 'Error getting stack name from database',
                    'error': str(e)
                })
            }
            
        except cloudformation_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                return {
                    'statusCode': StatusCodeConstant.NOT_FOUND,
                    'body': json.dumps({
                        'message': f'Stack {stack_name} does not exist',
                        'error': str(e)
                    })
                }
            else:
                raise e

    except Exception as e:
        error_message = f"Error during stack deletion: {str(e)}"
        logger.exception(error_message)

        return {
            'statusCode': StatusCodeConstant.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                'message': 'Stack deletion failed',
                'error': str(e)
            })
        }