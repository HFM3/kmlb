# kmlb docs - local preview with live reload.
# Run from kmlb-docs/. Serves the MkDocs site at http://localhost:8000.

Write-Host "Serving kmlb docs at http://localhost:8000  (Ctrl+C to stop)" -ForegroundColor Cyan
py -m mkdocs serve
