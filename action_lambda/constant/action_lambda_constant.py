class ActionConstant:
    ACTION = "action"
    DEPLOY = "deploy"
    DESTROY = "destroy"

class LambdaConstant:
    STACK_NAME = "stack_name"
    TEMPLATE_BODY = "template_body"
    PARAMETERS = "parameters"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_TOKEN_EXPIRY_IN_MINUTES = "jwt_expiry_minutes"
    MOTENASU_SERVERLESS_SHARED_BUCKET = "motenasu-serverless-shared"

class StatusCodeConstant:
    SUCCESS = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
    NOT_FOUND = 404
    CONFLICT = 409

class SiteMasterConstant:
    SITE_MASTER_ID = "site_master_id"
    MANAGER_DOMAIN = "manager_domain"
    DB_HOST = "db_host"
    DB_NAME = "db_name"
    DB_PASSWORD = "db_password"
    DB_PORT = "db_port"
    DB_USER = "db_user"

