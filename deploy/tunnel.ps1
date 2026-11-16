# Start Hassouna Green and give it a public address, free and without a domain.
#
#   .\deploy\tunnel.ps1
#
# The app keeps running on this computer; cloudflared only lends it a public
# HTTPS address. The address changes every time you start it again.
#
# Keep this window open. Ctrl+C stops both.
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$port = 8501
$cf = Join-Path $PSScriptRoot "cloudflared.exe"

if (-not (Test-Path $cf)) {
	Write-Host "Downloading cloudflared (the tunnel client)..." -ForegroundColor Cyan
	Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
		-OutFile $cf -UseBasicParsing
}

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
Write-Host "Your app is online at:" -ForegroundColor Green
Write-Host ""

& $cf tunnel --url "http://127.0.0.1:$port" --no-autoupdate
