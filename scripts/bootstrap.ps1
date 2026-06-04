Write-Host '== bootstrap =='
Write-Host "Python: $(python --version)"
Write-Host 'Install backend dev dependencies if needed:'
Write-Host '  python -m pip install -e "backend[dev]"'
Write-Host 'Then run: .\scripts\verify.ps1'
