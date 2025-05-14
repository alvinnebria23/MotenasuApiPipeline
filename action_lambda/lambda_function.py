import json
import logging
from typing import Dict, Any
from constant.action_lambda_constant import ActionConstant, LambdaConstant, StatusCodeConstant
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to deploy or destroy CloudFormation stacks
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        action = event.get(ActionConstant.ACTION)
        stack_name = event.get(LambdaConstant.STACK_NAME)

        logger.info(f"[Action: {action}], [Stack Name: {stack_name}]")
        
        if action == ActionConstant.DEPLOY:
            return deploy_stacks(stack_name)
        elif action == ActionConstant.DESTROY:
            return destroy_stacks(stack_name)
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

def deploy_stacks(stack_name: str) -> Dict[str, Any]:
    return

def destroy_stacks(stack_name: str) -> Dict[str, Any]:
    """Delete CloudFormation stacks."""
    try:        
        if not stack_name:
            return {
                'statusCode': StatusCodeConstant.BAD_REQUEST,
                'body': json.dumps({
                    'message': 'stack_name is required in request body'
                })
            }

        # Initialize CloudFormation client
        import boto3
        cloudformation_client = boto3.client('cloudformation')
        
        try:
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
                    'stack_name': stack_name
                })
            }
            
        except cloudformation_client.exceptions.ClientError as e:
            logger.info(str(e))
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