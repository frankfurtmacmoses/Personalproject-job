"""
This file contains all the messages for each Watchmen. Messages include details, short messages returned to lambdas, and
the subject of emails.

@author: Michael Garcia
@email: garciam@infoblox.com
"""

MOTHMAN = {
    "exception": "S3 file checks were unsuccessful due to an exception! Please check the logs for more information.",
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
