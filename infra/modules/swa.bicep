@description('Azure region for SWA. Must be one of: centralus, eastus2, eastasia, westeurope, westus2.')
param location string

@description('Resource name prefix (e.g. pk-stg-www).')
param prefix string

@description('SWA SKU.')
@allowed([
  'Free'
  'Standard'
])
param sku string = 'Free'

@description('App Insights connection string — piped from the monitoring module.')
param appInsightsConnectionString string

@description('Table Storage connection string — piped from the storage module. Consumed by the api/waitlist managed Function.')
@secure()
param waitlistStorageConnectionString string

@description('Table Storage table name for early access sign-ups — piped from the storage module.')
param waitlistTableName string

resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: '${prefix}-swa-ae'
  location: location
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    provider: 'None'
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    enterpriseGradeCdnStatus: 'Disabled'
  }
}

// Bicep owns ALL app settings on this SWA. Any setting not listed here is
// removed on deploy, so add new settings here rather than out-of-band in the
// portal. These are also the app settings the api/waitlist managed Function
// runs under (SWA managed Functions share the parent SWA's app settings).
// There is no CMS, so no GITHUB_OAUTH_* /
// CMS_OAUTH_BASE_URL settings: add them here (and the params, and the
// workflows' secrets) together with the CMS.
resource swaSettings 'Microsoft.Web/staticSites/config@2023-12-01' = {
  parent: swa
  name: 'appsettings'
  properties: {
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsightsConnectionString
    WAITLIST_TABLE_CONNECTION_STRING: waitlistStorageConnectionString
    WAITLIST_TABLE_NAME: waitlistTableName
  }
}

output id string = swa.id
output name string = swa.name
output defaultHostname string = swa.properties.defaultHostname
