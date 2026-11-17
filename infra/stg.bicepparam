using 'main.bicep'

param env = 'stg'
param location = 'australiaeast'
param swaLocation = 'eastasia'
param swaSku = 'Free'

// The pucksley.com zone lives in the Personal subscription's `global` resource group
// (infra/zone.bicep), and both service principals hold DNS Zone Contributor on it, so Bicep can
// write this env's CNAME.
param customHostname = 'stg-www.pucksley.com'
