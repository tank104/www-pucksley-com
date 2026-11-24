@description('Azure region for non-SWA resources (e.g. australiaeast).')
param location string

@description('Resource name prefix (e.g. pk-prd-www).')
param prefix string

resource laws 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-log-ae'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: '${prefix}-ain-ae'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: laws.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output logAnalyticsId string = laws.id
output appInsightsConnectionString string = appi.properties.ConnectionString
output appInsightsInstrumentationKey string = appi.properties.InstrumentationKey
