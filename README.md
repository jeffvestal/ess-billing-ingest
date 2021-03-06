## *This is a work in progress. Caution should be used when making financial or operational decisions off this data. Confirm all data directly from the Elastic Cloud Billing Dashboard in your account. This is not officially endorsed or supported by Elastic Co.*

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

# Example Dashboards
ndjson dashboard files are under `./dashboards/`

<img width="2448" alt="ESS Billing Account Overview" src="https://user-images.githubusercontent.com/53237856/139737781-a79251ca-8e20-41da-a1da-f41a4ef88338.png">

<img width="2441" alt="ESS Billing Deployment Details" src="https://user-images.githubusercontent.com/53237856/139737796-bdf535a3-c5b2-4bb2-80f6-66e2ed80e658.png">


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

#### Runtime Field
There is one runtime field added to the mapping to parse out the cloud region for the `ess.billing.deployment.itemized` documents of `bill.type:resources` 
This can be added to the index mapping at any time. 
```
PUT ess.billing.deployment.itemized/_mapping
{
    "runtime": {
    "cloudregion": {
      "type": "keyword",
      "script": """
      if (doc["bill.type.keyword"].value == "resources") {
        String cloudregion=grok('%{WORD:provider}\\.%{WORD:node_type}\\.%{WORD:nothing}\\.%{WORD:nothing}-%{DATA:cloudregion}_').extract(doc["sku.keyword"].value)?.cloudregion;
        if (cloudregion != null) emit(cloudregion); 
      }
        """
    }
  }
```

#### ILM
Currently ILM is not auto-configured, so it is up to the user to decide how they want to manage the lifecycle of the data


