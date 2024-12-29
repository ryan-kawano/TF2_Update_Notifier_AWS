"""
Holds various constants. Some of them are retrieved from environment variables in AWS Lambda.
"""
import os

# S3
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
S3_BUILD_ID_FILE = os.environ["S3_BUILD_ID_FILE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

# Return codes
SUCCESS_RETURN_CODE = 200
FAILURE_RETURN_CODE = 300

PATCH_NOTES_RSS_URL = os.environ["PATCH_NOTES_RSS_URL"]
