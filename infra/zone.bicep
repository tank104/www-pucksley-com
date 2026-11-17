// The pucksley.com DNS zone, in the `global` resource group of the owner's Personal subscription.
// Made once by infra/bootstrap.ps1, and safe to deploy again.
//
// Ownership: this file owns the zone itself and any record that is not the website's. `www` and
// `stg-www` belong to the site's own pipeline (infra/main.bicep, modules/dns-cname.bicep), which writes
// them on every deploy; do not declare them here. Deploy this file in Incremental mode only (the
// default): Complete mode would delete those records.
//
// The domain is registered at OnlyDomains. Point its nameservers at the ones this deployment outputs.
//
// No apex record yet: once www.pucksley.com is live, add `pucksley.com` itself (an ALIAS to the prd
// Static Web App, and the SWA's apex custom domain), so the bare domain answers too.

targetScope = 'resourceGroup'

resource zone 'Microsoft.Network/dnsZones@2018-05-01' = {
  name: 'pucksley.com'
  location: 'global'
  tags: {
    project: 'pucksley'
  }
}

@description('Azure-assigned authoritative nameservers. Set these as the domain\'s nameservers at the registrar (OnlyDomains).')
output nameServers array = zone.properties.nameServers
