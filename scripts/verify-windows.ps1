param(
  [string]$Version = "2026.06.12.1"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Assert-True([bool]$Condition, [string]$Message) {
  if (-not $Condition) {
    throw $Message
  }
}

function Wait-Http([string]$Url) {
  for ($i = 0; $i -lt 30; $i++) {
    try {
      Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2 | Out-Null
      return
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }
  throw "local HTTP server did not become ready"
}

$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $Root "install.ps1"), [ref]$tokens, [ref]$parseErrors) | Out-Null
Assert-True (($parseErrors | Measure-Object).Count -eq 0) "install.ps1 parse failed"

$installPs1 = Get-Content -Raw -Path (Join-Path $Root "install.ps1")
Assert-True ($installPs1.Contains("v$Version")) "install.ps1 version marker mismatch"
Assert-True ($installPs1.Contains("Download-OfficialInstaller")) "official installer validation missing"
Assert-True ($installPs1.Contains("Move-HermesAgentSourceAside")) "official repair fallback missing"
Assert-True ($installPs1.Contains("Ensure-WindowsNode")) "Windows Node.js preparation missing"
Assert-True ($installPs1.Contains("cdn.npmmirror.com/binaries/node/index.json")) "Node.js China mirror missing"
Assert-True ($installPs1.Contains("nodejs.org/dist/index.json")) "Node.js official fallback missing"

$exeBytes = [System.IO.File]::ReadAllBytes((Join-Path $Root "Hermes-zh-CN-Setup.exe"))
$exeText = [System.Text.Encoding]::UTF8.GetString($exeBytes)
Assert-True ($exeText.Contains("v$Version")) "windows exe embedded version marker mismatch"

$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("xiaoma-hermes-win-verify-" + [guid]::NewGuid().ToString("N"))
$home = Join-Path $temp "home"
$bin = Join-Path $temp "bin"
$hermesHome = Join-Path $home ".hermes"
$sourceRoot = Join-Path $temp "source"
$installHome = Join-Path $temp "xiaoma"
New-Item -ItemType Directory -Force -Path $bin, $hermesHome, $sourceRoot, (Join-Path $sourceRoot "hermes_cli") | Out-Null

$fakeHermes = Join-Path $bin "hermes"
Set-Content -Path $fakeHermes -Encoding UTF8 -Value @'
#!/usr/bin/env bash
printf 'Hermes Agent v0.16.0\n'
'@
$fakeHermesCmd = Join-Path $bin "hermes.cmd"
Set-Content -Path $fakeHermesCmd -Encoding ASCII -Value "@echo Hermes Agent v0.16.0"

$fakePython3 = Join-Path $bin "python3"
Set-Content -Path $fakePython3 -Encoding UTF8 -Value @'
#!/usr/bin/env bash
python "$@"
'@

$bannerPath = Join-Path $sourceRoot "hermes_cli/banner.py"
Set-Content -Path $bannerPath -Encoding UTF8 -Value @'
VERSION="0.16.0"
RELEASE_DATE="2026-06-05"
base = f"Hermes Agent v{VERSION} ({RELEASE_DATE})"
'@

$desktopDir = Join-Path $hermesHome "hermes-agent/apps/desktop/release/win-unpacked"
New-Item -ItemType Directory -Force -Path $desktopDir | Out-Null
Set-Content -Path (Join-Path $desktopDir "Hermes.exe") -Encoding ASCII -Value "fake"

if ($IsWindows) {
  $env:PATH = "$bin;$env:PATH"
} else {
  $env:PATH = "$bin`:$env:PATH"
}
$env:HOME = $home
$env:HERMES_HOME = $hermesHome
$env:XIAOMA_HERMES_HOME = $installHome
$env:XIAOMA_HERMES_SOURCE_ROOT = $sourceRoot
$env:XIAOMA_HERMES_REAL_HERMES = $fakeHermes
$env:XIAOMA_HERMES_SKIP_OFFICIAL_INSTALL = "1"
$env:XIAOMA_HERMES_SKIP_WRAPPER = "1"
$env:XIAOMA_HERMES_QUIET = "1"

$port = 18765
$server = Start-Process -FilePath python -ArgumentList @("-m", "http.server", "$port", "--bind", "127.0.0.1") -WorkingDirectory $Root -PassThru -WindowStyle Hidden
try {
  Wait-Http "http://127.0.0.1:$port/install.sh"
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "install.ps1") -BaseUrl "http://127.0.0.1:$port" -SkipOfficial
  if ($LASTEXITCODE -ne 0) {
    throw "install.ps1 exited with $LASTEXITCODE"
  }

  $statusPath = Join-Path $installHome "releases/$Version/PATCH_STATUS"
  Assert-True (Test-Path $statusPath) "PATCH_STATUS was not created"
  $status = Get-Content -Raw -Path $statusPath | ConvertFrom-Json
  Assert-True (($status.patched -contains "hermes_cli/banner.py") -or ($status.state -eq "partial")) "banner patch did not run"

  $updatedBanner = Get-Content -Raw -Path $bannerPath
  Assert-True ($updatedBanner.Contains("爱马仕机器人")) "banner text was not localized"

  $configPath = Join-Path $hermesHome "config.yaml"
  Assert-True (Test-Path $configPath) "config.yaml was not created"
  Assert-True ((Get-Content -Raw -Path $configPath).Contains("language: zh")) "config language was not set"

  Write-Host "windows verification passed: $Version"
} finally {
  if ($server -and -not $server.HasExited) {
    Stop-Process -Id $server.Id -Force
  }
  Remove-Item -Recurse -Force $temp -ErrorAction SilentlyContinue
}
