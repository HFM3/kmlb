# kmlb docs - build the MkDocs site and zip it.
# Run from kmlb-docs/. Produces upload.zip from the built site/ folder.

$ErrorActionPreference = "Stop"

Write-Host "Building site..." -ForegroundColor Cyan
py -m mkdocs build

Write-Host "Zipping site..." -ForegroundColor Cyan
Set-Location site
tar -a -c -f ..\upload.zip *
Set-Location ..

Write-Host "Done! Upload upload.zip to Cloudflare Pages." -ForegroundColor Green
