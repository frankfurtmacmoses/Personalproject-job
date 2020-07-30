"""
Created on June 30, 2020

Module containing functions for AWS EMR

@author Deemanth H L
@email dhl@infoblox.com

"""
import boto3
from datetime import datetime, timedelta


def get_emr_clusters_for_day():
    """
    Lists the EMR clusters running for past 24 hrs from current time.
    @param cluster_state: List of cluster state to be retrieved
    :return: list of clusters
    """
    emr_client = boto3.client('emr')

    clusters_list = []
    # Created from past 24 hrs
    time = datetime.utcnow() - timedelta(days=1)
    clusters_list = emr_client.list_clusters(
        CreatedAfter=time
    )
    return clusters_list.get('Clusters')
