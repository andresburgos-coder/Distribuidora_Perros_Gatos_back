# ============================================
# Comandos cURL para Probar Gestión de Categorías (Windows PowerShell)
# Base URL: http://localhost:8000
# ============================================

$baseUrl = "http://localhost:8000"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "PRUEBAS DE GESTIÓN DE CATEGORÍAS" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# 1. CREAR CATEGORÍA - Caso Exitoso
# ============================================
Write-Host "1. Crear Categoría 'Perros'..." -ForegroundColor Yellow
$body = @{
    nombre = "Perros"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/api/admin/categorias" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
Write-Host ""

# ============================================
# 2. CREAR CATEGORÍA - Caso Exitoso
# ============================================
Write-Host "2. Crear Categoría 'Gatos'..." -ForegroundColor Yellow
$body = @{
    nombre = "Gatos"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/api/admin/categorias" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
Write-Host ""

# ============================================
# 3. CREAR CATEGORÍA - Caso Exitoso
# ============================================
Write-Host "3. Crear Categoría 'Aves'..." -ForegroundColor Yellow
$body = @{
    nombre = "Aves"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/api/admin/categorias" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
Write-Host ""

# ============================================
# 4. CREAR SUBCATEGORÍA - Caso Exitoso
# ============================================
Write-Host "4. Crear Subcategoría 'Alimentos' en categoría 1..." -ForegroundColor Yellow
$body = @{
    categoriaId = "1"
    nombre = "Alimentos"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/api/admin/subcategorias" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
Write-Host ""

# ============================================
# 5. CREAR SUBCATEGORÍA - Caso Exitoso
# ============================================
Write-Host "5. Crear Subcategoría 'Juguetes' en categoría 1..." -ForegroundColor Yellow
$body = @{
    categoriaId = "1"
    nombre = "Juguetes"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/api/admin/subcategorias" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
Write-Host ""

# ============================================
# 6. LISTAR TODAS LAS CATEGORÍAS
# ============================================
Write-Host "6. Listar todas las categorías con subcategorías..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "$baseUrl/api/admin/categorias" `
    -Method GET `
    -ContentType "application/json"

$response | ConvertTo-Json -Depth 10
Write-Host ""

# ============================================
# 7. ACTUALIZAR CATEGORÍA
# ============================================
Write-Host "7. Actualizar categoría 1..." -ForegroundColor Yellow
$body = @{
    nombre = "Perros y Gatos"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/api/admin/categorias/1" `
    -Method PUT `
    -ContentType "application/json" `
    -Body $body
Write-Host ""

# ============================================
# 8. ACTUALIZAR SUBCATEGORÍA
# ============================================
Write-Host "8. Actualizar subcategoría 1..." -ForegroundColor Yellow
$body = @{
    nombre = "Alimentos Premium"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$baseUrl/api/admin/subcategorias/1" `
    -Method PUT `
    -ContentType "application/json" `
    -Body $body
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "PRUEBAS COMPLETADAS" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

