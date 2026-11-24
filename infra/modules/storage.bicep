@description('Azure region.')
param location string

@description('Resource name prefix (e.g. pk-prd-www).')
param prefix string

// Storage account names: 3-24 chars, lowercase alphanumeric only (no hyphens).
var storageName = take(toLower(replace('${prefix}${uniqueString(resourceGroup().id)}', '-', '')), 24)

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  // storageName is always prefix(~10) + uniqueString(13) = well over the 3-char floor.
  #disable-next-line BCP334
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
  }
}

resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource waitlistTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = {
  parent: tableService
  name: 'waitlist'
}

// Connection-string storage auth (not managed identity) — mirrors
// the sibling sites' Function storage: the deploy identity
// only has Contributor on the RG, which can't create the role assignments
// identity-based storage access would require. Consumed by the SWA's
// managed Functions (api/waitlist) as an app setting — see swa.bicep.
output connectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
output tableName string = waitlistTable.name
