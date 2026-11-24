# One-time bootstrap for www.pucksley.com's Azure and GitHub setup. Safe to run again: every step
# checks first and skips what already exists.
#
# In the Personal subscription, creates:
#   - The pucksley.com DNS zone in the `global` resource group (infra/zone.bicep), and prints the
#     nameservers to give the registrar (OnlyDomains).
#   - The custom role 'Pucksley www DNS Deployer' (deployment operations only) on `global`.
#   - For the environment (prd; there is no staging):
#       Resource group pk-www-{env} in Australia East, tagged.
#       Microsoft Entra app registration + service principal pk-www-{env}-github.
#       A federated credential letting GitHub Actions sign in as that SP when a job runs in the
#         matching GitHub Environment of tank104/www-pucksley-com.
#       Three roles: Contributor on pk-www-{env} (Bicep creates the site's resources there);
#         DNS Zone Contributor on the pucksley.com zone (the env's CNAME, written cross-RG by
#         infra/modules/dns-cname.bicep); 'Pucksley www DNS Deployer' on `global` (so that
#         cross-RG module can land its nested-deployment tracker there).
#   - The GitHub side: repository variables AZURE_TENANT_ID and AZURE_SUBSCRIPTION_ID, the `prd`
#     environment with its AZURE_CLIENT_ID, limited to the main branch.
#
# Needs: `az` signed in with Owner on the Personal subscription, and `gh` signed in with admin on the
# repository. The az CLI's default subscription is put back as it was at the end.
#
# Run from PowerShell 7:  pwsh -File infra/bootstrap.ps1

[CmdletBinding()]
param(
    [string]$GitHubRepo = 'tank104/www-pucksley-com',
    [string]$Subscription = 'Personal',
    [ValidateSet('prd')]
    [string]$Env = 'prd',
    [string]$Location = 'australiaeast'
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

$zoneName = 'pucksley.com'
$dnsRg = 'global'
$roleName = 'Pucksley www DNS Deployer'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    # az's JSON parser trips over the BOM Windows PowerShell writes by default.
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Initialize-Zone {
    if ((az group exists --name $dnsRg) -ne 'true') {
        Write-Host "Creating RG $dnsRg in $Location..."
        az group create --name $dnsRg --location $Location --output none
    }
    Write-Host "Deploying the $zoneName zone (infra/zone.bicep) into $dnsRg..."
    az deployment group create --resource-group $dnsRg --template-file (Join-Path $here 'zone.bicep') `
        --name "pucksley-zone-$(Get-Date -Format yyyyMMddHHmmss)" --mode Incremental --output none
    $ns = az network dns zone show --resource-group $dnsRg --name $zoneName --query nameServers -o tsv
    Write-Host "Nameservers for $zoneName (set these at the registrar):" -ForegroundColor Cyan
    $ns | ForEach-Object { Write-Host "  $_" }
}

function Initialize-DnsDeployerRole([string]$SubscriptionId) {
    $scope = "/subscriptions/$SubscriptionId/resourceGroups/$dnsRg"
    $existing = az role definition list --custom-role-only true --name $roleName --query '[0].roleName' -o tsv
    if ($existing) {
        Write-Host "Custom role '$roleName' exists, skipping." -ForegroundColor Yellow
        return
    }
    Write-Host "Creating custom role '$roleName'..."
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) 'pucksley-www-dns-deployer.json'
    Write-Utf8NoBom $tmp (@{
        Name             = $roleName
        Description      = 'Lets the www.pucksley.com CI service principals run the cross-RG deployment that writes the site''s CNAME into the global RG''s pucksley.com zone. Deployment operations only - the DNS record write itself comes from a separate DNS Zone Contributor assignment scoped to the pucksley.com zone.'
        Actions          = @(
            'Microsoft.Resources/deployments/write',
            'Microsoft.Resources/deployments/read',
            'Microsoft.Resources/deployments/delete',
            'Microsoft.Resources/deployments/operations/read',
            'Microsoft.Resources/deployments/operationstatuses/read'
        )
        AssignableScopes = @($scope)
    } | ConvertTo-Json -Depth 4)
    try { az role definition create --role-definition $tmp --output none }
    finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
    # A new role definition takes a little while to be assignable.
    for ($i = 0; $i -lt 30; $i++) {
        if (az role definition list --custom-role-only true --name $roleName --scope $scope --query '[0].roleName' -o tsv) { return }
        Start-Sleep -Seconds 5
    }
    throw "Custom role '$roleName' did not appear."
}

function Grant-Role([string]$SpObjectId, [string]$Role, [string]$Scope) {
    $existing = az role assignment list --assignee $SpObjectId --role $Role --scope $Scope --query '[0].id' -o tsv
    if ($existing) {
        Write-Host "  '$Role' on $Scope already assigned, skipping." -ForegroundColor Yellow
        return
    }
    Write-Host "  Assigning '$Role' on $Scope..."
    # A brand-new SP can take a minute to be visible to RBAC: retry, so a failed attempt must not stop
    # the script.
    $PSNativeCommandUseErrorActionPreference = $false
    for ($i = 1; $i -le 10; $i++) {
        az role assignment create --assignee-object-id $SpObjectId --assignee-principal-type ServicePrincipal `
            --role $Role --scope $Scope --output none 2>$null
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Seconds 10
    }
    throw "Could not assign '$Role' on $Scope."
}

function Initialize-Environment([string]$EnvName, [string]$SubscriptionId, [string]$SubjectPrefix) {
    $rgName = "pk-www-$EnvName"
    $appName = "pk-www-$EnvName-github"
    Write-Host ""
    Write-Host "=== $EnvName ===" -ForegroundColor Cyan

    if ((az group exists --name $rgName) -eq 'true') {
        Write-Host "RG $rgName exists, skipping create." -ForegroundColor Yellow
    } else {
        Write-Host "Creating RG $rgName in $Location..."
        az group create --name $rgName --location $Location --tags env=$EnvName project=pucksley --output none
    }

    $appId = az ad app list --display-name $appName --query '[0].appId' -o tsv
    if ($appId) {
        Write-Host "App registration $appName exists (appId=$appId), skipping create." -ForegroundColor Yellow
    } else {
        Write-Host "Creating app registration $appName..."
        $appId = az ad app create --display-name $appName --query appId -o tsv
    }
    $appObjectId = az ad app show --id $appId --query id -o tsv

    $spObjectId = az ad sp list --filter "appId eq '$appId'" --query '[0].id' -o tsv
    if ($spObjectId) {
        Write-Host "Service principal for $appName exists, skipping create." -ForegroundColor Yellow
    } else {
        Write-Host "Creating service principal for $appName..."
        $spObjectId = az ad sp create --id $appId --query id -o tsv
    }

    $subject = "${SubjectPrefix}:environment:$EnvName"
    $has = az ad app federated-credential list --id $appObjectId --query "[?subject=='$subject'].name" -o tsv
    if ($has) {
        Write-Host "Federated credential for '$EnvName' exists, skipping." -ForegroundColor Yellow
    } else {
        Write-Host "Adding federated credential (subject=$subject)..."
        $tmp = Join-Path ([System.IO.Path]::GetTempPath()) "pucksley-fedcred-$EnvName.json"
        Write-Utf8NoBom $tmp (@{
            name      = "gh-$EnvName-env"
            issuer    = 'https://token.actions.githubusercontent.com'
            subject   = $subject
            audiences = @('api://AzureADTokenExchange')
        } | ConvertTo-Json)
        try { az ad app federated-credential create --id $appObjectId --parameters "@$tmp" --output none }
        finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
    }

    Grant-Role $spObjectId 'Contributor' "/subscriptions/$SubscriptionId/resourceGroups/$rgName"
    Grant-Role $spObjectId 'DNS Zone Contributor' "/subscriptions/$SubscriptionId/resourceGroups/$dnsRg/providers/Microsoft.Network/dnszones/$zoneName"
    Grant-Role $spObjectId $roleName "/subscriptions/$SubscriptionId/resourceGroups/$dnsRg"

    Write-Host "Setting up GitHub environment '$EnvName'..."
    if ($EnvName -eq 'prd') {
        # Production deploys only from main: a workflow run from any other branch cannot use the prd
        # environment, so it cannot sign in as the prd identity.
        gh api --method PUT "repos/$GitHubRepo/environments/$EnvName" --silent `
            -F 'deployment_branch_policy[protected_branches]=false' -F 'deployment_branch_policy[custom_branch_policies]=true'
        $branches = gh api "repos/$GitHubRepo/environments/$EnvName/deployment-branch-policies" --jq '.branch_policies[].name'
        if ($branches -notcontains 'main') {
            gh api --method POST "repos/$GitHubRepo/environments/$EnvName/deployment-branch-policies" -f name=main -f type=branch --silent
        }
    } else {
        gh api --method PUT "repos/$GitHubRepo/environments/$EnvName" --silent
    }
    gh variable set AZURE_CLIENT_ID --repo $GitHubRepo --env $EnvName --body $appId

    return [PSCustomObject]@{ Env = $EnvName; RG = $rgName; App = $appName; ClientId = $appId }
}

# --- Main ---
$previous = az account show --query id -o tsv
az account set --subscription $Subscription
try {
    $account = az account show --query '{id:id, tenantId:tenantId, name:name}' -o json | ConvertFrom-Json
    Write-Host "Subscription: $($account.name) ($($account.id))"
    Write-Host "GitHub repo:  $GitHubRepo"

    # GitHub's OIDC subject for this repo. New repositories use the immutable form
    # (repo:Owner@ownerId/name@repoId), which survives renames; read it rather than guess.
    $sub = gh api "repos/$GitHubRepo/actions/oidc/customization/sub" | ConvertFrom-Json
    $subjectPrefix = if ($sub.sub_claim_prefix) { $sub.sub_claim_prefix } else { "repo:$GitHubRepo" }
    Write-Host "OIDC subject: ${subjectPrefix}:environment:<env>"

    Initialize-Zone
    Initialize-DnsDeployerRole $account.id

    gh variable set AZURE_TENANT_ID --repo $GitHubRepo --body $account.tenantId
    gh variable set AZURE_SUBSCRIPTION_ID --repo $GitHubRepo --body $account.id

    $envs = @($Env)
    $results = foreach ($e in $envs) { Initialize-Environment $e $account.id $subjectPrefix }

    Write-Host ""
    Write-Host "=== Done ===" -ForegroundColor Green
    $results | Format-Table -AutoSize
    Write-Host "Merging to main: deploy-prd.yml deploys infra + site to prd."
}
finally {
    az account set --subscription $previous
}
