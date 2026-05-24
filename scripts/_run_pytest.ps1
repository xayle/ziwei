Set-Location "d:\Users\Administrator\Desktop\c2"
& .venv\Scripts\python.exe -m pytest tests/ --no-cov --tb=no --timeout=60 -q --ignore=tests\e2e
Write-Host "EXIT:$LASTEXITCODE"
