"""
This file contains all the messages for each Watchmen. Messages include details, short messages returned to lambdas, and
the subject of emails.

@author: Michael Garcia
@email: garciam@infoblox.com
"""

BERNARD = {
    "exception_local_load_failure_message": "Cannot load clusters to check from file:\n{}\n\nException: {}",
    "exception_short_message": "Bernard failed due to an exception!",
    "exception_subject": "EXCEPTION: Bernard Encountered an Exception Checking the EMR Cluster!",
    "exception_s3_load_failure_message": "A failure occurred loading the emr_clusters_to_check.json file from S3!"
                                         "The local emr_clusters_to_check.json file will be used instead. Please "
                                         "check the logs for more details.\n\nS3 file location: {}/{}\n\nException: {}",
    "exception_s3_load_failure_subject": "Bernard Exception: Unable to Load Clusters to check from S3!",
    "failed_cluster": "The following cluster terminated with errors: {} \nStatus: {}\n",
    "failure_short_message": "There were failures while checking the EMR cluster status!",
    "failure_subject": "FAILURE: Bernard Encountered Failure while Checking the EMR Cluster!",
    "hung_cluster": "The following EMR Cluster has been hung for more than {} hours: {}\nStatus: {}\n",
    "not_loaded_details": "Failed to load the config file {} due to the following:\n{}\n\nPlease look at the "
                          "logs.",
    "not_loaded_message": "Failed to load the config file, please check logs.",
    "success_details": "Cluster: {} successfully terminated",
    "success_short_message": "All Clusters were terminated successfully!",
    "success_subject": "SUCCESS: EMR Clusters Terminated Properly!",
}

COMEDIAN = {
    "exception_api_details": "Unable to check api quota info. An exception has occurred. Check logs for more detail. ",
    "exception_config_details": "An exception occurred while reading the api_targets config file. "
                                "\n\nTraceback of exception:\n{}",
    "exception_details": "\nThere was an exception retrieving {} quota information.\n\nTraceback of exception:\n{}",
    "exception_quota_details": "\n\"{}\" usage is not being tracked. \nThis could be caused by an issue with the config"
                               " or a None value in the API's response.\nCheck the logs for more information.\n",
    "exception_short_message": "EXCEPTION: Unable to check API quotas, please check logs!",
    "exception_subject": "EXCEPTION: Unable to Check API Quotas!",
    "failure_short_message": "FAILURE: At least one quota was exceeded, please check the logs for more information!",
    "failure_short_message_single": "FAILURE: A quota in {} was exceeded, please check the logs for more information!",
    "failure_subject": "FAILURE: At Least One API Quota Was Exceeded!",
    "failure_subject_single": "FAILURE: A {} Quota Exceeded!",
    "quota_exceeded": "\nQuota \"{}\" exceeded the {:.2f}% threshold!\nPercent Used: {:.2f}%\nUsed: {}, Allowed: {}\n",
    "quota_exception_details": "There is API information missing.\n\n{}",
    "success_details": "All API quota checks ran successfully and were within the current thresholds.",
    "success_details_single": "\n{} quota checks ran successfully and were within the current thresholds.\n",
    "success_short_message": "SUCCESS: All API quota checks were within the threshold for today!",
    "success_short_message_single": "SUCCESS: {} quota checks were within the threshold for today!",
    "success_subject": "SUCCESS: All API Quotas Within Thresholds!",
    "success_subject_single": "SUCCESS: {} Quotas Within Thresholds!",
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

METROPOLIS = {
    "details_format": "{}\n\nMetric_type: {}\nMetric_description: {}\nMetric_value: {}\n{}\n",
    "exception_details": "Process: {}, Source: {} reached an exception on {} trying to get "
                         "watchmenResults.csv" + " from s3 due to the following:\n\n{}\n\nPlease look "
                         "at the logs for more insight.",
    "exception_message": "Metropolis failed due to an exception!",
    "exception_subject": "Metropolis: EXCEPTION Checking Process: {}",
    "failure_details": "Process: {}, Source: {} is down for {}!",
    "failure_exception_message": "Failure and exception checking process metrics.",
    "failure_message": "There were moving_mean values outside of the threshold!",
    "failure_subject": "Metropolis: OUTLIER DETECTED! - Process: {}",
    "generic": "Generic: ",
    "generic_exception_subject": "Metropolis: EXCEPTION Checking Process Metrics",
    "generic_fail_subject": "Metropolis: FAILURE Checking Process Metrics",
    "generic_fail_and_exception_subject": "Metropolis: FAILURE AND EXCEPTION Checking Process Metrics",
    "generic_success_subject": "Metropolis: No Outliers!",
    "min_and_max_message": "Moving Mean: {} || Minimum: {} || Maximum: {}",
    "min_and_max_error_message": "Error: Minimum is larger than maximum.",
    "no_indicator_message": "Indicator {} not present in the {} metrics",
    "not_loaded_details": "Failed to find rows with date of {} in {} due to the following:\n{}\n\nPlease look at the "
                          "logs or check the CSV file for more insight.",
    "not_loaded_message": "Failed to load data from the CSV file, please check logs.",
    "not_loaded_subject": "Metropolis: ERROR Loading Data File!",
    "process_not_in_file": "{} process is missing from the CSV file.",
    "success_details": "Process: {}, Source: {} is up and running for {}!",
    "success_message": "All moving_mean values were inside the threshold!",
    "success_subject": "Metropolis: No Outliers! - {}"
}

MOTHMAN = {
    "exception_details": "There was an exception while trying to check the Malspam MTA S3 files.\n\nTraceback of "
                         "exception:\n{}",
    "exception_subject": "EXCEPTION: Unable to check Malspam MTA S3 files!",
    "success_latest_hm": "Check was skipped due to latest S3 file being 0000.tar.gz.\nFile path: {}",
    "success_previous_file_dne": "Latest S3 file exists, but the previous S3 file does not. A notification"
                                 " should have already been sent for the previous file.\nPrevious file: {}",
    "success_previous_hm": "0010.tar.gz S3 file exists and the previous file is not expected to be uploaded.",
    "success_short_message": "SUCCESS: All expected S3 files exist.",
    "success_subject": "SUCCESS: Malspam MTA files found on S3",
    "success_unequal_files": "Two most recent files exist and are not the same file!\nLatest file: {}\n"
                             "Previous file: {}",
    "failure_latest_file_dne": "Latest file does not exist: {}",
    "failure_equal_files": "The same file was uploaded twice in a row.\nLatest file: {}\nPrevious file: {}",
    "failure_short_message": "FAILURE: S3 file(s) do not exist or files are the same size.",
    "failure_subject": "FAILURE: Malspam MTA S3 Files Error"
}

NITEOWL = {
    "exception_api_failed": "The Github api call failed checking {} for {}\nTraceback:\n{}",
    "exception_api_failed_w_path": "The Github api call failed checking {} for {} on path: {}\nTraceback:\n{}",
    "exception_config_load_failure_details": "Cannot load Github targets from the config",
    "exception_config_load_failure_subject": "EXCEPTION: Cannot load Github Targets!",
    "exception_invalid_check": "Check {} is an invalid check for {}",
    "exception_invalid_event_details": "An invalid event was passed from the CloudWatch event. Check the events in the "
                                       "CloudFormation file.",
    "exception_invalid_event_subject": "EXCEPTION: Niteowl received an invalid event type!",
    "exception_invalid_target_format": "Missing required tags: {}",
    "exception_message": "An exception occurred while checking Github targets. Check the logs for more details.",
}

RORSCHACH = {
    "exception_config_load_failure_details": "Cannot load S3 targets from file: {}\nException: {}",
    "exception_config_load_failure_subject": "EXCEPTION: Unable to Load S3 Targets Config File!",
    "exception_details": "The following S3 paths threw exceptions during their file checks:\n\n{}",
    "exception_invalid_event_details": "An invalid event was passed from the CloudWatch event, please check the "
                                       "CloudFormation file and CloudWatch events to ensure that the correct"
                                       " parameters are being sent. S3 targets can not be checked with an invalid "
                                       "event parameter.",
    "exception_invalid_event_subject": "EXCEPTION: Rorschach Received An Invalid CloudWatch Event!",
    "exception_message": "Exception occurred when checking S3 targets! Please check the logs for more details.",
    "exception_string_format": "Item: {}\nException: {}",
    "exception_subject": "EXCEPTION: Unable to Check S3 files for {}!",
    "failure_bucket_not_found": "FAILURE: The following bucket was not found: {}.\n",
    "failure_details": "The following failures were encountered while performing checks:\n\n{}",
    "failure_event_check": "Invalid event parameter type passed in from Lambda: {}.",
    "failure_exception_message": "FAILURE AND EXCEPTION: S3 file checks could not be performed, please look at the logs"
                                 " for more details!",
    "failure_exception_subject": "FAILURE AND EXCEPTION: Unable to Check S3 files for {}!",
    "failure_file_empty": "The following S3 file is empty: {}",
    "failure_invalid_s3_key": "The following key was not found in S3: {}",
    "failure_invalid_suffix": "The following file(s) did not have the required suffix \"{}\":\n{}",
    "failure_message": "FAILURE: At least one S3 file check did not pass, please check the logs for more details!",
    "failure_multiple_file_size": "The size of all files found in {} is {} KB, which is less than expected"
                                  " total file size {} KB.",
    "failure_no_files": "The following key has NO FILES on S3: {}",
    "failure_single_file_size": "The following file did not meet the {} KB size threshold: {}",
    "failure_subject": "FAILURE: S3 File Checks Failed for {}!",
    "failure_total_objects": "The number of objects found in {} is {}, which is less than expected total objects count:"
                             " {}.",
    "failure_last_modified_date": "FAILURE: S3 Target file {} has not been updated during {}",
    "generic_exception_subject": "EXCEPTION: At Least One S3 Target Has An Exception!",
    "generic_failure_exception_subject": "EXCEPTION and FAILURE: At Least One S3 Target Has An Exception and Failure!",
    "generic_failure_subject": "FAILURE: At Least One S3 Target Has Failed!",
    "generic_success_subject": "SUCCESS: All S3 Targets Passed!",
    "success_details": "All of the S3 file checks for the {} target passed successfully!",
    "success_event_check": "The event parameter passed in from Lambda is valid.",
    "success_message": "SUCCESS: All S3 File Checks passed!",
    "success_subject": "SUCCESS: All S3 File Checks for {} Passed!",
}

SILHOUETTE = {
    "exception_message": "Silhouette for lookalike2 algorithm failed on \n\t\"{}\" \ndue to "
                         "the Exception:\n\n{}\n\nPlease check the logs!",
    "exception_short_message": "Silhouette for lookalike2 algorithm failed due to an exception, please check the logs!",
    "exception_subject": "EXCEPTION: Silhouette failed to check the Lookalike2 algorithm!",
    "failure_message": "Lookalike2 algorithm never added files yesterday! "
                       "The algorithm may be down or simply did not complete!",
    "failure_subject": "FAILURE: Silhouette detected an issue with the Lookalike2 algorithm!",
    "success_message": "Lookalike2 algorithm is up and running!",
    "success_subject": "Silhouette: Lookalike2 files have been successfully detected in S3!"
}

SPECTRE = {
    "exception_message": "Spectre for Georgia Tech failed on \n\t\"{}\" \ndue to "
                         "the Exception:\n\n{}\n\nPlease check the logs!",
    "exception_short_message": "Spectre monitor failed due to an exception, check S3 and Georgia Tech logs!",
    "exception_subject": "Spectre for Georgia Tech had an exception!",
    "failure_message": "could not be found in {}/{}! "
                       "Please check S3 and Georgia Tech logs!",
    "failure_short_message": "Spectre monitor failed, please check S3 and Georgia Tech logs!",
    "failure_subject_message": "Spectre Georgia Tech data monitor detected a failure!",
    "file_not_found_error": " not found on S3 in {}/{}! Georgia Tech data is missing, "
                            "please view the logs!",
    "success_message": "Georgia Tech Feed data found on S3!",
    "success_subject": "Spectre Georgia Tech data monitor found everything alright. "
}
