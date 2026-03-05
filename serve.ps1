# Serve the website locally (Windows PowerShell)
$port = 8080
$root = $PSScriptRoot
Set-Location $root
Write-Host "Serving at http://localhost:$port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
python -m http.server $port
