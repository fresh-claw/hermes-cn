param(
  [string]$BaseUrl = $env:XIAOMA_HERMES_BASE_URL
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
  $BaseUrl = "https://useai.live/hermes"
}
$BaseUrl = $BaseUrl.TrimEnd("/")
$env:XIAOMA_HERMES_ENTRYPOINT = "github-windows-powershell"

$script = Invoke-RestMethod -Uri "$BaseUrl/install.ps1"
Invoke-Expression $script
