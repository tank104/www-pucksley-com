using 'main.bicep'

param env = 'prd'
param location = 'australiaeast'
param swaLocation = 'eastasia'
param swaSku = 'Free'

// See stg.bicepparam.
param customHostname = 'www.pucksley.com'

// The bare domain answers too, and redirects to www (the workflow makes www the SWA's default domain).
param apexHostname = 'pucksley.com'
