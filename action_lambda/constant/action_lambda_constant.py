class ActionConstant:
    ACTION = "action"
    DEPLOY = "deploy"
    DESTROY = "destroy"

class LambdaConstant:
    STACK_NAME = "stack_name"
    TEMPLATE_BODY = "template_body"
    PARAMETERS = "parameters"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_TOKEN_EXPIRY_IN_MINUTES = "JWT_TOKEN_EXPIRY_IN_MINUTES"

class StatusCodeConstant:
    SUCCESS = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
    NOT_FOUND = 404
    CONFLICT = 409

class SiteMasterConstant:
    SITE_MASTER_ID = "site_master_id"
    MANAGER_DOMAIN = "manager_domain"

