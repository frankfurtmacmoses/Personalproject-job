"""
This file contains all the messages for each Watchmen. Messages include details, short messages returned to lambdas, and
the subject of emails.

@author: Michael Garcia
@email: garciam@infoblox.com
"""

COMEDIAN = {
    "exception_details": "There was an exception retrieving the quota information from the VirusTotal API.\n\nTraceback"
                         " of exception:\n{}",
    "exception_short_message": "EXCEPTION: Unable to check VirusTotal quotas, please check logs!",
    "exception_subject": "EXCEPTION: Unable to Check VirusTotal Quotas!",
    "failure_short_message": "FAILURE: A quota was exceeded, please check the logs for more information!",
    "failure_subject": "FAILURE: VirusTotal Quota Exceeded!",
    "quota_exceeded": "Quota \"{}\" exceeded the {}% threshold!\nUsed: {}\nAllowed: {}\nPercent Used: {}%\n",
    "quota_exception_details": "An expected quota was missing from the VirusTotal API response.\n\n{}",
    "success_details": "All VirusTotal quota checks ran successfully and were within the current threshold.",
    "success_short_message": "SUCCESS: All VirusTotal quota checks were within the threshold for today!",
    "success_subject": "SUCCESS: All VirusTotal Quotas Within Threshold!",
}

CROOKSHANKS = {
    "exception_message": "The following source(s) received an error: \n\n {} \n"
                         "Please check the logs for more details!",
    "exception_subject": "EXCEPTION: There was an error while checking for the smartlists!",
    "failure_exception_message": "The following source(s) do not have smartlists: \n\n {} \n\n"
                                 "The following source(s) received an error: \n\n{}",
    "failure_exception_subject": "FAILURE and EXCEPTION: A failure and exception occurred during the smartlists check",
    "failure_message": "The following source(s) do not have smartlists: \n\n {}",
    "failure_subject": "FAILURE: Smartlisting file(s) do not exist in S3!",
    "log_exception_message": "Failed due to an exception: \n\n{}",
    "log_fail_exception_msg": "Failure(s):\n {} \n\n Exception(s):\n {}",
    "log_failure_message": "Failure(s): \n\n{}",
    "success_message": "All smartlisting files can be found in S3!",
    "success_subject": "SUCCESS: All expected smartlisting files exists in S3!",
}

JUPITER = {
    "bad_endpoints_message": "There are endpoints with no path variable, please check the endpoints files locally and "
                             "in S3!",
    "check_logs": "Please check logs for more details!",
    "error_jupiter": "Jupiter: No Results Found",
    "error_subject": "Jupiter: Failure in checking endpoint",
    "failure_subject": "Jupiter: Cyber Intel endpoints monitor detected a failure!",
    "no_results": "There are no results! Endpoint file might be empty or Service Checker may not be working correctly."
                  " Please check logs and endpoint file to help identify the issue.",
    "not_enough_eps": "Jupiter: Too Few Endpoints",
    "not_enough_eps_message": "There are no valid endpoints to check or something is wrong with endpoint file.",
    "results_dne": "Results do not exist! There is nothing to check. Service Checker may not be working correctly. "
                   "Please check logs and endpoint file to help identify the issue.",
    "skip_message_format": "Notification is skipped at {}",
    "success_message": "All endpoints are healthy!",
    "success_subject": "Jupiter: Cyber Intel endpoints are working properly!",
    "s3_fail_load_message": "Cannot load endpoints from the following S3 resource:\n\tBucket: {}\n\tKey: {} \n\n"
                            "Local endpoints being monitored: \n{} \nException that caused failure: {}",
    "s3_fail_load_subject": "Jupiter endpoints - S3 load error"
}

MANHATTAN = {
    "check_email_message": "Please check the email for more details!",
    "exception_details_start": "Manhattan failed due to the following: ",
    "exception_invalid_event_message": "An invalid event was passed from the CloudWatch event, please check the "
                                       "CloudFormation file and CloudWatch events to ensure that the correct parameters"
                                       " are being sent. Metrics can not be checked with an invalid event parameter.",
    "exception_invalid_event_subject": "Manhattan Exception: Invalid CloudWatch Event!",
    "exception_local_load_failure_message": "Cannot load feeds to check from file:\n{}\n\nException: {}",
    "exception_s3_load_failure_message": "A failure occurred loading the feeds_to_check.json file from S3! The local "
                                         "feeds_to_check.json file will be used instead. Please check the logs for more"
                                         " details.\n\nS3 file location: {}/{}\n\nException: {}",
    "exception_s3_load_failure_subject": "Manhattan Exception: Unable to Load S3 Feeds File!",
    "exception_message": "EXCEPTION occurred while checking feeds! Please check the email for more details!",
    "failed_event_check": "Invalid event parameter type passed in from Lambda: {}.",
    "failure_abnormal_message": "One or more feeds are submitting abnormal amounts of domains:",
    "failure_down_message": "One or more feeds are down:",
    "failure_subject": "Manhattan Feeds Failure",
    "no_metrics_message": 'One or more feeds do not have metrics:{}',
    "stuck_tasks_message": 'One or more feeds have been running longer than a day:{}\n\n'
                           'These feeds must be manually stopped within AWS console here: \n{}',
    "subject_exception_message": "Manhattan watchmen failed due to an exception!",
    "success_message": "SUCCESS: Feeds are up and running normally!",
    "success_subject": "{} feeds monitored by Manhattan are up and running!",
    "success_event_check": "The event parameter passed from Lambda is valid."
}

MOTHMAN = {
    "exception_details": "There was an exception while trying to check the ForeverMail S3 files.\n\nTraceback of "
                         "exception:\n{}",
    "exception_subject": "EXCEPTION: Unable to check ForeverMail S3 files!",
    "success_latest_hm": "Check was skipped due to latest S3 file being 0000.tar.gz.\nFile path: {}",
    "success_previous_file_dne": "Latest S3 file exists, but the previous S3 file does not. A notification"
                                 " should have already been sent for the previous file.\nPrevious file: {}",
    "success_previous_hm": "0010.tar.gz S3 file exists and the previous file is not expected to be uploaded.",
    "success_short_message": "SUCCESS: All expected S3 files exist.",
    "success_subject": "SUCCESS: ForeverMail files found on S3",
    "success_unequal_files": "Two most recent files exist and are not the same file!\nLatest file: {}\n"
                             "Previous file: {}",
    "failure_latest_file_dne": "Latest file does not exist: {}",
    "failure_equal_files": "The same file was uploaded twice in a row.\nLatest file: {}\nPrevious file: {}",
    "failure_short_message": "FAILURE: S3 file(s) do not exist or files are the same size.",
    "failure_subject": "FAILURE: ForeverMail S3 Files Error"
}

SLATER = {
    "exception_details": "There was an exception retrieving the quota information from the "
                         "DomainTools API.\n\nTraceback"
                         " of exception:\n{}",
    "exception_message": "EXCEPTION: Unable to check DomainTools quotas, please check logs!",
    "exception_subject": "EXCEPTION: Unable to check DomainTools Quotas!",
    "failure_message": "FAILURE: A quota was exceeded, please check the logs for more information!",
    "failure_subject": "WARNING: DomainTools Quota Exceeded!",
    "quota_exceeded": "Quota for {} exceeded the {}% threshold!\nUsed: {}\nAllowed: {}\nPercent Used: {}%\n",
    "success_details": "All the DomainTools quota checks ran successfully and were within the threshold.",
    "success_message": "SUCCESS: All DomainTools quota checks were within the threshold for today!",
    "success_subject": "SUCCESS: All DomainTools Quotas Within Threshold!"
}

RORSCHACH = {
    "exception_subject": "EXCEPTION: Unable to Check S3 files for {}!",
    "exception_invalid_event_subject": "EXCEPTION: Rorschach Received An Invalid CloudWatch Event!",
    "exception_config_load_failure_subject": "EXCEPTION: Unable to Load S3 Targets Config File!",
    "exception_invalid_event_details": "An invalid event was passed from the CloudWatch event, please check the "
                                       "CloudFormation file and CloudWatch events to ensure that the correct"
                                       " parameters are being sent. S3 targets can not be checked with an invalid "
                                       "event parameter.",
    "exception_config_not_load_details": "Cannot load S3 targets from file: {}\nException: {}",
    "exception_message": "Exception occurred when checking S3 targets! Please check the logs for more details.",
    "exception_details": "The following S3 paths threw exceptions during their file checks:\n\n{}",
    "success_message": "SUCCESS: All S3 File Checks for {} passed!",
    "success_details": "All of the S3 file checks for the {} target passed successfully!",
    "success_subject": "SUCCESS: All S3 File Checks for {} Passed!",
    "success_event_check": "The event parameter passed from Lambda is valid.",
    "failed_event_check": "Invalid event parameter type passed in from Lambda: {}.",
    "failure_prefix_suffix_not_match": "There is at least one S3 that key did not match the expected "
                                       "prefix: {} and suffix: {}.\n",
    "failure_file_empty": "The following S3 file is empty: {}",
    "failure_total_file_size_below_threshold": "The size of all files found in {} is {} KB, which is less than "
                                               "expected total file size {} KB.\n",
    "failure_total_objects": "The number of objects found in {} is {}, which is less than expected total objects "
                             "count {}.\n",
    "failure_bucket_not_found": "FAILURE: The following bucket was not found: {}.\n",
    "failure_no_file_found_s3": "The following file was not found in S3: {}",
    "failure_subject": "FAILURE: {} S3 File Checks Failed!",
    "failure_details": "The following S3 paths failed their checks:\n{}",
    "failure_message": "FAILURE: At least one S3 file check did not pass, please check the logs for more details!",
    "generic_failure_subject": "FAILURE: At Least One S3 Target Has Failed!",
    "generic_exception_subject": "Exception: At Least One S3 Target Has An Exception!",
    "generic_fail_exception_subject": "EXCEPTION and FAILURE: At Least One S3 Target Has An Exception"
                                      " and Failure!",
    "generic_success_subject": "SUCCESS: All S3 Targets Passed!."
}

SILHOUETTE = {
    "success_message": "Lookalike2 algorithm is up and running!",
    "failure_message": "Lookalike2 algorithm never added files yesterday! "
                       "The algorithm may be down or simply did not complete!",
    "success_subject": "Silhouette: Lookalike2 files have been successfully detected in S3!",
    "failure_subject": "FAILURE: Silhouette detected an issue with the Lookalike2 algorithm!",
    "exception_subject": "EXCEPTION: Silhouette failed to check the Lookalike2 algorithm!",
    "exception_message": "Silhouette for lookalike2 algorithm failed on \n\t\"{}\" \ndue to "
                         "the Exception:\n\n{}\n\nPlease check the logs!",
    "exception_short_message": "Silhouette for lookalike2 algorithm failed due to an exception, please check the logs!"
}
