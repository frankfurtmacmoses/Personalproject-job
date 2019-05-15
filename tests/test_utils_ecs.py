"""
Unit tests for watchmen/utils/ecs.py

@author: Jason Zhu
@email: jason_zhuyx@hotmail.com

Refactored on May 15, 2019
@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import pytz
import unittest
from moto import mock_ecs
from mock import patch
from datetime import datetime
from watchmen.utils.ecs import get_stuck_ecs_tasks


class TestECS(unittest.TestCase):

    @mock_ecs
    @patch('boto3.client')
    @patch('watchmen.utils.ecs.datetime')
    def test_get_stuck_ecs_tasks(self, mock_dt, mock_client):
        mock_dt.now.return_value = datetime(
            year=2019, month=5, day=6, hour=5, minute=5, second=5, tzinfo=pytz.utc
        )
        tests = [
            {
                'describe_tasks': {},
                'tasks_arns': {},
                'expected': []
            },
            {
                'describe_tasks': {'tasks': []},
                'tasks_arns': {
                    'taskArns': 'item'
                },
                'expected': []
            },
            {
                'describe_tasks': {
                    'tasks': [
                        {
                            'createdAt': datetime(
                                year=2019, month=5, day=6, hour=4, minute=5, second=5, tzinfo=pytz.utc
                            ),
                            'name': 'the_feed_of_all_feeds'
                        }
                    ]
                },
                'tasks_arns': {'taskArns': 'item'},
                'expected': []
            },
            {
                'describe_tasks': {
                    'tasks': [
                        {
                            'createdAt': datetime(
                                year=2019, month=5, day=5, hour=4, minute=5, second=5, tzinfo=pytz.utc
                            ),
                            'task': 'greatest_feed_ever'
                        }
                    ]
                },
                'tasks_arns': {'taskArns': 'item'},
                'expected': [
                    {
                        'createdAt': datetime(
                            year=2019, month=5, day=5, hour=4, minute=5, second=5, tzinfo=pytz.utc
                        ),
                        'task': 'greatest_feed_ever'
                    }
                ]
            },
        ]
        for test in tests:
            mock_client.return_value.list_tasks.return_value = test.get('tasks_arns')
            mock_client.return_value.describe_tasks.return_value = test.get('describe_tasks')
            result = get_stuck_ecs_tasks('cluster')
            self.assertEqual(test.get('expected'), result)
