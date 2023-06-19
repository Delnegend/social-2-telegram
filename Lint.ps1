Write-Host "`n=== Sorting imports ==="
isort --profile black -l 125 .
Write-Host "`n=== Formatting ==="
black .
Write-Host "`n=== Linting ===`n"
ruff . --fix --show-fixes