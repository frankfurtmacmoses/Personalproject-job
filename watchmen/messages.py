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
    "exception_message": "EXCEPTION occurred while checking feeds! Please check the email for more details!",
    "failure_abnormal_message": "One or more feeds are submitting abnormal amounts of domains:",
    "failure_down_message": "One or more feeds are down:",
    "failure_subject": "Manhattan Feeds Failure",
    "no_metrics_message": 'One or more feeds do not have metrics:{}',
    "stuck_tasks_message": 'One or more feeds have been running longer than a day:{}\n\n'
                          'These feeds must be manually stopped within AWS console here: \n{}',
    "subject_exception_message": "Manhattan watchmen failed due to an exception!",
    "success_message": "SUCCESS: Feeds are up and running normally!",
    "success_subject": "{} feeds monitored by Manhattan are up and running!",
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
