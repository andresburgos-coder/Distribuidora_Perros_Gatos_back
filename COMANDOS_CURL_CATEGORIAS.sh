#!/bin/bash
# ============================================
# Comandos cURL para Probar Gestión de Categorías
# Base URL: http://localhost:8000
# ============================================

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "PRUEBAS DE GESTIÓN DE CATEGORÍAS"
echo "=========================================="
echo ""

# ============================================
# 1. CREAR CATEGORÍA - Caso Exitoso
# ============================================
echo "1. Crear Categoría 'Perros'..."
curl -X POST "${BASE_URL}/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Perros"
  }'
echo ""
echo ""

# ============================================
# 2. CREAR CATEGORÍA - Caso Exitoso
# ============================================
echo "2. Crear Categoría 'Gatos'..."
curl -X POST "${BASE_URL}/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Gatos"
  }'
echo ""
echo ""

# ============================================
# 3. CREAR CATEGORÍA - Caso Exitoso
# ============================================
echo "3. Crear Categoría 'Aves'..."
curl -X POST "${BASE_URL}/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Aves"
  }'
echo ""
echo ""

# ============================================
# 4. CREAR CATEGORÍA - Error: Nombre muy corto
# ============================================
echo "4. Intentar crear categoría con nombre muy corto (debe fallar)..."
curl -X POST "${BASE_URL}/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "A"
  }'
echo ""
echo ""

# ============================================
# 5. CREAR CATEGORÍA - Error: Campo vacío
# ============================================
echo "5. Intentar crear categoría con campo vacío (debe fallar)..."
curl -X POST "${BASE_URL}/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": ""
  }'
echo ""
echo ""

# ============================================
# 6. CREAR SUBCATEGORÍA - Caso Exitoso
# ============================================
echo "6. Crear Subcategoría 'Alimentos' en categoría 1..."
curl -X POST "${BASE_URL}/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "categoriaId": "1",
    "nombre": "Alimentos"
  }'
echo ""
echo ""

# ============================================
# 7. CREAR SUBCATEGORÍA - Caso Exitoso
# ============================================
echo "7. Crear Subcategoría 'Juguetes' en categoría 1..."
curl -X POST "${BASE_URL}/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "categoriaId": "1",
    "nombre": "Juguetes"
  }'
echo ""
echo ""

# ============================================
# 8. CREAR SUBCATEGORÍA - Caso Exitoso
# ============================================
echo "8. Crear Subcategoría 'Accesorios' en categoría 2..."
curl -X POST "${BASE_URL}/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "categoriaId": "2",
    "nombre": "Accesorios"
  }'
echo ""
echo ""

# ============================================
# 9. CREAR SUBCATEGORÍA - Error: Categoría inexistente
# ============================================
echo "9. Intentar crear subcategoría con categoría inexistente (debe fallar)..."
curl -X POST "${BASE_URL}/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "categoriaId": "999",
    "nombre": "Algo"
  }'
echo ""
echo ""

# ============================================
# 10. CREAR SUBCATEGORÍA - Error: Campo faltante
# ============================================
echo "10. Intentar crear subcategoría sin categoriaId (debe fallar)..."
curl -X POST "${BASE_URL}/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Alimentos"
  }'
echo ""
echo ""

# ============================================
# 11. LISTAR TODAS LAS CATEGORÍAS
# ============================================
echo "11. Listar todas las categorías con subcategorías..."
curl -X GET "${BASE_URL}/api/admin/categorias" \
  -H "Content-Type: application/json"
echo ""
echo ""

# ============================================
# 12. ACTUALIZAR CATEGORÍA
# ============================================
echo "12. Actualizar categoría 1..."
curl -X PUT "${BASE_URL}/api/admin/categorias/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Perros y Gatos"
  }'
echo ""
echo ""

# ============================================
# 13. ACTUALIZAR SUBCATEGORÍA
# ============================================
echo "13. Actualizar subcategoría 1..."
curl -X PUT "${BASE_URL}/api/admin/subcategorias/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Alimentos Premium"
  }'
echo ""
echo ""

# ============================================
# 14. INTENTAR CREAR CATEGORÍA DUPLICADA (case-insensitive)
# ============================================
echo "14. Intentar crear categoría duplicada 'perros' (minúsculas, debe fallar en worker)..."
curl -X POST "${BASE_URL}/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "perros"
  }'
echo ""
echo ""

# ============================================
# 15. INTENTAR CREAR SUBCATEGORÍA DUPLICADA
# ============================================
echo "15. Intentar crear subcategoría duplicada en misma categoría (debe fallar en worker)..."
curl -X POST "${BASE_URL}/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "categoriaId": "1",
    "nombre": "alimentos"
  }'
echo ""
echo ""

echo "=========================================="
echo "PRUEBAS COMPLETADAS"
echo "=========================================="
echo ""
echo "Nota: Los errores de duplicados se detectan en el Worker."
echo "Revisa los logs del worker para ver los mensajes de error:"
echo "docker logs distribuidora-worker"

