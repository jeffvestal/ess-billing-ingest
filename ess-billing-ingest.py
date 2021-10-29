import os
import logging
import requests
from elasticsearch import Elasticsearch, helpers
from time import time, sleep
from datetime import datetime

__version__ = 0.1

'''
connect to Elastic Cloud Billing API to pull down detailed cluster billing metrics
send them to an elasticsearch cluster for magic
https://www.elastic.co/guide/en/cloud/current/Billing_Costs_Analysis.html
'''


def ess_connect(cluster_id, cluster_api_key):
    '''
    Create a connection to Elastic Cloud
    '''

    logging.info ('Attempting to create connection to elastic cluster')

    es = Elasticsearch(
        cloud_id = cluster_id,
        api_key = cluster_api_key
    )

    return es

def get_billing_api(endpoint, billing_api_key):
    '''
    make a GET request to the billing api
    '''

    logging.info(f'calling billing api with {endpoint}')
    ess_api = 'api.elastic-cloud.com'

    response = requests.get(
        url = f'https://{ess_api}{endpoint}',
        headers = {'Authorization': billing_api_key}
    )

    return response


def pull_org_id(billing_api_key):
    '''
    Get account /api/v1/account info to org_id
    return org_id
    '''

    logging.info(f'Starting pull_org_id')

    # get org_id if it doesn't exist
    account_endp = '/api/v1/account'
    response = get_billing_api(account_endp, billing_api_key)

    if response.status_code != 200:
        logging.error(f'pull_org_id returned error {response} {response.reason}')
        # TODO Need to decide what to do in this situation
    else:
        rj = response.json()
        logging.info(rj)
        return rj['id']

def pull_org_summary(org_id, org_summary_index, now):
    '''
    Get org billing summary including balance
    '''

    logging.info(f'starting pull_org_summary')

    org_summary_endp = f'/api/v1/billing/costs/{org_id}'
    response = get_billing_api(org_summary_endp, billing_api_key)

    if response.status_code != 200:
        raise
        #TODO something else
    else:
        rj = response.json()

        rj['org_id'] = org_id
        rj['_index'] = org_summary_index
        rj['api'] = org_summary_endp
        rj['@timestamp'] = now

        logging.debug(rj)
        return rj

def pull_deployments( org_id, billing_api_key, deployment_index, now):
    '''
    Pull list of deployments from /api/v1/billing/costs/<org_id>/deployments
    return list of deployments payload
    '''

    logging.info(f'starting pull_deployments')

    # get deployments
    deployments_endp = f'/api/v1/billing/costs/{org_id}/deployments'
    response = get_billing_api(deployments_endp, billing_api_key)

    if response.status_code != 200:
        logging.error(response.status_code)
        raise
        #TODO something else
    else:
        rj = response.json()

        #build deployments payload
        payload = []
        for d in rj['deployments']:
            d['_index'] = deployment_index
            d['api'] = deployments_endp
            d['@timestamp'] = now
            payload.append(d)


        logging.debug(payload)
        return (payload)


def pull_deployment_itemized(org_id, billing_api_key, deployment_itemized_index, deployment, now):
    '''
    Get the itemized billing for a deployment
    '''

    logging.info(f'starting pull_deployment_itemized')

    # get itemized
    deployment_id = deployment['deployment_id']
    itemized_endp = f'/api/v1/billing/costs/{org_id}/deployments/{deployment_id}/items'
    response = get_billing_api(itemized_endp, billing_api_key)

    if response.status_code != 200:
        raise
        #TODO something else
    else:
        rj = response.json()
        payload = {}

        #build deployments and extra info
        payload['deployment'] = {
                'deployment_id' : deployment['deployment_id'],
                'deployment_name' : deployment['deployment_name'],
                'api' : itemized_endp
                }
        payload['_index'] = deployment_itemized_index
        payload['@timestamp'] = now

        # Rather than deal wiht nested docs, break out the DTS and Resource info by SKU
        for key in rj:
            if key in ('data_transfer_and_storage', 'resources'):
                payload[key] = {}
                for d in rj[key]:
                    payload[key][d['sku']] = d
            else:
                payload[key] = rj[key]


    logging.debug(payload)
    return payload


def main(billing_api_key, es, organization_delay, org_summary_index, deployment_inventory_delay, deployment_index, deployment_itemized_delay, deployment_itemized_index):
    '''
    Connect to API to pull organization id from account,needed for billing APIs
    get list of all deployments currently in the account
    pull the billing info for:
    - account summary level
    - deployment summary level
    - deployment itemized level

    index into elastic cluster
    '''

    logging.info(f'Starting main ')

    # Run the billing pulls on the startup
    deployment_inventory_last_run = 0
    organization_last_run = 0
    deployment_itemized_last_run = 0


    # get the account org_id
    logging.info(f'calling pull_org_id')
    org_id = pull_org_id(billing_api_key)


    logging.info(f'Starting main loop')
    while True:
        # This is kinf of a lazy way to do a timer but exactly running on intervals is not super important so here we are


        billing_payload = []
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # get deplotment summary billing
        deployment_inventory_elapsed = time() - deployment_inventory_last_run
        if deployment_inventory_elapsed >= deployment_inventory_delay:
            logging.info(f'calling pull_deployments after {deployment_inventory_elapsed} seconds')
            deployments = pull_deployments(org_id, billing_api_key, deployment_index, now)
            billing_payload.extend(deployments)
            deployment_inventory_last_run = time()

        # get organization billing summary
        organization_elapsed = time() - organization_last_run
        if organization_elapsed >= organization_delay:
            logging.info(f'calling pull_org_summary after {organization_elapsed} seconds')
            org_summary = pull_org_summary(org_id, org_summary_index, now)
            billing_payload.append(org_summary)
            organization_last_run = time()

        # get deployment itimieze billing
        deployment_itemized_elapsed = time() - deployment_itemized_last_run
        if deployment_itemized_elapsed >= deployment_itemized_delay:
            for d in deployments:
                logging.info(f'calling pull_deployment_itemized after {deployment_itemized_elapsed} seconds')
                itemized = pull_deployment_itemized(org_id, billing_api_key, deployment_itemized_index, d, now)
                billing_payload.append(itemized)
            deployment_itemized_last_run = time()


        if billing_payload:
            logging.info('sending payload to bulk')
            helpers.bulk(es, billing_payload)

        # don't spin
        sleep(1)




if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)d:%(message)s', level=logging.INFO)
    logging.info('Starting up')

    # ESS Billing
    billing_api_key = os.getenv('billing_api_key')

    organization_delay = 60
    org_summary_index = 'ess.billing'

    deployment_inventory_delay = 3600
    deployment_index = 'ess.billing.deployment'

    deployment_itemized_delay = 60
    deployment_itemized_index = 'ess.billing.deployment.itemized'

    # Destination Elastic info
    es_id = os.getenv('billing_es_id')
    es_api = os.getenv('billing_es_api')
    indexName = 'ess_billing'
    es = ess_connect(es_id, es_api)

    # Start main loop
    main(billing_api_key, es, organization_delay, org_summary_index, deployment_inventory_delay, deployment_index, deployment_itemized_delay, deployment_itemized_index)




#vim: expandtab tabstop=4
