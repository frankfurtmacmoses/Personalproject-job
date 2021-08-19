import json
import requests
from datetime import date,datetime, timedelta
from dateutil import parser as date_parser
import urllib.parse as u
import time
import argparse

dremioServer = 'dremio-stg.sdp.infoblox.com:9047'
dremio_sql_url = f"https://{dremioServer}/api/v3/sql"
dremio_job_url = f"https://{dremioServer}/api/v3/job"
dremio_catalog_bypath_url = f"https://{dremioServer}/api/v3/catalog/by-path"
dremio_catalog_url = f"https://{dremioServer}/api/v3/catalog"
dremio_reflection_url = f"https://{dremioServer}/api/v3/reflection"
dremio_login_url = f"https://{dremioServer}/apiv2/login"

wait_time = 60
max_wait_time = 600

dremio_source_path = "ib-dl-saas-rz-prod/dns-tagged-history/bitaa-refined-common/year={dt_y}/month={dt_m}/day={dt_d}"
dremio_pds_path = '"ib-dl-saas-rz-prod"."dns-tagged-history"."bitaa-refined-common"."year={dt_y}"."month={dt_m}"."day={dt_d}"'
dremio_space = "ENG_DataEngineering"
dremio_subspace = "dns_cubes_portunus"
dremio_history_vds = "s3_dns_history_{dt}"

start_date_str = "2021-08-14" #start_date of the data processing
username="<username>@infoblox.com" #username
password="<PAT>" #Dremio PAT

def api_dremio_post(url, body, headers):
    response = requests.post(url, json=body, headers=headers)
    return response

def api_dremio_get(url, headers):
    response = requests.get(url, headers=headers)
    return response

#Method to generate auth token
def generate_token(username, password):
    body = {
        "userName": username,
        "password": password
    }
    response = api_dremio_post(dremio_login_url, body, headers=None)
    js = json.loads(response.text)
    return '_dremio'+js["token"]

#Generate dates given the start date and n
def daterange(start_date, n):
    for i in range(n+1):
        yield start_date - timedelta(i)

#This method can be used to trigger reflection refresh related to a PDS
def refresh_catalog(catalog_id, headers):
    catalog_bypath_url = f"{dremio_catalog_url}/{catalog_id}/refresh"
    print(catalog_bypath_url)
    response = api_dremio_post(catalog_bypath_url, "", headers)
    js = json.loads(response.text)
    return js

#Update the combined history VDS for including the current date
def update_combined_history_vds(input_date, date_interval, headers):
    vds_list = []
    create_cmd = 'CREATE OR REPLACE VDS "{space}"."{subspace}"."s3_dns_history"\nAS\n'
    query = 'select * from "{space}"."{subspace}"."s3_dns_history_{dt}"'
    create_query = create_cmd.format(space=dremio_space, subspace=dremio_subspace)

    for date_iter in daterange(input_date, date_interval):
        dt_str = date_iter.strftime("%Y%m%d")
        vds_list.append(query.format(dt=dt_str, space = dremio_space, subspace=dremio_subspace))

    update_vds_body = create_query + "\nUNION ALL\n".join(vds_list)
    print(f"SQL: {update_vds_body}")
    body = {"sql": update_vds_body}
    response = api_dremio_post(dremio_sql_url, body, headers)
    js = json.loads(response.text)
    print(f"JobId: {js['id']}")

    is_completed = poll_job(js['id'], headers)
    if not is_completed:
        print(f"Error! Combined History VDS update did not complete for {js['id']}")
        exit(0)
    print(f"Combined History VDS update is complete")
    return

#Create PDS for the input_date
def promote_pds(input_date, headers):
    dt_year = input_date.strftime('%Y')
    dt_month = input_date.strftime('%m')
    dt_day = input_date.strftime('%d')
    suffix_path = dremio_source_path.format(dt_y = dt_year, dt_m = dt_month, dt_d =dt_day)

    #Poll the catalog if the PDS is also created
    js = poll_catalog(suffix_path, headers)
    if js["entityType"] == "dataset":
        print(f"PDS at {suffix_path} is already created.")
        return

    #Encode the PDS id
    pds_id = u.quote(js['id'], safe='')

    #Promote the catalog id
    catalog_url = f"{dremio_catalog_url}/{pds_id}"
    body= {
        "entityType": "dataset",
        "id": pds_id,
        "path": js["path"],
        "type": "PHYSICAL_DATASET",
        "format": {"type": "Parquet"}
    }

    #Majority of the times, this API times out. Catching a generic exception for now and polling the catalog for the status
    try:
        response = api_dremio_post(catalog_url, body, headers)
        js = json.loads(response.text)
    except Exception as ex:
        print(ex)

    curr_wait_time = 0
    while curr_wait_time < max_wait_time:
        js = poll_catalog(suffix_path, headers)
        if js["entityType"] == "dataset":
            print(f"PDS at {suffix_path} is successfully created.")
            return
        print(f"Polling for PDS creation at {suffix_path}...")
        time.sleep(wait_time)
        curr_wait_time+=wait_time
    print(f"PDS at {suffix_path} is not created - Timed out (10 minutes)")
    exit(0)

def create_vds(vds_name, sql_body, headers):
    body = {
        "entityType": "dataset",
        "path": [
            dremio_space,
            dremio_subspace,
            vds_name
        ],
        "type": "VIRTUAL_DATASET",
        "sql": sql_body,
        "sqlContext": [dremio_space]
    }
    print(body,dremio_catalog_url)
    response = api_dremio_post(dremio_catalog_url, body, headers)
    print(response)
    js = json.loads(response.text)
    print(js)
    return js

#Using catalog API to create VDS
def create_history_vds_v2(input_date, headers):
    dt_year = input_date.strftime('%Y')
    dt_month = input_date.strftime('%m')
    dt_day = input_date.strftime('%d')
    pds_path = dremio_pds_path.format(dt_y = dt_year, dt_m = dt_month, dt_d =dt_day)

    dremio_history_vds_today = dremio_history_vds.format(dt=input_date.strftime("%Y%m%d"))
    vds_parent_path = "{space}/{subspace}".format(space = dremio_space, subspace=dremio_subspace)
    vds_full_path = "{space}/{subspace}/{dremio_history_vds}".format(dremio_history_vds=dremio_history_vds_today, space = dremio_space, subspace=dremio_subspace)

    is_created = poll_vds(vds_parent_path, dremio_history_vds_today, headers)
    if is_created:
        print(f"VDS for {vds_full_path} exists.")
        return

    sql_body = 'select *, SUBSTR(TO_TIMESTAMP("timestamp"),1,10) AS dt_str, TO_TIMESTAMP("timestamp") as dt from {dp}'.format(dp=pds_path)
    print(sql_body)
    create_vds(dremio_history_vds_today,sql_body,headers)
    is_created = poll_vds(vds_parent_path, dremio_history_vds_today, headers)

    if not is_created:
        print(f"Error! VDS creation did not complete for {dremio_history_vds_today}")
        exit(0)

    print(f"VDS {dremio_history_vds_today} successfully created")
    return

#Poll the catalog for an id
def poll_catalog(url_suffix_path, headers):
    catalog_bypath_url = f"{dremio_catalog_bypath_url}/{url_suffix_path}"
    print(catalog_bypath_url)
    response = api_dremio_get(catalog_bypath_url, headers)
    js = json.loads(response.text)
    return js

#Poll the existence of the VDS in the children of the expected parent
def poll_vds(vds_parent_path, vds_lookup, headers):
    js = poll_catalog(vds_parent_path, headers)
    print(f"Checking for VDSs under {vds_parent_path}")
    for vds in js["children"]:
        if vds_lookup in vds["path"] and vds["datasetType"] == "VIRTUAL":
            return True
    return False

#Create a History VDS for the input date
def create_history_vds(input_date, headers):
    dt_year = input_date.strftime('%Y')
    dt_month = input_date.strftime('%m')
    dt_day = input_date.strftime('%d')
    pds_path = dremio_pds_path.format(dt_y = dt_year, dt_m = dt_month, dt_d =dt_day)

    dremio_history_vds_today = dremio_history_vds.format(dt=input_date.strftime("%Y%m%d"))
    vds_full_name = '"{space}"."{subspace}".{dremio_history_vds}'.format(dremio_history_vds=dremio_history_vds_today, space = dremio_space, subspace=dremio_subspace)
    vds_parent_path = "{space}/{subspace}".format(space = dremio_space, subspace=dremio_subspace)
    vds_full_path = "{space}/{subspace}/{dremio_history_vds}".format(dremio_history_vds=dremio_history_vds_today, space = dremio_space, subspace=dremio_subspace)

    is_created = poll_vds(vds_parent_path, dremio_history_vds_today, headers)

    if is_created:
        print(f"VDS for {vds_full_path} exists.")
        return

    create_cmd = 'CREATE OR REPLACE VDS {vds_path} \
    AS \n select *, SUBSTR(TO_TIMESTAMP("timestamp"),1,10) AS dt_str, TO_TIMESTAMP("timestamp") as dt \
    from {dp}'
    update_vds_body = str(create_cmd).format(vds_path=vds_full_name, dp=pds_path)
    print(update_vds_body)
    body = {"sql": update_vds_body}
    response = api_dremio_post(dremio_sql_url, body, headers)
    js = json.loads(response.text)
    print(js["id"])

    is_completed = poll_job(js['id'], headers)
    if not is_completed:
        print(f"Error! VDS creation did not complete for {js['id']}")
        exit(0)
    print(f"VDS {dremio_history_vds_today} successfully created")
    return

#Poll the JOB API to check the status periodically for a specific job Id
def poll_job(job_id, headers):
    url = f"{dremio_job_url}/{job_id}"
    curr_wait_time = 0
    wait_time_short = wait_time/10
    while curr_wait_time < max_wait_time:
        response = api_dremio_get(url, headers=headers)
        js = json.loads(response.text)
        if js["jobState"] in ['COMPLETED']:
            print("Job successfully completed")
            return True
        elif js["jobState"] in ['CANCELED', 'FAILED']:
            print(f"Error! Job failed with status {js['jobState']}")
            return False
        print("Polling....")
        time.sleep(wait_time_short)
        curr_wait_time+=wait_time_short
    print(f"Error! Poll timed out for {job_id} with status {js['jobState']}")
    return False

#Check if reflection exists
def poll_reflection(reflection_name, headers):
    response = api_dremio_get(dremio_reflection_url, headers)
    js = json.loads(response.text)
    for ref in js["data"]:
        if reflection_name == ref["name"]:
            return True
    return False

#Create reflections for the input date
def create_raw_reflection(input_date, headers):
    dt_str = input_date.strftime("%Y%m%d")
    reflection_name_raw1 = f"s3_dns_history_{dt_str}_raw1"
    is_created = poll_reflection(reflection_name_raw1, headers)

    if is_created:
        print(f"Raw reflection {reflection_name_raw1} already exists")
        return

    suffix_path = f"{dremio_space}/{dremio_subspace}/s3_dns_history_{dt_str}"
    catalog_bypath_url = f"{dremio_catalog_bypath_url}/{suffix_path}"

    response = api_dremio_get(catalog_bypath_url, headers)
    js = json.loads(response.text)

    ref_body = {
        "type": "RAW",
        "name": reflection_name_raw1,
        "datasetId": js['id'],
        "enabled": "true",
        "arrowCachingEnabled": "false",
        "displayFields": [
            {
                "name": "type"
            },
            {
                "name": "storage_id"
            },
            {
                "name": "timestamp"
            },
            {
                "name": "qname"
            },
            {
                "name": "query_type"
            },
            {
                "name": "response"
            },
            {
                "name": "qip"
            },
            {
                "name": "rip"
            },
            {
                "name": "policy_id"
            },
            {
                "name": "source"
            },
            {
                "name": "domains"
            },
            {
                "name": "dns_view"
            },
            {
                "name": "network"
            },
            {
                "name": "user"
            },
            {
                "name": "device_name"
            },
            {
                "name": "os_version"
            },
            {
                "name": "mac_address"
            },
            {
                "name": "dhcp_fingerprint"
            },
            {
                "name": "_storage_id"
            },
            {
                "name": "pname"
            },
            {
                "name": "refined_at"
            },
            {
                "name": "dir0"
            },
            {
                "name": "dt_str"
            },
            {
                "name": "dt"
            }
        ],
        "partitionFields": [
            {
                "name": "dir0"
            },
            {
                "name": "dt_str"
            }
        ],
        "sortFields": [
            {
                "name": "dt"
            }
        ],
        "partitionDistributionStrategy": "STRIPED"
    }

    response = api_dremio_post(dremio_reflection_url, ref_body, headers)
    js = json.loads(response.text)
    print(f"Raw reflection {reflection_name_raw1} refresh started")

#Metadata refresh of the PDS of the input date
def metadata_refresh(input_date, headers):
    dt_year = input_date.strftime('%Y')
    dt_month = input_date.strftime('%m')
    dt_day = input_date.strftime('%d')
    pds_path = dremio_pds_path.format(dt_y = dt_year, dt_m = dt_month, dt_d =dt_day)

    metadata_refresh_body = f'ALTER PDS {pds_path} REFRESH METADATA'
    print(metadata_refresh_body)
    body = {"sql": metadata_refresh_body}
    response = api_dremio_post(dremio_sql_url, body, headers)
    js = json.loads(response.text)
    print(js["id"])

    is_completed = poll_job(js['id'], headers)
    if not is_completed:
        print(f"Error! Metadata refresh did not complete for {js['id']}")
        exit(0)
    print("Metadata refresh completed")
    return

def main(args):
    # default date should be the day prior to running when run in batch mode so it gets full day of data
    # this date value corresponds to the date of the events not the date the code was run
    # if current_date is passed then that overrides everything and runs for current day.

    input_date = date_parser.parse(args.date).date() if args.date else (datetime.today() - timedelta(1)).date()
    if args.current_date is True:
        input_date = datetime.today().date()

    auth_token = generate_token(username, password)
    #auth_token = '<AuthToken>'

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    date_interval = (input_date - start_date).days

    headers = {
        'Authorization': auth_token,
        'Content-Type': "application/json",
        'cache-control': "no-cache"
    }

    print("\n--------------------------------------")
    print(f"PDS for {input_date}")
    print("--------------------------------------")
    promote_pds(input_date, headers)

    print("\n--------------------------------------")
    print(f"VDS for {input_date}")
    print("--------------------------------------")
    create_history_vds(input_date, headers)

    print("\n--------------------------------------")
    print(f"Metadata refresh for {input_date}")
    print("--------------------------------------")
    metadata_refresh(input_date, headers)

    print("\n--------------------------------------")
    print(f"Raw Reflection for {input_date}")
    print("--------------------------------------")
    create_raw_reflection(input_date, headers)

    if not args.noupdatehistory:
        print("\n--------------------------------------")
        print(f"Combined History VDS for {input_date}")
        print("--------------------------------------")
        update_combined_history_vds(input_date, date_interval, headers)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="curate a file of dns", allow_abbrev=True)
    parser.add_argument('--date', '-date', help="date to run curation against", required=False)
    parser.add_argument('--current-date', '-curr', help="run against current date(True if passed)", action='store_true')
    parser.add_argument('--noupdatehistory', '-nohis', help="Do not update combined History VDS(True if passed)", action='store_true')
    args = parser.parse_args()
    main(args)