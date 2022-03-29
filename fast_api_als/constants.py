import os

# AWS credential constants
ALS_AWS_SECRET_KEY = os.getenv("ALS_AWS_SECRET_KEY")
ALS_AWS_ACCESS_KEY = os.getenv("ALS_AWS_ACCESS_KEY")
ALS_AWS_REGION = os.getenv("ALS_AWS_REGION_NAME", "us-east-1")
ALS_AWS_ACCOUNT = os.getenv("ALS_AWS_ACCOUNT", "082830052325")

# DDB Constants
DB_TABLE_NAME = os.getenv("ALS_DDB_TABLE_NAME", "auto-lead-scoring")
DEALER_DB_TABLE = os.getenv("ALS_DEALER_DDB_TABLE_NAME", "als-dealer-table")

# HYU Endpoint Constants
HYU_DEALER_ENDPOINT_NAME = os.getenv('HYU_DEALER_ENDPOINT_NAME')
HYU_NO_DEALER_ENDPOINT_NAME = os.getenv('HYU_NO_DEALER_ENDPOINT_NAME')

# BMW Endpoint Constants
BMW_DEALER_ENDPOINT_NAME = os.getenv('BMW_DEALER_ENDPOINT_NAME')

# Admin Constants
SUPPORTED_OEMS = ["hyundai", "bmw"]

# Data Tool 3rd Party Service Constants
ALS_DATA_TOOL_REQUEST_KEY = os.getenv('ALS_DATA_TOOL_REQUEST_KEY')
ALS_DATA_TOOL_SERVICE_URL = os.getenv('ALS_DATA_TOOL_SERVICE_URL')
ALS_DATA_TOOL_PHONE_VERIFY_METHOD = os.getenv('ALS_DATA_TOOL_PHONE_VERIFY_METHOD')
ALS_DATA_TOOL_EMAIL_VERIFY_METHOD = os.getenv('ALS_DATA_TOOL_EMAIL_VERIFY_METHOD')

# S3 bucket for lead dumping
S3_BUCKET_NAME = os.getenv("ALS_QUICKSIGHT_BUCKET_NAME", "auto-lead-scoring-quicksight")
# Cognito Constants
ALS_USER_POOL_ID = os.getenv('ALS_USER_POOL_ID')
# Quicksight Dashboards

PROVIDER_DASHBOARD_ID = os.getenv('PROVIDER_DASHBOARD', "ceb3c69c-707d-4709-a072-89745bfea377")
OEM_DASHBOARD_ID = os.getenv('OEM_DASHBOARD', "c504a613-a3d1-48ad-9212-73552e7c0b69")
ADMIN_DASHBOARD_ID = os.getenv('ADMIN_DASHBOARD', "92e96960-d42e-4f12-9910-0448c1e08fd6")

DASHBOARD_ARN = {
    "3PL": f"arn:aws:quicksight:us-east-1:{ALS_AWS_ACCOUNT}:dashboard/{PROVIDER_DASHBOARD_ID}",
    "OEM": f"arn:aws:quicksight:us-east-1:{ALS_AWS_ACCOUNT}:dashboard/{OEM_DASHBOARD_ID}",
    "ADMIN": f"arn:aws:quicksight:us-east-1:{ALS_AWS_ACCOUNT}:dashboard/{ADMIN_DASHBOARD_ID}"
}

SESSION_LIFETIME = 600
S3_BUCKET_NAME = 'auto-lead-scoring-quicksight'
