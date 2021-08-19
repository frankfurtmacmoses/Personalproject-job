"""
Common library for accessing Dremio's API

authors: lpeaslee, vcollooru
"""

import logging
import requests


class Dremio:

    def __init__(self, dremio_root_url, user_name, secret_value):
        '''
        dremio_root_url: Root url of Dremio end point
        user_name: User account to access Dremio
        secret_value: Passcode for the user account
        '''
        self.dremio_root_url = dremio_root_url
        self.user_name = user_name
        self.secret_value = secret_value
        self.dremio_login_url = f"https://{dremio_root_url}/apiv2/login"
        self.dremio_sql_url = f"https://{dremio_root_url}/api/v3/sql"

    def generate_auth_token(self):
        """
        Generates the auth token for communication with Dremio
        """
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }

        response = requests.post(self.dremio_login_url,
                                 json={"userName": self.user_name,
                                       "password": self.secret_value},
                                 headers=headers)

        logging.info(f" Response from Dremio Generate Token {str(response)}")

        # Grab authorization token from response
        # Grab authorization token from response
        if 'token' in response.json():
            return "_dremio" + response.json()['token']

        return None

    def metadata_refresh(self, token, pds_path):
        '''
        Posts a metadata refresh for the PDS passed

        token: Auth token for Dremio
        pds_path: Full path of the PDS
        '''
        logging.info(self.dremio_sql_url)
        sql_string = f'ALTER PDS {pds_path} REFRESH METADATA'
        logging.info(sql_string)
        body = {
            "sql": sql_string
        }
        headers = {
            'Authorization': token,
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }
        response = requests.post(self.dremio_sql_url, json=body, headers=headers)
        logging.info(f" Response from Dremio Metadata Refresh {str(response)}")

    def dremio_catalog_lookup(self, refresh, token, catalog_url):
        """
        GET request to find out the id of the asset we want to refresh
        in dremio based on the asset path

        refresh: path to the asset at the end of the catalog url
        token: Auth token for Dremio
        catalog_url: string with tokens present for catalog url
        """
        url = catalog_url.format(root=self.dremio_root_url, path=str(refresh))
        logging.info(url)
        headers = {
            'Authorization': token,
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }

        response = requests.get(url, headers=headers)

        logging.info(f" Response from Dremio Catalog Lookup {str(response)}")
        if 'id' in response.json():
            return response.json()['id']

        return None

    def dremio_refresh_asset(self, asset_id, token, refresh_url):
        """
        POST to refresh the dremio asset by id

        asset_id: key value for the asset to refresh
        token: Auth token for Dremio
        refresh_url: URL string with tokens to refresh
        """
        url = refresh_url.format(root=self.dremio_root_url, id=str(asset_id))
        logging.info(url)
        payload = ""
        headers = {
            'Authorization': token,
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }

        response = requests.post(url, data=payload, headers=headers)

        logging.info(f" Response from Dremio Refresh {str(response)}")
