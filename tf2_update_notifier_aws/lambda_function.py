"""Main function that AWS Lambda will run. See the README.md file for more information.
"""
import os

import boto3
import botocore.client
import feedparser

import constants
from utility import(
    send_email,
    verify_environment_variables,
    generate_return_message,
    find_largest_build_id,
    handle_error
)


def lambda_handler(event, context):
    """The main function that will be run by AWS Lambda.

    :return: A status message indicating success or failure.
    :rtype dict
    """
    print("Entered lambda_handler")

    print("Creating boto3 clients")
    s3_client = boto3.client(constants.Boto.S3)
    sns_client = boto3.client(constants.Boto.SNS)

    verify_env_result = verify_environment_variables()
    if verify_env_result is not None:
        return handle_error(sns_client, verify_env_result)

    print(f"Retrieving and parsing RSS data from url \"{constants.Misc.PATCH_NOTES_RSS_URL}\"")
    patch_notes_data = feedparser.parse(constants.Misc.PATCH_NOTES_RSS_URL)
    if not patch_notes_data or not patch_notes_data.entries:
        return handle_error(sns_client,"The RSS feed for TF2 updates from Steam DB was empty." )
    else:
        print(f"Retrieved data from RSS.\nData: {patch_notes_data}")

    # Find the largest build ID
    latest_patch = find_largest_build_id(patch_notes_data)
    if not latest_patch or not latest_patch.build_id or not latest_patch.date:
        return handle_error(sns_client, "Failed when retrieving the latest patch data from the RSS feed.")

    print("Checking if the largest build ID is greater than the one we have stored in S3")
    print(f"Downloading file \"{constants.S3_BUILD_ID_FILE}\" from S3")
    try:
        s3_client.get_object(Bucket=constants.S3_BUCKET_NAME, Key=constants.S3_BUILD_ID_FILE)
        s3_client.download_file(
            Bucket=constants.S3_BUCKET_NAME,
            Key=constants.S3_BUILD_ID_FILE,
            Filename=f"/tmp/{constants.S3_BUILD_ID_FILE}"
        )
    except Exception as e:
        if isinstance(e, botocore.client.ClientError) and e.response["Error"]["Code"] == "NoSuchKey":
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            print(f"Caught ClientError. Code: {error_code}. Message: {error_message}")
            print(f"The file \"{constants.S3_BUILD_ID_FILE}\" was not found on S3. Creating it and uploading it.")
            with open(f"/tmp/{constants.S3_BUILD_ID_FILE}", "w") as build_id_file:
                build_id_file.write(str(latest_patch.build_id))
            try:
                s3_client.upload_file(
                    f"/tmp/{constants.S3_BUILD_ID_FILE}",
                    constants.S3_BUCKET_NAME,
                    constants.S3_BUILD_ID_FILE
                )
            except Exception as e:
                return handle_error(sns_client, f"Caught exception when uploading. Exception: {e}")
            print("Uploaded file to S3")
            send_email(
                sns_client,
                subject=f"{constants.Misc.EMAIL_SUBJECT_PREFIX} - Uploaded new build id file to S3",
                message=(
                    f"There wasn't a build id file on S3, so created a new one and uploaded it. It's possible a new"
                    f" version was released. Latest build ID: {latest_patch.build_id}. Latest build date: "
                    f"{latest_patch.date}"
                ),
            )
            return generate_return_message(
                constants.StatusCodes.FAILURE,
                (
                    f"There wasn't a build id file on S3, so created a new one and uploaded it. It's possible a "
                    f"new version was released. Latest build ID: {latest_patch.build_id}. Latest build date: "
                    f"{latest_patch.date}"
                )
            )
        else:
            return handle_error(
                sns_client,
                f"Caught exception when downloading build ID file from S3. Exception: {e}"
            )

    print("Finished downloading")
    if not os.path.exists(f"/tmp/{constants.S3_BUILD_ID_FILE}"):
        return handle_error(sns_client, f"Could not find build ID file in tmp directory")

    with open(f"/tmp/{constants.S3_BUILD_ID_FILE}", mode="r") as build_id_file:
        # There should only be one line in the file, the build ID.
        cached_build_id = int(build_id_file.readline())
        if not cached_build_id:
            return handle_error(sns_client, "Latest build id file was empty")
        print(f"Comparing cached build ID: {cached_build_id} to steam DB build ID: {latest_patch.build_id}")
        is_new_build = latest_patch.build_id > cached_build_id

    if not is_new_build:
        print("There wasn't a new build. Don't send email")
        return generate_return_message(
            constants.StatusCodes.SUCCESS,
            "There wasn't a new build. Didn't need to send email"
        )

    print("There is a new build. Sending email")
    try:
        send_email(
            sns_client,
            subject=f"{constants.Misc.EMAIL_SUBJECT_PREFIX} - Update has been released for TF2",
            message=f"Cached build ID (old): {cached_build_id}\nSteam DB build ID (new): {latest_patch.build_id}\n")
    except Exception as e:
        return handle_error(sns_client, f"Caught exception when sending email: {e}")

    print("Email sent successfully. Updating build ID file in S3")
    with open(f"/tmp/{constants.S3_BUILD_ID_FILE}", mode="w") as build_id_file:
        write_txt = str(latest_patch.build_id)
        print(f"Writing {write_txt} to file")
        build_id_file.write(str(latest_patch.build_id))
    try:
        s3_client.upload_file(
            f"/tmp/{constants.S3_BUILD_ID_FILE}",
            constants.S3_BUCKET_NAME,
            constants.S3_BUILD_ID_FILE
        )
    except Exception as e:
        return handle_error(sns_client, f"Caught exception when uploading file to S3. Exception: {e}")
    print("Sent email successfully")

    return generate_return_message(
        constants.StatusCodes.SUCCESS,
        "Email sent successfully and S3 updated with new build ID"
    )
