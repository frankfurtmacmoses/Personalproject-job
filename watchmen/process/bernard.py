"""
Created on July 21, 2020
This script is designed to monitor EMR clusters within the atg-infoblox account that are for production usage.
The clusters that run using steps which would require monitoring of total failure shutting down the cluster and
cluster running much longer than necessary -  step clusters.
@author: Deemanth
@email: dhl@infoblox.com

"""
import json
import traceback

from watchmen import const
from watchmen import messages
from watchmen.common.result import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings
from watchmen.utils.emr import get_emr_clusters_for_day
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.s3 import get_content

EMR_TARGET = "EMR Cluster Status"
JSON_FILE = settings('bernard.json_file')
MESSAGES = messages.BERNARD
SNS_TOPIC_ARN = settings("bernard.sns_topic", "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")
S3_BUCKET = settings('bernard.s3_bucket', 'cyber-intel-test')
S3_PREFIX = settings('bernard.s3_prefix')
THRESHOLD_TIME_HRS = settings("bernard.hour_threshold", 12)


class Bernard(Watchman):
    """
    class of Bernard
    """
    def __init__(self, event, context):
        """
        constructor of Bernard
        """
        super().__init__()

    def monitor(self) -> [Result]:
        """
        Monitors the emr clusters running using steps.
        @return: <Result> List of Result objects
        """

        clusters_to_check, tb = self._load_clusters_to_check()
        if not clusters_to_check:
            details = MESSAGES.get("not_loaded_details").format(JSON_FILE, tb)
            parameters = self._create_result_parameters(None, details)
            result = self._create_result(parameters)
            return result

        # Get the list of clusters for clusters running steps
        step_clusters_list = self._get_emr_clusters()
        # Check against failure or hung clusters
        cluster_check_info = self._check_step_clusters(clusters_to_check, step_clusters_list)

        parameters = self._create_result_parameters(cluster_check_info.get("success"),
                                                    cluster_check_info.get("details"))
        # Create result object
        result = self._create_result(parameters)

        return result

    def _check_successful_cluster_termination(self, cluster, cluster_check_info):
        """
        Checks for failed cluster.
        :param cluster: <dict> Dictionary of cluster details
        :param cluster_check_info <dict> Dictionary containing information about the cluster check
        :return: <bool>
        <bool> whether cluster has terminated properly or not
        <str> traceback
        """
        try:
            if cluster.get('Status').get('State') == 'TERMINATED_WITH_ERRORS':
                failed_details = MESSAGES.get("failed_cluster").format(cluster.get('Name'),
                                                                       cluster.get('Status').get('StateChangeReason'))
                self._update_cluster_check_info(failed_details, False, cluster_check_info)
                return False
            return True
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()

            self._update_cluster_check_info(tb, None, cluster_check_info)
            return None

    def _check_cluster_runtime(self, cluster, cluster_check_info):
        """
        Checks for cluster running more than the threshold time defined(emr_clusters_to_check.json)
        :param cluster: <dict> Dictionary of cluster details
        :param cluster_check_info <dict> Dictionary containing information about the cluster check
        """
        try:
            timeline = cluster.get('Status').get('Timeline')
            delta_time = timeline.get('EndDateTime') - timeline.get('CreationDateTime')
            # Stores number of hours the cluster is been running
            elapsed_time = int(delta_time.total_seconds()/3600)
            if elapsed_time > THRESHOLD_TIME_HRS:
                hung_details = MESSAGES.get("hung_cluster").format(THRESHOLD_TIME_HRS, cluster.get('Name'),
                                                                   cluster.get('Status').get('State'))
                self._update_cluster_check_info(hung_details, False, cluster_check_info)
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()

            self._update_cluster_check_info(tb, None, cluster_check_info)

    def _check_step_clusters(self, clusters_to_check, clusters_list):
        """
        Checks for failed and hung clusters running through steps. Creates detils of the failure/hung
        :param clusters_to_check: <list> Clusters to check from list of clusters retrieved for a day.
        :param clusters_list: <list> list of cluster dictionaries.
        :return: Dictionary containing information about the cluster check. "success" indicates the result of checking
        all the clusters. The "details" is a properly formatted string of all the clusters that are terminated  with
        errors or hung for defined threshold time.
        """
        cluster_check_info = {
            "success": True,
            "details": ""
        }

        for cluster in clusters_list:
            if cluster.get('Name') in clusters_to_check:
                # Check for failed cluster
                failed_cluster_check = self._check_successful_cluster_termination(cluster, cluster_check_info)

                # Check for hung cluster
                if failed_cluster_check:
                    self._check_cluster_runtime(cluster, cluster_check_info)

        return cluster_check_info

    def _create_result(self, parameters):
        """
        Creates and returns list of the Result object. This list includes the Result object EMR clusters.
        :param parameters: Dictionary of Result attributes corresponding to the result of the EMR Clusters check.
        :return: List of Result object: [ result ]
        """
        result = Result(
            details=parameters.get("details"),
            disable_notifier=parameters.get("disable_notifier"),
            short_message=parameters.get("short_message"),
            snapshot=parameters.get("snapshot"),
            watchman_name=self.watchman_name,
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            success=parameters.get("success"),
            target=EMR_TARGET,
        )
        return [result]

    def _create_result_parameters(self, cluster_check, cluster_details):
        """
        Creates a dictionary that includes:
            success: whether the cluster is terminated successful
            disable_notifier: whether we should disable the notifier
            state: state of result
            subject: subject for long notification
            short_message: short message describing whether the target is considered successful
            target: The SNS topic that will be notified if an exception or failure occurred.
        :param cluster_check: <bool> result of checking the cluster, None upon exception
        :param cluster_details: <str> details on cluster check result
        :param cluster_list: <dict> dictionary of Cluster list
        :return: <dict> parameters for creating results
        """
        parameter_chart = {
            None: {
                "details": cluster_details,
                "disable_notifier": False,
                "short_message": MESSAGES.get("exception_short_message"),
                "snapshot": {},
                "state": Watchman.STATE.get("exception"),
                "subject": MESSAGES.get("exception_subject"),
                "success": False,
            },
            True: {
                "details": MESSAGES.get("success_details"),
                "disable_notifier": True,
                "short_message": MESSAGES.get("success_short_message"),
                "snapshot": {},
                "state": Watchman.STATE.get("success"),
                "subject": MESSAGES.get("success_subject"),
                "success": True,
            },
            False: {
                "details": cluster_details,
                "disable_notifier": False,
                "short_message": MESSAGES.get("failure_short_message"),
                "snapshot": {},
                "state": Watchman.STATE.get("failure"),
                "subject": MESSAGES.get("failure_subject"),
                "success": False,
            },
        }
        parameters = parameter_chart.get(cluster_check)
        return parameters

    def _get_emr_clusters(self):
        """
        Retrieves the list of clusters for a day.
        @return: <step_clusters_list> List of clusters started since 24 hrs
        """
        step_clusters_list = get_emr_clusters_for_day()

        return step_clusters_list

    def _load_clusters_to_check(self):
        """
        Load clusters to check from config file
        @return: <dict> a dictionary including clusters to check
        @return: <str> error message
        """
        key_name = "{}/{}".format(S3_PREFIX, JSON_FILE)
        try:
            data = get_content(key_name=key_name, bucket=S3_BUCKET)
            clusters_dict = json.loads(data)
            step_clusters = clusters_dict.get("step_clusters")
            step_cluster_list = [item.get("cluster_name") for item in step_clusters if item.get("cluster_name")]
            return step_cluster_list, None
        except Exception as s3_exception:
            try:
                # If the file could not be loaded from S3 send an alert, but still attempt to load the local
                # (potentially out of date) file.
                short_message = MESSAGES.get("exception_s3_load_failure_message").format(S3_BUCKET, key_name,
                                                                                         type(s3_exception).__name__)
                self.logger.error(short_message)
                raise_alarm(topic_arn=SNS_TOPIC_ARN, msg=short_message,
                            subject=MESSAGES.get("exception_s3_load_failure_subject"))

                with open(JSON_FILE) as file:
                    clusters_dict = json.load(file)

                step_clusters = clusters_dict.get("step_clusters")
                step_cluster_list = [item.get("cluster_name") for item in step_clusters if item.get("cluster_name")]
                return step_cluster_list, None

            except Exception as local_load_exception:
                # If the local file could not be loaded, then return the traceback message. SNS alerts with exceptions
                # will be sent.
                short_message = MESSAGES.get("exception_local_load_failure_message").format(
                    JSON_FILE, type(local_load_exception).__name__)
                self.logger.error(short_message)
                return None, short_message

    def _update_cluster_check_info(self, details, status, cluster_check_info):
        """
        Checks for cluster running more than the threshold time defined(emr_clusters_to_check.json)
        :param details: <str> details on cluster check result
        :param status: <bool> result of checking the cluster, None upon exception
        :param cluster_check_info: <dict> Dictionary containing information about the cluster check.
        """
        cluster_check_info["details"] += (details + "\n\n")
        cluster_check_info["success"] = status
