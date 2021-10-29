# ESS Billing Ingest
Pulls Elastic Cloud Billing information from the [Billing API](https://www.elastic.co/guide/en/cloud/current/Billing_Costs_Analysis.html) then sends it to an elasticsearch cluster
Author : Jeff Vestal - github.com/jeffvestal

# Description
This script will connect to Elastic Cloud's billing api and pull down various billin data:
- [Account Level Summary](https://www.elastic.co/guide/en/cloud/current/Billing_Costs_Analysis.html#get-costs-overview)
- [Deployment Level Summary](https://www.elastic.co/guide/en/cloud/current/Billing_Costs_Analysis.html#get-costs-deployments)
- [Deployment Itimized](https://www.elastic.co/guide/en/cloud/current/Billing_Costs_Analysis.html#get-costs-items-by-deployment)

Depending on the section, info can include:
- costs
	- total
	- hourly
	- dts
- resources
	- node type breakdown

Billing data is sent to an elasticsearch cluster where it can be used for analysis, searching, alerting, dashboard, magic

# Requirements
- python 3.6+
- [elasticsearch python library](https://elasticsearch-py.readthedocs.io/)
- [Elastic Cloud account](https://cloud.elastic.co/)
- [Elastic Cloud API Key](https://www.elastic.co/guide/en/cloud/current/ec-api-authentication.html)
- elasticsearch cluster to store billing data
	- [elasticsearch api_key](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-api-create-api-key.html)

# Configuration
#### There are 3 environment variables that are required
- *billing_api_key* 
	- The Elastic Cloud API Key
- *billing_es_id*
	- destination elasticsearch cloud_id
- *billing_es_api*
	- destination elasticsearch api_key

#### There are default setting that can be changed in the script
- organization_delay = 60
	- Delay between Account Level summary data pull
- deployment_inventory_delay = 3600
	- Delay between Deployment Level summary data pull
- deployment_itemized_delay = 60
	- Delay between Deployment Itemized Level data pull

# Running
1. Set required environment variables
2. ./ess-billing-ingest.py

# Destination Data
#### Indices
By default data is written out to 3 separate indices:
1. *ess.billing*
	- Org level summary
2. *ess.billing.deployment*
	- Deployment level summary
3. *ess.billing.deployment.itemized*
	- Deployment itemized billing

#### Mapping
Elasticsearch correctly auto-types each field. If a different type is required index templates can be set up ahead of time. 

#### ILM
Currently ILM is not auto-configured, so it is up to the user to decide how they want to manage the lifecycle of the data


