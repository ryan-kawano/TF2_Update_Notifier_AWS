# TF2 Update Notifier AWS
An application for AWS Lambda that will send an email when updates for the online video-game "Team Fortress 2" are released.

It utilizes data from SteamDB's RSS feed for TF2 updates. The application is set to run repeatedly on a timer. When the timer goes off, it'll retrieve the latest patch data from SteamDB, compare it to the latest build data that we have cached, and send an email if SteamDB has a newer version. The comparison is based on build ID, so larger build ID = newer build. It will also send an email if it encountered any errors such as missing cached file, download errors, etc.

## Example Notification
```
Subject: [URGENT] - Update has been released for TF2
From: AWS Notifications

Cached build ID (old): 17400490
Steam DB build ID (new): 17400495


--
If you wish to stop receiving notifications from this topic, please click or visit the link below to unsubscribe:
<Unsubscribe Link>

Please do not reply directly to this email. If you have any questions or comments regarding this email, please contact us at <Contact Link>
```

## Requirements
1. An AWS account
2. An email to receive notifications

## Set up on AWS:
Before doing the steps below, make sure the `region` you are using is set to the correct one.
### Simple Notification Service
This is the service that will actually send the email.
1. Go to `Topics`.
2. Click `Create topic`.
3. For ```Type```, use ```Standard```.
4. Name it `TF2_Update_Notifier_Topic`.
5. Keep the rest of the settings as default.
6. Click ```Create topic``` on the bottom-right.
7. Open the topic and click `Create subscription`.
8. For ```Protocol```, choose ```email``` and enter the email you would like notifications to be sent to.
9. Confirm the subscription by opening the email's inbox and clicking the link in the email that was sent.

### S3
This is where we will cache the build ID.
1. Click```General purpose buckets```.
2. Click ```Create bucket```.
3. Name it anything.
4. Keep the rest of the settings as default.
5. Click ```Create bucket``` on the bottom-right.

### IAM - Policy
The application needs certain permissions to run correctly.
1. Click `Policies`.
2. Click `Create policy`.
3. Click the `JSON` tab.
4. Copy and paste the `IAM_policy.json` included in this repo and fill in any places that have the text `FILL IN`. For `REGION`, type in the region you are using, i.e. `us-west-1`, `us-east-2`, etc. For `ACCOUNT_ID`, fill in your account ID, it will be in the top-right if you click your account name. For `S3 BUCKET NAME`, enter the name of the bucket you created earlier.
5. Click `Next`.
6. Name it `TF2_Update_Notifier_Policy`.
7. Click `Create policy` on the bottom-right.

### IAM - Role
This role uses the policy created above.
1. Click `Roles`.
2. Click `Create role`.
3. For `Trusted entity type`, choose `AWS Service`.
4. For `Use case` -> `Service or use case` choose `Lambda`.
5. Click `Next`.
6. Check the policy that we created in the earlier section.
7. Click `Next`.
8. Name it `TF2_Update_Notifier_Role`.
9. Click `Create role`.

###  Lambda Part 1 - Creating the function
This is the function that has the main application code. It parses the latest build data and determines whether to send an email.
1. Click `Functions`.
2. Click `Create function`.
3. Choose `Author from scratch`.
4. Name it `TF2_Update_Notifier_Lambda`.
5. For `Runtime`, choose `Python 3.11`.
6. For `Architecture`, choose `x86_64`.
7. Expand the `Change default execution role` section.
8. Under `Execution Role`, choose `Use an existing role`.
9. Select the role that we created previously. It should be named `TF2_Update_Notifier_Role`.
10. Click `Create function`.

### Lambda Part 2 - Adding the layer
The Lambda uses external Python libraries, so a layer containing these libraries needs to be added.
1. Follow the instructions in this link to create the layer using the `requirements.txt` file in this repo. https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html
2. After creating the layer `.zip` file, follow the instructions below.
3. Open our Lambda function.
4. Click `Layers` on the left-hand side.
5. Click `Create layer`.
6. Name it `TF2_Update_Notifier_Layer`.
7. Choose `Upload a .zip file`.
8. Upload the layer that we created previously.
9. For `Compatible architectures`, choose `x86_64`.
10. For `Compatible runtimes`, choose `Python 3.11`.
11. Click `Create` on the bottom-right. The layer has been uploaded.
12. Click `Functions` on the left-hand side.
13. Click the function we created.
14. Scroll down to `Layers`.
15. Click `Add a layer`.
16. Choose `Custom layers` and select the layer we uploaded previously.
17. Choose the latest version.
18. Click `Add` on the bottom-right.

### Lambda Part 3 - Adding environment variables
1. Open our function.
2. Click on the `Configuration` tab.
3. Click on `Environment variables`.
4. Click `edit` and add these environment variables:
   * Key = S3_BUCKET_NAME, Value = \<NAME_OF_S3_BUCKET_CREATED_EARLIER\>
   * Key = S3_BUILD_ID_FILE, Value = latest_build.txt.
   * Key = SNS_TOPIC_ARN, Value = \<The ARN of the SNS topic you created earlier\>
     * Open the SNS topic in order to get the ARN.
   * Key = PATCH_NOTES_RSS_URL, Value = https://steamdb.info/api/PatchnotesRSS/?appid=440
     * This is the RSS feed for TF2 taken from SteamDB.
5. Click `Save` on the bottom-right.

### Lambda Part 4 - Adding the source code
1. Open our function.
2. Open the `Code` tab.
3. In order to upload our code, you may do one of the below:
   1. Create the same files in the integrated IDE and copy and paste the source code manually into them.
   2. Add the repo files to a .zip file and upload it via the `Upload from` button. If zipping, make sure to select all the files at the base-level of this repo and then zip it. Don't zip the folder `TF2_Update_Notifier_AWS`. When the .zip is unzipped, it should unzip to the individual files, not a directory containing the individual files. If doing this method, you may need to refresh the page for the uploaded code to show up.
4. After adding the code, make sure to click `Deploy` in the IDE.
5. At this point, you may test the code by clicking `Test` under the `Test` tab.

### EventBridge
This is the timer that will execute the Lambda.
1. Click ```Rules```.
2. Click `Create rule`.
3. Name it `TF2_Update_Notifier_Timer`
4. For ```Rule type```, choose ```Schedule```. If it asks you to use ```EventBridge Scheduler```, just ignore it and click ```Continue to create rule``` instead of ```Continue in EventBridge Scheduler```.
5. For ```Define Schedule``` -> ```Schedule Pattern```, choose ```A schedule that runs at a regular rate, such as every 10 minutes.```.
6. For ```Rate expression```, enter a desired value. This will be the frequency in which the application will check if there was a new TF2 update. I recommend setting this to 1 hour.
7. Click `Next` on the bottom-right.
8. Under `Select target(s)` -> `Target 1`, choose `AWS service`.
9. Under `Select a target`, choose `Lambda function`.
10. Under `Function`, choose the lambda function we created. It should be called `TF2_Update_Notifier_Lambda`.
11. Click `Next` on the bottom-right until the end.
12. Finally click `Create rule` on the bottom-right.

After following these steps, the code should run automatically based on whatever time frequency you set in EventBridge. Now, it should automatically email you if a new update is released for TF2. 

## Notes
1. If the timer is set to every hour, then it should be within the limits on AWS to be considered free-tier. Double-check AWS's current criteria for free-tier to be certain.
