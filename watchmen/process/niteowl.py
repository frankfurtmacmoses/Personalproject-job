"""
Created May 2021

This watchman is designed to check for updates to Github Repos specified in the config, github_targets.yaml.
Currently the checks that can be performed are for new commits and new releases. This watchman makes use of the Github
util to check on repos and is limited to 5000 requests per hour for authenticated users (user token is passed)
and 60 requests per hour for unauthenticated users (no user token is passed). A failure represents an update, or change
to a repo. An exception represents an error that occurred in the code, or that occurred during a Github checks.

@author: Phillip Hecksel
@email: phecksel@infoblox.com
"""

import datetime
import os
import traceback
import yaml

from watchmen import const, messages
from watchmen.common.result import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings
from watchmen.utils import github

CONFIG_NAME = settings('niteowl.targets')
DAILY = "Daily"
GITHUB_TOKEN = settings('niteowl.github_token')
MESSAGES = messages.NITEOWL
REQUIRED_TARGET_TAGS = ['target_name', 'owner', 'repo', 'checks']
TARGET_ACCOUNT = settings("TARGET_ACCOUNT", "atg")

CONFIG_PATH = os.path.join(
    os.path.realpath(os.path.dirname(__file__)), 'configs', CONFIG_NAME)
EVENT_OFFSET_PAIR = {DAILY: 'days'}
GENERIC_TARGET = 'Generic Github {}'.format(TARGET_ACCOUNT)


class Niteowl(Watchman):

    def __init__(self, event, context):
        """
        Niteowl Constructor
        """
        super().__init__()
        self.event = event.get('Type')

    def monitor(self):
        """
        Monitors Github Targets in the github_targets.yaml file
        :return: <List> A list of result objects from the checks performed on each target.
        """

        if not self._is_valid_event():
            return self._create_invalid_event_result()

        github_targets, tb = self._load_config()
        if tb:
            return self._create_config_not_loaded_result()

        processed_targets = self._process_targets(github_targets)
        summary_parameters = self._create_summary_parameters(processed_targets)
        results = self._create_results(summary_parameters)
        return results

    def _calculate_since_date(self, time_offset=1, offset_type=None):
        """
        Creates a date that is a specified distance from the current date. This is used to check github changes within a
        window of time.
        :param time_offset: <int> The number of offset_type's to go backwards. Defaults to 1.
        :param offset_type: <str> The unit of the time_offset (Ex: Daily). Defaults to the event type.
        :return: <Datetime> A Datetime object representing a date in the past.
        """
        offset_type = self.event if not offset_type else offset_type
        date = (datetime.datetime.utcnow() - datetime.timedelta(**{EVENT_OFFSET_PAIR[offset_type]: time_offset})) \
            .replace(microsecond=0)
        return date

    def _check_commits(self, target):
        """
        This checks for new git commits from the target and returns a formatted summary of them if they exist.
        :param target: <dict> The target's entry in github_targets.yaml
        :return: <list> new_commit_strings are formatted messages for any new git commits
                 <list> exception_strings are messages for any errors encountered
        """
        repo = target.get('repo')
        owner = target.get('owner')
        time_offset = target.get('time_offset', 1)
        offset_type = target.get('offset_type')
        since_date = self._calculate_since_date(time_offset, offset_type)
        new_commit_strings, exception_strings = [], []

        if target.get('target_path'):
            new_commits, exceptions = self._get_new_commits(target.get('target_name'), repo, owner, since_date,
                                                            target.get('target_path'))
        else:
            new_commits, exceptions = self._get_new_commits(target.get('target_name'), repo, owner, since_date)

        new_commit_strings.extend(new_commits)
        exception_strings.extend(exceptions)

        return new_commit_strings, exception_strings

    def _check_releases(self, target):
        """
        This checks for new releases for the target within the specified time window (default is 1 of the event type).
        :param target: <dict> The target's entry in github_targets.yaml
        :return: <list> new_release_strings are formatted messages for any new releases
                 <list> exception_strings are messages for any errors encountered
        """
        repo = target.get('repo')
        owner = target.get('owner')
        time_offset = target.get('time_offset', 1)
        offset_type = target.get('offset_type')
        since_date = self._calculate_since_date(time_offset, offset_type)

        new_release_strings, exception_strings = [], []

        current_release, tb = github.get_repository_release(owner=owner, repo=repo, token=GITHUB_TOKEN)
        if tb:
            exception_strings.append(self._format_api_exception('releases', target.get('target_name'), tb))
            return new_release_strings, exception_strings

        release_date = datetime.datetime.fromisoformat(current_release.get('published_at')[:-1])

        if release_date >= since_date:
            new_release_strings.append(MESSAGES.get('new_release').format(
                name=current_release.get('name'), date=release_date, url=current_release.get('url')
            ))

        return new_release_strings, exception_strings

    def _create_config_not_loaded_result(self):
        """
        Creates a Result object for if the config cannot be loaded.
        :return: <list> A result object for the config error
        """
        return [Result(
            details=MESSAGES.get("exception_config_load_failure_details"),
            disable_notifier=False,
            short_message=MESSAGES.get("exception_message"),
            snapshot={},
            state=Watchman.STATE.get("exception"),
            subject=MESSAGES.get("exception_config_load_failure_subject"),
            success=False,
            target=GENERIC_TARGET,
            watchman_name=self.watchman_name,
        )]

    @staticmethod
    def _create_details(processed_target):
        """
        Creates details for the result objects from the new_change_strings and exception_strings if they exist.
        :param processed_target: <dict> A dictionary of the target name with any failures or exceptions that occurred
        :return: <str> A details string for the target with information from the checks performed
        """
        target_name = processed_target.get('target_name')

        if processed_target.get('success'):
            return MESSAGES.get("success_details").format(target_name)

        details = ''
        if processed_target.get("exception_strings"):
            all_exceptions_string = "\n\n".join(processed_target.get("exception_strings"))
            details += MESSAGES.get("exception_details").format(target_name, all_exceptions_string) + "\n\n"

        if processed_target.get('new_changes_strings'):
            all_changes_string = "\n\n".join(processed_target.get("new_changes_strings"))
            details += MESSAGES.get("change_detected_details").format(target_name, all_changes_string) + "\n\n"

        return details

    def _create_invalid_event_result(self):
        """
        Creates a result object for if the event type is invalid
        :return: <list> A Result object for an invalid event type
        """
        return [Result(
            details=MESSAGES.get("exception_invalid_event_details"),
            disable_notifier=False,
            short_message=MESSAGES.get("exception_message"),
            snapshot={},
            state=Watchman.STATE.get("exception"),
            subject=MESSAGES.get("exception_invalid_event_subject"),
            success=False,
            target=GENERIC_TARGET,
            watchman_name=self.watchman_name,
        )]

    def _create_results(self, summary_parameters):
        """
        This creates result objects for each of the summary parameters and a generic result for all of them. These will
        then be sent to subscribers of the corresponding sns topics.
        :param summary_parameters: <list<dict>>  The parameters needed to make each Result object.
        :return: <list> Result objects for each summary parameter, as well as a generic result object that represents
            all results.
        """
        results = []
        generic_result_details = ''
        change_detected = False
        exception = False
        for parameters in summary_parameters:
            success = parameters.get("success")

            if success is False:
                change_detected = True
            if success is None:
                exception = True

            if not success:
                generic_result_details += "{}{}\n\n".format(parameters.get("details"), const.MESSAGE_SEPARATOR)

            results.append(Result(
                details=parameters.get("details"),
                disable_notifier=parameters.get("disable_notifier"),
                short_message=parameters.get("short_message"),
                snapshot={},
                state=parameters.get("state"),
                subject=parameters.get("subject"),
                success=success is True,
                target=parameters.get("target"),
                watchman_name=self.watchman_name,
            ))
        results.append(self._create_generic_result(change_detected, exception, generic_result_details))
        return results

    def _create_generic_result(self, change_detected, exception, details):
        """
        This creates the generic result object which contains information from all checks performed for all targets.
        :param change_detected: <bool> True if there was a change detected during a github check
        :param exception: <bool> True if an exception occurred during a github check
        :param details: <str> A string with all the messages generated from each check
        :return: <Result> A result with all targets check information
        """
        if change_detected and exception:
            disable_notifier = False
            short_message = MESSAGES.get("change_detected_exception_message")
            state = Watchman.STATE.get("exception")
            subject = MESSAGES.get("generic_change_detected_exception_subject")
            success = False

        elif exception:
            disable_notifier = False
            short_message = MESSAGES.get("exception_message")
            state = Watchman.STATE.get("exception")
            subject = MESSAGES.get("generic_exception_subject")
            success = False

        elif change_detected:
            disable_notifier = False
            short_message = MESSAGES.get("change_detected_message")
            state = Watchman.STATE.get("failure")
            subject = MESSAGES.get("generic_change_detected_subject")
            success = False

        else:
            disable_notifier = True
            short_message = MESSAGES.get("success_message")
            state = Watchman.STATE.get("success")
            subject = MESSAGES.get("generic_success_subject")
            success = True

        return Result(
            details=details,
            disable_notifier=disable_notifier,
            short_message=short_message,
            snapshot={},
            watchman_name=self.watchman_name,
            state=state,
            subject=subject,
            success=success,
            target=GENERIC_TARGET,
        )

    def _create_summary_parameters(self, processed_targets):
        """
        Create the parameters needed for result objects based on the checks performed for each target.
        :param processed_targets: <list<dict>> Dictionaries of information from each check performed on a target
        :return: <list<dict>> Returns a dictionary for every processed target that has the parameters needed to create
            the result object for that target
        """
        summary_parameters = []
        parameter_chart = {
            None: {
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
                "success": None
            },
            True: {
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "success": True
            },
            False: {
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "success": False
            }
        }

        for target in processed_targets:
            target_name = target.get('target_name')
            success = target.get('success')
            parameters = parameter_chart.get(success).copy()
            parameters.update({'target': target_name, 'details': self._create_details(target)})

            if success:
                parameters.update({"short_message": MESSAGES.get("success_message")})
                parameters.update({"subject": MESSAGES.get("success_subject").format(target_name)})
            elif target.get('success') is None:
                parameters.update({"short_message": MESSAGES.get("exception_message")})
                parameters.update({"subject": MESSAGES.get("exception_subject").format(target_name)})
            else:
                # If there are exceptions and failures:
                if target.get("exception_strings"):
                    parameters.update({"short_message": MESSAGES.get("change_detected_exception_message")})
                    parameters.update({"subject": MESSAGES.get("change_detected_exception_subject")
                                      .format(target_name)})
                else:
                    parameters.update({"short_message": MESSAGES.get("change_detected_message")})
                    parameters.update({"subject": MESSAGES.get("change_detected_subject").format(target_name)})

            summary_parameters.append(parameters)

        return summary_parameters

    @staticmethod
    def _format_api_exception(check_name, target_name, tb, path=None):
        """
        Returns an exception string with information about a Github API Failure
        :param check_name: <str> Name of the check that threw the exception
        :param target_name: <str> The target name
        :param tb: <str> The traceback of the exception
        :param path: <str> The path the exception occurred on, if applicable
        :return: <str> An message with information from the API exception
        """
        if path:
            return MESSAGES.get("exception_api_failed_w_path").format(check_name, target_name, path, tb)

        return MESSAGES.get("exception_api_failed").format(check_name, target_name, tb)

    @staticmethod
    def _format_commits(commits):
        """
        Method to help format the returned commits from the call to the github util to a readable message
        :param commits: <list<dict>> A list of commits returned from the _get_repo_commits
        :return: <list<str>> A list of strings which contain information about each new commit
        """
        formatted_commits = []
        for commit in commits:
            formatted_commits.append(MESSAGES.get('new_commit').format(
                date=commit.get('commit').get('author').get('date'),
                sha=commit.get('sha'),
                message=commit.get('commit').get('message'),
                url=commit.get('html_url')
            ))
        return formatted_commits

    def _get_new_commits(self, target_name, repo, owner, since_date, paths=[None]):
        """
        Calls the get_repository_commits method from the Github util, then formats the results.
        :param repo :<str> The name of the github repository to check
        :param target_name: <str> The name of the target
        :param owner: <str> The owner of the repository
        :param since_date: <datetime> A Datetime object to start checking for new commits from.
        :param paths: <List<str>> A list of paths to check for new commits on if there is no need to check the entire
                        repo.
        :return: <list<str>> A list of every new commit since the since_date.
                 <list<str>> Any exceptions that occurred when checking new commits
        """
        new_commit_strings = []
        exception_strings = []

        for path in paths:
            new_commits, tb = github.get_repository_commits(
                owner=owner, repo=repo, since=since_date, token=GITHUB_TOKEN, path=path)

            if tb:
                exception_strings.append(self._format_api_exception('commits', target_name, tb, path))
                return new_commit_strings, exception_strings

            new_commit_strings.extend(self._format_commits(new_commits))

        return new_commit_strings, exception_strings

    def _is_valid_event(self):
        """
        A check to make sure the event is supported by niteowl
        :return: if the event is in the list of time offsets used for performing github checks
        """
        return self.event in list(EVENT_OFFSET_PAIR.keys())

    def _load_config(self):
        """
        Loads github_targets.yaml and returns the targets for the event type.
        :returns: <list<dict>> A list of targets with the needed information
        """
        try:
            with open(CONFIG_PATH) as f:
                github_targets = yaml.load(f, Loader=yaml.FullLoader).get(self.event)
            return github_targets, None
        except Exception as ex:
            self.logger.error("ERROR Loading Config!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _process_targets(self, github_targets):
        """
        This method validates the target config entry, then performs the requested checks and creates a processed
        target dictionary from the new_change_strings and exception strings.
        :param github_targets: <list<dict>> The config entries for each target
        :returns: <list<dict>> processed_targets will contain the information gathered from each check performed.
                Format: {
                            'target_name': str
                            'success': boolean
                            'exception_strings': [str]
                            'new_changes_strings': [str]
                        }
        """
        processed_targets = []
        for target in github_targets:
            new_change_strings = []
            exception_strings = []

            is_valid, missing_string = self._validate_target_entry(target)

            if is_valid:
                for target_check in target.get('checks'):
                    new_changes, exceptions = self._run_check(target_check, target)

                    new_change_strings.extend(new_changes)
                    exception_strings.extend(exceptions)
            else:
                exception_strings.append(missing_string)

            processed_targets.append({
                'target_name': target.get('target_name'),
                'success': None if exception_strings and not new_change_strings else not new_change_strings,
                'exception_strings': exception_strings,
                'new_changes_strings': new_change_strings
            })

        return processed_targets

    def _run_check(self, check_name, target):
        """
        This will find the method to perform a specific check based on the check_name. Ex: the Commits check will be
        mapped to the _check_commits function
        :param check_name: <str> The name of the check to make.
        :param target: <dict> The target's config entry
        :return: The check function's result
        """
        try:
            source_function = getattr(self, '_check_{}'.format(check_name.lower()))
            return source_function(target)
        except Exception as ex:
            self.logger.error("ERROR retrieving {} check function!".format(check_name))
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            exception = [MESSAGES.get('exception_invalid_check').format(check_name, target.get('target_name'))]
            return [], exception

    @staticmethod
    def _validate_target_entry(target):
        """
        Checks the target config entry for required tags to make the github api call.
        :param target: <dict> The target's config entry
        :return: <bool> if the entry is valid,
                 <str> A missing message if a tag is missing
        """
        is_valid, missing, message = True, [], ''
        for tag in REQUIRED_TARGET_TAGS:
            if not target.get(tag):
                is_valid = False
                missing.append(tag)
        if missing:
            message = MESSAGES.get("exception_invalid_target_format").format(missing)
        return is_valid, message



