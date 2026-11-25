param(
    [string]$Repository = 'califDEV/asteri-ios',
    [string]$BundleId = 'org.asteri.califdev',
    [string]$GhPath = ''
)
$ErrorActionPreference = 'Stop'
if (!$GhPath) {
    $command = Get-Command gh -ErrorAction SilentlyContinue
    if ($command) { $GhPath = $command.Source }
    else { $GhPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\tools\gh\bin\gh.exe')) }
}
if (!(Test-Path -LiteralPath $GhPath)) { throw 'GitHub CLI not found. Pass -GhPath.' }
if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') { throw 'Invalid repository' }
if ($BundleId -notmatch '^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$') { throw 'Invalid bundle identifier' }
$apiId = Read-Host 'Telegram API ID (my.telegram.org/apps)'
if ($apiId -notmatch '^[1-9][0-9]*$') { throw 'API ID must be a positive integer' }
$secureHash = Read-Host 'Telegram API Hash (input hidden)' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureHash)
try {
    $apiHash = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    if ($apiHash -notmatch '^[a-fA-F0-9]{32}$') { throw 'API Hash must have 32 hexadecimal characters' }
    $configuration = @{
        bundle_id = $BundleId; api_id = $apiId; api_hash = $apiHash
        team_id = 'UNSIGNED00'; is_internal_build = 'true'; is_appstore_build = 'false'
        appstore_id = '0'; app_specific_url_scheme = 'asteri'
        premium_iap_product_id = ''; enable_siri = $false; enable_icloud = $false
    } | ConvertTo-Json -Compress
    $configuration | & $GhPath secret set TELEGRAM_BUILD_CONFIGURATION --repo $Repository
    if ($LASTEXITCODE -ne 0) { throw 'Could not upload GitHub Actions secret' }
    Write-Host 'TELEGRAM_BUILD_CONFIGURATION saved to GitHub Secrets. No local credentials file was created.'
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    $apiHash = $null
    $configuration = $null
    $secureHash.Dispose()
}
