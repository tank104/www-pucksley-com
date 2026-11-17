// Cross-RG apex writer: the zone's own name (pucksley.com) as an Azure DNS alias A record pointing at the
// prd Static Web App. An apex cannot be a CNAME; an alias follows the SWA's addresses itself, so nothing here
// goes stale. Instantiated by main.bicep with `scope: resourceGroup('global')`, for prd only.
//
// The apex also needs a TXT record at `@` holding the SWA's ownership token. The token only exists once the
// workflow has registered the domain (`az staticwebapp hostname set --validation-method dns-txt-token`), so the
// workflow writes it, not this module.

targetScope = 'resourceGroup'

@description('Apex zone name (must already exist in this RG).')
param zoneName string

@description('Resource ID of the Static Web App the apex points at.')
param swaId string

@description('TTL in seconds.')
param ttl int = 3600

resource zone 'Microsoft.Network/dnsZones@2018-05-01' existing = {
  name: zoneName
}

resource apex 'Microsoft.Network/dnsZones/A@2018-05-01' = {
  parent: zone
  name: '@'
  properties: {
    TTL: ttl
    targetResource: {
      id: swaId
    }
  }
}

output fqdn string = zoneName
