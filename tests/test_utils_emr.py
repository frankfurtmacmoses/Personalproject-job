"""
Unit tests for watchmen/utils/emr.py

@author Deemanth
@email dhl@infoblox.com
"""
import unittest
from mock import patch
from moto import mock_emr

from watchmen.utils.emr import get_emr_clusters_for_day


class TestEMR(unittest.TestCase):

    def setUp(self):
        self.example_list_clusters = {'Clusters': [{'Id': 'j-3BEYCAG31GW3J', 'Name': 'JupyterCluster'}]}
        self.example_list_clusters_empty = {}

    @mock_emr
    @patch('boto3.client')
    def test_get_clusters_for_day(self, mock_client):
        """
        watchmen.utils.emr :: get_clusters_for_day()
        """
        tests = [{
            "list_cluster_return": self.example_list_clusters,
            "expected": [{'Id': 'j-3BEYCAG31GW3J', 'Name': 'JupyterCluster'}],
        }, {
            "list_cluster_return": self.example_list_clusters_empty,
            "expected": None
        }]
        for test in tests:
            mock_client.return_value.list_clusters.return_value = test.get("list_cluster_return")
            result = get_emr_clusters_for_day()
            self.assertEqual(test.get("expected"), result)
