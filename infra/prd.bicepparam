using 'main.bicep'

param env = 'prd'
param location = 'australiaeast'
param swaLocation = 'eastasia'
param swaSku = 'Free'

// The pucksley.com zone lives in the Personal subscription's `global` resource group
// (infra/zone.bicep), and the service principal holds DNS Zone Contributor on it, so Bicep can
// write this env's CNAME.
param customHostname = 'www.pucksley.com'

// The bare domain answers too, and redirects to www (the workflow makes www the SWA's default domain).
param apexHostname = 'pucksley.com'
