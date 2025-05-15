import json
import logging
import os
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
        logger.info(f"Attempting to deploy stack: {site_master_id}")
        
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

        if not site_master_id:
            return {
                'statusCode': StatusCodeConstant.BAD_REQUEST,
                'body': json.dumps({
                    'message': 'site_master_id is required in request body'
                })
            }

        # Initialize AWS clients
        import boto3
        s3_client = boto3.client('s3')
        cloudformation_client = boto3.client('cloudformation')

        # Create .env file content
        env_content = f"""
# Environment variables for {site_master_id}
SITE_MASTER_ID={site_master_id}
JWT_SECRET_KEY={os.getenv(LambdaConstant.JWT_SECRET_KEY)}
JWT_TOKEN_EXPIRY_IN_MINUTES={os.getenv(LambdaConstant.JWT_TOKEN_EXPIRY_IN_MINUTES)}
"""
        
        # Upload .env file to S3
        try:
            s3_client.put_object(
                Bucket='motenasu-api-pipeline',
                Key=f'client_env/{site_master_id}/.env',
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

        # Check if stack exists and deploy/update
        try:
            cloudformation_client.describe_stacks(StackName=stack_name)
            logger.info(f"Stack {stack_name} exists, proceeding with update")
            
            # Update the stack
            cloudformation_client.update_stack(
                StackName=stack_name,
                TemplateBody=event.get(LambdaConstant.TEMPLATE_BODY),
                Parameters=event.get(LambdaConstant.PARAMETERS, [])
            )
            
            return {
                'statusCode': StatusCodeConstant.SUCCESS,
                'body': json.dumps({
                    'message': f'Stack {stack_name} update initiated successfully and .env file uploaded to S3',
                    'stack_name': stack_name
                })
            }
            
        except cloudformation_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                # Create new stack if it doesn't exist
                cloudformation_client.create_stack(
                    StackName=stack_name,
                    TemplateBody=event.get(LambdaConstant.TEMPLATE_BODY),
                    Parameters=event.get(LambdaConstant.PARAMETERS, [])
                )
                
                return {
                    'statusCode': StatusCodeConstant.SUCCESS,
                    'body': json.dumps({
                        'message': f'Stack {stack_name} creation initiated successfully and .env file uploaded to S3',
                        'stack_name': stack_name
                    })
                }
            else:
                raise e

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
        if not site_master_id:
            return {
                'statusCode': StatusCodeConstant.BAD_REQUEST,
                'body': json.dumps({
                    'message': 'site_master_id is required in request body'
                })
            }

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