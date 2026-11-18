// The pucksley.com DNS zone, in the `global` resource group of the owner's Personal subscription.
// Made once by infra/bootstrap.ps1, and safe to deploy again.
//
// Ownership: this file owns the zone itself and the records that are not the website's (the apex TXT
// record and the mail records below). The website's records belong to its own pipeline, which writes them
// on every deploy; do not declare them here:
//   - `www` and `stg-www` CNAMEs (infra/main.bicep, modules/dns-cname.bicep)
//   - the apex `@` A record, an alias onto the prd Static Web App (modules/dns-apex.bicep)
// Deploy this file in Incremental mode only (the default): Complete mode would delete those records.
// It is not deployed by CI: run it by hand (or infra/bootstrap.ps1) after changing it:
//   az deployment group create -g global --template-file infra/zone.bicep --subscription Personal
//
// The domain is registered at OnlyDomains, with its nameservers set to the ones this deployment outputs.

targetScope = 'resourceGroup'

resource zone 'Microsoft.Network/dnsZones@2018-05-01' = {
  name: 'pucksley.com'
  location: 'global'
  tags: {
    project: 'pucksley'
  }
}

// The apex TXT record. Azure DNS keeps every TXT value at a name in one record set, and a deploy replaces
// the whole set, so every value at `@` must be listed here or the next deploy removes it.
@description('Every TXT value at the apex (pucksley.com).')
param apexTxt array = [
  // Google Search Console's proof that the domain is ours. Google checks it again from time to time, so it stays.
  'google-site-verification=md2V3mysGdEsn36f2qx0HsWQp5Vtf330_XELmvb2Fkg'
  // The prd Static Web App's ownership token for the apex. If the Static Web App is ever made again, the prd
  // workflow publishes the new token itself; copy it here then, in place of this one.
  '_1i0cfg72xzgv99clxf3a30t2fk6c02u'
  // No server sends mail as pucksley.com (see below).
  'v=spf1 -all'
]

resource apexTxtRecord 'Microsoft.Network/dnsZones/TXT@2018-05-01' = {
  parent: zone
  name: '@'
  properties: {
    TTL: 3600
    TXTRecords: [for v in apexTxt: {
      value: [
        v
      ]
    }]
  }
}

// pucksley.com sends and receives no email (the site's contact address is elsewhere). These say so, so
// nobody can send mail that passes as @pucksley.com: a null MX (RFC 7505) accepts none, SPF (above) names
// no sender, and DMARC tells receivers to reject anything claiming to be from the domain. To start using
// email on the domain, replace the MX and the SPF value and loosen DMARC.
resource nullMx 'Microsoft.Network/dnsZones/MX@2018-05-01' = {
  parent: zone
  name: '@'
  properties: {
    TTL: 3600
    MXRecords: [
      {
        preference: 0
        exchange: '.'
      }
    ]
  }
}

resource dmarc 'Microsoft.Network/dnsZones/TXT@2018-05-01' = {
  parent: zone
  name: '_dmarc'
  properties: {
    TTL: 3600
    TXTRecords: [
      {
        value: [
          'v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s'
        ]
      }
    ]
  }
}

@description('Azure-assigned authoritative nameservers. Set these as the domain\'s nameservers at the registrar (OnlyDomains).')
output nameServers array = zone.properties.nameServers
