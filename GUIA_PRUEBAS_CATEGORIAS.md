# 🧪 Guía de Pruebas - Gestión de Categorías y Subcategorías

## 📋 Información General

- **Base URL**: `http://localhost:8000`
- **Puerto API**: `8000` (según docker-compose.yml)
- **Formato**: JSON
- **Content-Type**: `application/json`

---

## 🚀 Endpoints Disponibles

### 1. Crear Categoría
### 2. Crear Subcategoría
### 3. Actualizar Categoría
### 4. Actualizar Subcategoría
### 5. Listar Categorías (con subcategorías)

---

## 1️⃣ CREAR CATEGORÍA

### Endpoint
```
POST http://localhost:8000/api/admin/categorias
```

### cURL (Caso Exitoso)
```bash
curl -X POST "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Perros"
  }'
```

### cURL (Error - Nombre muy corto)
```bash
curl -X POST "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "P"
  }'
```

### cURL (Error - Campo vacío)
```bash
curl -X POST "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": ""
  }'
```

### Request Body (Postman)
```json
{
  "nombre": "Perros"
}
```

### Response Exitoso (201 Created)
```json
{
  "status": "success",
  "message": "Categoría creada exitosamente"
}
```

### Response Error - Nombre muy corto (400 Bad Request)
```json
{
  "detail": {
    "status": "error",
    "message": "El nombre de la categoría debe tener al menos 2 caracteres."
  }
}
```

### Response Error - Campo vacío (400 Bad Request)
```json
{
  "detail": {
    "status": "error",
    "message": "Por favor, completa todos los campos obligatorios."
  }
}
```

---

## 2️⃣ CREAR SUBCATEGORÍA

### Endpoint
```
POST http://localhost:8000/api/admin/subcategorias
```

### cURL (Caso Exitoso)
```bash
curl -X POST "http://localhost:8000/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "categoriaId": "1",
    "nombre": "Alimentos"
  }'
```

### cURL (Error - Categoría no existe)
```bash
curl -X POST "http://localhost:8000/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "categoriaId": "999",
    "nombre": "Alimentos"
  }'
```

### cURL (Error - Campo faltante)
```bash
curl -X POST "http://localhost:8000/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Alimentos"
  }'
```

### Request Body (Postman)
```json
{
  "categoriaId": "1",
  "nombre": "Alimentos"
}
```

### Response Exitoso (201 Created)
```json
{
  "status": "success",
  "message": "Subcategoría creada exitosamente"
}
```

### Response Error - Categoría no existe (400 Bad Request)
```json
{
  "detail": {
    "status": "error",
    "message": "La categoría especificada no parece válida."
  }
}
```

### Response Error - Campo faltante (400 Bad Request)
```json
{
  "detail": {
    "status": "error",
    "message": "Por favor, completa todos los campos obligatorios."
  }
}
```

---

## 3️⃣ ACTUALIZAR CATEGORÍA

### Endpoint
```
PUT http://localhost:8000/api/admin/categorias/{id}
```

### cURL (Caso Exitoso)
```bash
curl -X PUT "http://localhost:8000/api/admin/categorias/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Perros y Gatos"
  }'
```

### cURL (Error - Nombre duplicado)
```bash
curl -X PUT "http://localhost:8000/api/admin/categorias/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Aves"
  }'
```

### Request Body (Postman)
```json
{
  "nombre": "Perros y Gatos"
}
```

### Response Exitoso (200 OK)
```json
{
  "status": "success",
  "message": "Actualización realizada correctamente"
}
```

---

## 4️⃣ ACTUALIZAR SUBCATEGORÍA

### Endpoint
```
PUT http://localhost:8000/api/admin/subcategorias/{id}
```

### cURL (Caso Exitoso)
```bash
curl -X PUT "http://localhost:8000/api/admin/subcategorias/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Alimentos Premium"
  }'
```

### Request Body (Postman)
```json
{
  "nombre": "Alimentos Premium"
}
```

### Response Exitoso (200 OK)
```json
{
  "status": "success",
  "message": "Actualización realizada correctamente"
}
```

---

## 5️⃣ LISTAR CATEGORÍAS (con subcategorías)

### Endpoint
```
GET http://localhost:8000/api/admin/categorias
```

### cURL
```bash
curl -X GET "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json"
```

### Response Exitoso (200 OK)
```json
[
  {
    "id": 1,
    "nombre": "Perros",
    "created_at": "2025-01-20T10:00:00Z",
    "updated_at": "2025-01-20T10:00:00Z",
    "subcategorias": [
      {
        "id": 1,
        "categoria_id": 1,
        "nombre": "Alimentos",
        "created_at": "2025-01-20T10:05:00Z",
        "updated_at": "2025-01-20T10:05:00Z"
      },
      {
        "id": 2,
        "categoria_id": 1,
        "nombre": "Juguetes",
        "created_at": "2025-01-20T10:10:00Z",
        "updated_at": "2025-01-20T10:10:00Z"
      }
    ]
  },
  {
    "id": 2,
    "nombre": "Gatos",
    "created_at": "2025-01-20T11:00:00Z",
    "updated_at": "2025-01-20T11:00:00Z",
    "subcategorias": []
  }
]
```

---

## 📝 Cómo Probar en Postman

### Paso 1: Configurar el Entorno
1. Abre Postman
2. Crea una nueva Collection llamada "Categorías"
3. Crea una variable de entorno:
   - Variable: `base_url`
   - Valor: `http://localhost:8000`

### Paso 2: Crear Categoría
1. **Método**: `POST`
2. **URL**: `{{base_url}}/api/admin/categorias`
3. **Headers**:
   - `Content-Type: application/json`
4. **Body** (raw JSON):
   ```json
   {
     "nombre": "Perros"
   }
   ```
5. Click en **Send**
6. Deberías recibir: `{"status": "success", "message": "Categoría creada exitosamente"}`

### Paso 3: Crear Otra Categoría
```json
{
  "nombre": "Gatos"
}
```

### Paso 4: Crear Subcategoría
1. **Método**: `POST`
2. **URL**: `{{base_url}}/api/admin/subcategorias`
3. **Body**:
   ```json
   {
     "categoriaId": "1",
     "nombre": "Alimentos"
   }
   ```

### Paso 5: Listar Todas las Categorías
1. **Método**: `GET`
2. **URL**: `{{base_url}}/api/admin/categorias`
3. Deberías ver todas las categorías con sus subcategorías

### Paso 6: Actualizar Categoría
1. **Método**: `PUT`
2. **URL**: `{{base_url}}/api/admin/categorias/1`
3. **Body**:
   ```json
   {
     "nombre": "Perros y Gatos"
   }
   ```

---

## 🧪 Casos de Prueba Completos

### Test 1: Crear Categoría Válida ✅
```bash
curl -X POST "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Aves"}'
```
**Esperado**: `{"status": "success", "message": "Categoría creada exitosamente"}`

### Test 2: Intentar Crear Categoría Duplicada ❌
```bash
curl -X POST "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Aves"}'
```
**Esperado**: El worker procesará y detectará el duplicado (case-insensitive)

### Test 3: Crear Categoría con Nombre Muy Corto ❌
```bash
curl -X POST "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "A"}'
```
**Esperado**: `{"detail": {"status": "error", "message": "El nombre de la categoría debe tener al menos 2 caracteres."}}`

### Test 4: Crear Subcategoría Válida ✅
```bash
curl -X POST "http://localhost:8000/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{"categoriaId": "1", "nombre": "Semillas"}'
```
**Esperado**: `{"status": "success", "message": "Subcategoría creada exitosamente"}`

### Test 5: Crear Subcategoría con Categoría Inexistente ❌
```bash
curl -X POST "http://localhost:8000/api/admin/subcategorias" \
  -H "Content-Type: application/json" \
  -d '{"categoriaId": "999", "nombre": "Algo"}'
```
**Esperado**: El worker detectará que la categoría no existe

### Test 6: Listar Todas las Categorías ✅
```bash
curl -X GET "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json"
```
**Esperado**: Array JSON con todas las categorías y sus subcategorías

---

## ⚠️ Notas Importantes

1. **Flujo Asíncrono**: 
   - Cuando creas/actualizas una categoría, FastAPI publica el mensaje en RabbitMQ
   - El Worker procesa el mensaje y persiste en SQL Server
   - La respuesta inmediata es de éxito, pero la validación de duplicados se hace en el Worker

2. **Validación Case-Insensitive**:
   - "Perros" = "perros" = "PERROS" (se consideran duplicados)
   - El Worker valida esto usando `LOWER(LTRIM(RTRIM(nombre)))`

3. **Verificar RabbitMQ**:
   - Puedes verificar los mensajes en: `http://localhost:15672`
   - Usuario: `guest` / Password: `guest`

4. **Verificar Logs del Worker**:
   ```bash
   docker logs distribuidora-worker
   ```

5. **Verificar Base de Datos**:
   - Conecta a SQL Server en `localhost:1433`
   - Base de datos: `DistribuidoraDB`
   - Tablas: `Categorias` y `Subcategorias`

---

## 🔍 Verificar que Todo Funciona

### 1. Verificar que la API está corriendo:
```bash
curl http://localhost:8000/health
```

### 2. Verificar que RabbitMQ está corriendo:
```bash
# Abre en navegador: http://localhost:15672
# Login: guest / guest
```

### 3. Verificar logs del Worker:
```bash
docker logs -f distribuidora-worker
```

### 4. Verificar que las tablas existen:
```sql
-- Conectar a SQL Server y ejecutar:
SELECT * FROM Categorias;
SELECT * FROM Subcategorias;
```

---

## 📦 Colección Postman Completa

Puedes importar esta colección en Postman:

```json
{
  "info": {
    "name": "Categorías API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Crear Categoría",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"nombre\": \"Perros\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/api/admin/categorias",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "admin", "categorias"]
        }
      }
    },
    {
      "name": "Crear Subcategoría",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"categoriaId\": \"1\",\n  \"nombre\": \"Alimentos\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/api/admin/subcategorias",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "admin", "subcategorias"]
        }
      }
    },
    {
      "name": "Listar Categorías",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/api/admin/categorias",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "admin", "categorias"]
        }
      }
    },
    {
      "name": "Actualizar Categoría",
      "request": {
        "method": "PUT",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"nombre\": \"Perros y Gatos\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/api/admin/categorias/1",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "admin", "categorias", "1"]
        }
      }
    },
    {
      "name": "Actualizar Subcategoría",
      "request": {
        "method": "PUT",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"nombre\": \"Alimentos Premium\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/api/admin/subcategorias/1",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "admin", "subcategorias", "1"]
        }
      }
    }
  ]
}
```

---

## ✅ Checklist de Pruebas

- [ ] Crear categoría exitosamente
- [ ] Intentar crear categoría con nombre muy corto (debe fallar)
- [ ] Intentar crear categoría duplicada (el worker debe detectarlo)
- [ ] Crear subcategoría exitosamente
- [ ] Intentar crear subcategoría con categoría inexistente (debe fallar)
- [ ] Listar todas las categorías con sus subcategorías
- [ ] Actualizar categoría exitosamente
- [ ] Actualizar subcategoría exitosamente
- [ ] Verificar en RabbitMQ que los mensajes se están publicando
- [ ] Verificar en los logs del Worker que se están procesando
- [ ] Verificar en SQL Server que los datos se están persistiendo

---

¡Listo para probar! 🚀

