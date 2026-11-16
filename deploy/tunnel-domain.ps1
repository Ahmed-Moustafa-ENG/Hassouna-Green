# Start Hassouna Green on your own domain, from your own computer.
#
#   .\deploy\tunnel-domain.ps1
#
# This needs the domain to be on Cloudflare (the DNS is free) and a named
# tunnel, which is set up by this script the first time it runs.
#
# The address is then always the same: https://hassounagreen-eg.com
# Keep this window open.
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$port = 8501
$domain = "hassounagreen-eg.com"
$tunnel = "hassouna-green"
$cf = Join-Path $PSScriptRoot "cloudflared.exe"
$cfDir = Join-Path $env:USERPROFILE ".cloudflared"

if (-not (Test-Path $cf)) {
	Write-Host "Downloading cloudflared (the tunnel client)..." -ForegroundColor Cyan
	Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
		-OutFile $cf -UseBasicParsing
}

# ── one-time setup: the tunnel and its DNS route ────────────────────────────
if (-not (Test-Path (Join-Path $cfDir "config.yml"))) {
	Write-Host "Setting up the tunnel for $domain (only the first time)..." -ForegroundColor Cyan
	New-Item -ItemType Directory -Force -Path $cfDir | Out-Null

	# 1. sign in to Cloudflare and pick the domain
	& $cf tunnel login
	if ($LASTEXITCODE -ne 0) {
		throw "cloudflared tunnel login failed. Open https://dash.cloudflare.com/argotunnel to create the tunnel by hand."
	}

	# 2. create the tunnel and read its id
	& $cf tunnel create $tunnel
	$id = (Get-Content (Join-Path $cfDir "*.json") -ErrorAction SilentlyContinue |
		Select-String -Pattern "" -ErrorAction SilentlyContinue)
	$idFile = Get-ChildItem $cfDir -Filter "*.json" | Select-Object -First 1
	if (-not $idFile) { throw "The tunnel was created but its credentials file was not found." }
	$tunnelId = (Get-Content $idFile.FullName -Raw | ConvertFrom-Json).TunnelID

	# 3. point the domain at the tunnel
	& $cf tunnel route dns $tunnel $domain
	& $cf tunnel route dns $tunnel "www.$domain"

	# 4. write the configuration
	(Get-Content (Join-Path $PSScriptRoot "cloudflared.yml") -Raw).
		Replace("TUNNEL_ID", $tunnelId).
		Replace("CREDENTIALS_FILE", $idFile.FullName) |
		Set-Content -Path (Join-Path $cfDir "config.yml") -Encoding UTF8

	Write-Host "The tunnel is ready." -ForegroundColor Green
}

# ── the app ─────────────────────────────────────────────────────────────────
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
	throw "No virtual environment found. Run: python -m venv .venv  and then install the requirements."
}

Write-Host "Starting the app..." -ForegroundColor Cyan
$app = Start-Process -FilePath $python `
	-ArgumentList "-m", "streamlit", "run", "22_updated.py", `
		"--server.port", $port, "--server.address", "127.0.0.1", "--server.headless", "true" `
	-WorkingDirectory $root -NoNewWindow -PassThru

Start-Sleep -Seconds 6
if ($app.HasExited) {
	throw "The app did not start. Run it once by hand to see the error."
}

Write-Host ""
Write-Host "Your app is online at: https://$domain" -ForegroundColor Green
Write-Host ""

& $cf tunnel run $tunnel
