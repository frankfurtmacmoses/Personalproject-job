"""
Created on April 30, 2021
watchmen/common/storage_service.py
This class is used to store Watchmen Result objects. At the moment, it only stores Results in S3.
@author: Saba Farheen
@email: sfarheen@infoblox.com
"""
# python imports
import datetime
import json

from watchmen.config import LOGGER, settings
from watchmen.utils.s3 import create_key

FOLDER = settings('storage_service.s3_prefix')
NOW = datetime.datetime.utcnow()


class StorageService:
    """
    class of StorageService
    """

    def __init__(self):
        """
        Constructor of StorageService class
        """
        pass

    def save_results(self, results, bucket):
        """
        This method is used to save the obtained result objects.
        @param bucket: <str> Name of the bucket to store the results.
        """
        return self._save_to_s3(results, bucket)

    @staticmethod
    def _save_to_s3(results, bucket):
        """
        This is a private method used to store the obtained result objects in an s3 file.
        Example s3 file path: cyber-intel-test/watchmen/results/2021/06/16/.
        Example file name: 2021-06-1606:13:07.102614.json
        @param results: <list> Result Object.
        @param bucket: <str> Name of the bucket to store the results.
        """
        try:
            data = []  # data is a list used to store all the result objects.
            for result in results:
                data.append(result.to_dict())
            s3_prefix = FOLDER.format(NOW.strftime('%Y'), NOW.strftime('%m'), NOW.strftime('%d'), NOW.strftime('%Y-%m-%d%X.%f'))
            result_data = json.dumps(data, indent=4)  # data is converted to json form to get an organised output.
            create_key(result_data, s3_prefix, bucket=bucket)
        except Exception as ex:
            LOGGER.exception('{}'.format(ex))
