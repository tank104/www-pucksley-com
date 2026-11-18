// www.pucksley.com: one environment (stg or prd) of the site. The same shape as the sibling sites'
// infra: a Static Web App with managed Functions (api/), App Insights, a storage table for the email
// form, and the env's CNAME written cross-RG into the pucksley.com zone in `global`. Deployed by
// .github/workflows/deploy-*.yml into pk-www-{env}; the RGs, the zone and the deploy identities come
// from infra/bootstrap.ps1.

targetScope = 'resourceGroup'

@description('Environment name (stg or prd). Drives resource naming.')
@allowed([
  'stg'
  'prd'
])
param env string

@description('Azure region for non-SWA resources.')
param location string = 'australiaeast'

@description('Azure region for the Static Web App. SWA is not available in australiaeast.')
param swaLocation string = 'eastasia'

@description('SWA SKU. Free is free; Standard (~$9/month) adds an SLA + staging environments.')
@allowed([
  'Free'
  'Standard'
])
param swaSku string = 'Free'

@description('Public custom hostname for the SWA (e.g. www.pucksley.com). Empty = no custom domain, SWA uses default hostname only.')
param customHostname string = ''

@description('The bare domain (pucksley.com) to point at this SWA as well, or empty. prd only: there is one apex.')
param apexHostname string = ''

@description('Resource group hosting the pucksley.com DNS zone (infra/zone.bicep). The env deployment cross-RG-writes its CNAME into this RG.')
param dnsResourceGroup string = 'global'

var prefix = 'pk-${env}-www'

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    prefix: prefix
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    prefix: prefix
  }
}

module swa 'modules/swa.bicep' = {
  name: 'swa'
  params: {
    location: swaLocation
    prefix: prefix
    sku: swaSku
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    waitlistStorageConnectionString: storage.outputs.connectionString
    waitlistTableName: storage.outputs.tableName
  }
}

// Cross-RG: write the SWA-pointing CNAME into the pucksley.com zone.
// The label is the leftmost hostname segment (e.g. 'www' from 'www.pucksley.com').
var customHostnameLabel = empty(customHostname) ? '' : split(customHostname, '.')[0]

module dnsRecord 'modules/dns-cname.bicep' = if (!empty(customHostname)) {
  scope: resourceGroup(dnsResourceGroup)
  name: 'dns-${env}-cname'
  params: {
    zoneName: 'pucksley.com'
    recordName: customHostnameLabel
    targetCname: swa.outputs.defaultHostname
  }
}

// Cross-RG: the apex as an alias A record onto this SWA (prd only). Its ownership TXT record is written
// by the workflow, which is where the token first exists.
module dnsApex 'modules/dns-apex.bicep' = if (!empty(apexHostname)) {
  scope: resourceGroup(dnsResourceGroup)
  name: 'dns-${env}-apex'
  params: {
    zoneName: apexHostname
    swaId: swa.outputs.id
  }
}

// NOTE: the SWA customDomain registration is intentionally NOT done here.
// cname-delegation validation can poll for ~an hour on first creation, which
// outlives the GitHub OIDC credential the deploy runs under (the federated
// assertion is valid ~5 min), so an inline blocking customDomain would make
// `az deployment group create` fail with AADSTS700024. Bicep writes the CNAME
// above; the workflow registers the custom domain with
// `az staticwebapp hostname set --no-wait` so it validates asynchronously and
// never blocks the deploy. (Pattern from the sibling sites.)
output swaName string = swa.outputs.name
output swaHostname string = swa.outputs.defaultHostname
output customHostname string = customHostname
output apexHostname string = apexHostname
