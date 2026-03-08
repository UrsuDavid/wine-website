# Serve the website locally (Windows PowerShell)
$port = 5500
$root = $PSScriptRoot
Set-Location $root
$siteUrl = "http://localhost:$port"
Write-Host "Serving at $siteUrl" -ForegroundColor Green
Start-Process $siteUrl
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
python -m http.server $port
