// Cross-RG single-CNAME writer. Instantiated by env main.bicep with
// `scope: resourceGroup('global')` so the record lands in the RG that hosts
// the pucksley.com zone (infra/zone.bicep, in the Personal subscription, which
// leaves `www` to this pipeline). Same module as
// the sibling sites'.

targetScope = 'resourceGroup'

@description('Apex zone name (must already exist in this RG).')
param zoneName string

@description('Subdomain label (e.g. "www"). Becomes <recordName>.<zoneName>.')
param recordName string

@description('Target hostname for the CNAME. Trailing "." added if absent so Azure DNS does not see drift on subsequent deploys.')
param targetCname string

@description('TTL in seconds.')
param ttl int = 3600

var cnameWithDot = endsWith(targetCname, '.') ? targetCname : '${targetCname}.'

resource zone 'Microsoft.Network/dnsZones@2018-05-01' existing = {
  name: zoneName
}

resource cname 'Microsoft.Network/dnsZones/CNAME@2018-05-01' = {
  parent: zone
  name: recordName
  properties: {
    TTL: ttl
    CNAMERecord: {
      cname: cnameWithDot
    }
  }
}

output fqdn string = '${recordName}.${zoneName}'
