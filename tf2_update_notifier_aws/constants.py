"""Various constants used throughout the program.
"""
import os

# AWS Resources
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
S3_BUILD_ID_FILE = os.environ["S3_BUILD_ID_FILE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

class Boto:
    SNS = "sns"
    S3 = "s3"

class StatusCodes:
    SUCCESS = 200
    FAILURE = 300

class Misc:
    PROJECT_NAME = "TF2 Update Notifier"
    # This should be the URL of the RSS feed from SteamDB that has the patch data
    PATCH_NOTES_RSS_URL = os.environ["PATCH_NOTES_RSS_URL"]
