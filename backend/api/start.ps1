# PowerShell script to start the API server
Write-Host "Starting Distribuidora Perros y Gatos Backend API..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment and run the server
& ".\venv\Scripts\python.exe" main.py

