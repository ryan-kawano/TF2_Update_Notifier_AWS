"""Various utility functions.
"""
from botocore.client import BaseClient
import feedparser

import constants
from patch_class import Patch


def handle_error(sns_client: BaseClient, error_message: str) -> dict:
    print(error_message)
    send_email(
        sns_client,
        subject=f"{constants.Misc.EMAIL_SUBJECT_PREFIX} - {constants.Misc.PROJECT_NAME} had an error",
        message=error_message
    )
    return generate_return_message(constants.StatusCodes.FAILURE, error_message)


def send_email(sns_client: BaseClient, subject: str, message: str):
    """Sends an email using the SNS client with the provided subject and message.

    :param sns_client: The SNS client to send emails with.
    :type sns_client: BaseClient
    :param subject: The subject line of the email.
    :type subject: str
    :param message: The body of the email.
    :type message: str
    """
    sns_client.publish(
        TopicArn=constants.SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )


def verify_environment_variables() -> str | None:
    """Verifies that the Lambda environment variables were inputted correctly. See README.md for where to set these.

    :return an error message if it's missing environment variables, otherwise returns nothing.
    :rtype: str | None
    """
    print("Verifying that env variables were provided")
    if not constants.S3_BUCKET_NAME:
        return "S3 bucket name was not provided. Please provide one in the env variable \"S3_BUCKET_NAME\""
    if not constants.S3_BUILD_ID_FILE:
        return "S3 build ID file name was not provided. Please provide one in the env variable \"S3_BUILD_ID_FILE\""
    if not constants.SNS_TOPIC_ARN:
        return "SNS topic ARN was not provided. Please provide one in the env variable \"SNS_TOPIC_ARN\""
    if not constants.Misc.PATCH_NOTES_RSS_URL:
        return "Patch notes RSS URL not provided. Please provide one in the env variable \"PATCH_NOTES_RSS_URL\""

    return None


def generate_return_message(status_code : int, status_body: str) -> dict:
    """Generates a status message.

    :param status_code: Return message's status code.
    :type status_code: int
    :param status_body: Return message's body.
    :type status_body: str
    :return: A status message.
    :rtype: dict
    """
    return {
        "statusCode": status_code,
        "body": status_body
    }


def find_largest_build_id(patch_notes_data: feedparser.FeedParserDict) -> Patch:
    """Iterates through all the build IDs to find the largest one.
    The data from the RSS feed seems to come sorted chronologically, so we could probably stop at the 1st entry,
    but checking all the entries is safer. Plus, there usually aren't many entries, so it doesn't take long

    :param patch_notes_data: The result from feedparser.parse() with the RSS url.
    :type patch_notes_data: feedparser.FeedParserDict
    :return: A patch object with the latest patch data.
    :rtype: Patch
    """
    print("Finding largest build ID")
    latest_patch = Patch(-1, "")
    for patch in patch_notes_data.entries:
        print(f"Processing patch: {patch}")

        # Extract the build ID and date
        build_id_full = patch.guid  # Build id comes in the form "build#16294548". Need to remove non-numbers
        print(f"Parsing id: \"{build_id_full}\"")
        id_num_index = build_id_full.find("#") + 1
        if id_num_index == -1:
            print("Couldn't find \"#\" in build ID. Skipping.")
            continue
        else:
            print(f"Found index: {id_num_index}. Extracting build ID with this index.")
        build_id = int(build_id_full[id_num_index:])
        build_date = patch.published
        print(f"Extracted build ID: {build_id} and build date: {build_date}")

        # If it's the first iteration, simply save the build ID as the largest since there is nothing to
        # compare to yet.
        if latest_patch.build_id == -1:
            print(f"This is the first item. So, saving {build_id} as the largest build ID for now.")
            latest_patch.build_id = build_id
            latest_patch.date = build_date
            continue

        # Save the build ID if it's larger than what we have currently
        if build_id > latest_patch.build_id:
            print(f"{build_id} was greater than {latest_patch.build_id}. Saving")
            latest_patch.build_id = build_id
            latest_patch.date = build_date
        else:
            print(f"{build_id} is not greater than {latest_patch.build_id}. Not saving.")

    print(f"Found largest build ID: {latest_patch.build_id} with date: {latest_patch.date}")
    return latest_patch
