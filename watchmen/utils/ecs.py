"""
Created on July 17, 2018

Module containing functions for AWS ECS

@author Daryan Hanshew
@email dhanshew@infoblox.com

Refactored on May 15, 2019
@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import pytz
import boto3
from logging import getLogger
from datetime import datetime, timedelta

LOGGER = getLogger(__name__)


def get_stuck_ecs_tasks(cluster_name, hour_cap=12):
    """
    Check if an ECS task is "stuck"
    @param cluster_name: Name of the cluster to check
    @param hour_cap: The amount of hours marking when a feed is stuck
    :return: list of stuck tasks
    """
    ecs_client = boto3.client('ecs')

    stuck_tasks = []
    list_tasks = ecs_client.list_tasks(
        cluster=cluster_name,
        desiredStatus='RUNNING'
    )
    tasks_arns = list_tasks.get('taskArns')
    if tasks_arns:
        described_tasks = ecs_client.describe_tasks(
            cluster=cluster_name,
            tasks=tasks_arns
        )
        tasks = described_tasks.get('tasks')
        LOGGER.info(tasks)
        now = datetime.now(tz=pytz.utc)
        if tasks:
            for task in tasks:
                time_elapsed = now - task.get('createdAt')
                if time_elapsed > timedelta(hours=hour_cap):
                    stuck_tasks.append(task)
    LOGGER.info('Stuck tasks: ' + str(stuck_tasks))
    return stuck_tasks
