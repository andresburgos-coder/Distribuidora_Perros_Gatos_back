# 🔧 Solución: No se crea en la Base de Datos

## ✅ Cambios Realizados

He mejorado el código del Worker para asegurar que la conexión a la base de datos esté lista antes de procesar mensajes.

### Cambios en `backend/worker/src/database.ts`:
- ✅ Agregada función `ensureConnection()` para verificar/conectar antes de usar
- ✅ Mejorado manejo de errores de conexión
- ✅ Agregado `trustServerCertificate: true` por defecto para Docker

### Cambios en `backend/worker/src/services/categorias.service.ts`:
- ✅ Agregada verificación de conexión antes de cada operación
- ✅ Mejorado logging de errores

---

## 🚀 Pasos para Solucionar el Problema

### Paso 1: Reconstruir el Worker

```bash
docker-compose build worker
docker-compose up -d worker
```

### Paso 2: Ver los Logs del Worker

```bash
docker logs -f distribuidora-worker
```

**Busca estos mensajes:**
- ✅ `Connected to MSSQL: sqlserver:1433/distribuidora_db` - Conexión exitosa
- ✅ `All consumers registered and waiting for messages` - Consumers listos
- ✅ `Received message: ...` - Mensajes recibidos
- ✅ `Category created successfully: ...` - Categoría creada

**Si ves errores:**
- ❌ `Database Connection Failed!` - Problema de conexión
- ❌ `Error creating category:` - Error al crear

### Paso 3: Verificar Variables de Entorno

```bash
docker exec distribuidora-worker env | grep DB_
```

Deberías ver:
```
DB_SERVER=sqlserver
DB_PORT=1433
DB_NAME=distribuidora_db
DB_USER=SA
DB_PASSWORD=yourStrongPassword123#
```

### Paso 4: Verificar que las Tablas Existen

Conecta a SQL Server y ejecuta:

```sql
USE DistribuidoraDB;  -- o distribuidora_db según tu configuración
GO

SELECT * FROM Categorias;
SELECT * FROM Subcategorias;
```

**Si las tablas no existen o tienen estructura incorrecta:**
Ejecuta la migración:
```sql
-- Ejecuta: sql/migrations/002_update_categorias_subcategorias.sql
```

### Paso 5: Probar Creación

```bash
curl -X POST "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Test"}'
```

Luego verifica en los logs:
```bash
docker logs --tail 20 distribuidora-worker
```

Y en la base de datos:
```sql
SELECT * FROM Categorias WHERE nombre = 'Test';
```

---

## 🔍 Diagnóstico Rápido

### Comando Todo-en-Uno:

```bash
echo "=== 1. Estado de Contenedores ==="
docker ps | grep -E "(worker|api|sqlserver|rabbitmq)"

echo ""
echo "=== 2. Logs Worker (últimas 20 líneas) ==="
docker logs --tail 20 distribuidora-worker

echo ""
echo "=== 3. Variables de Entorno Worker ==="
docker exec distribuidora-worker env | grep -E "(DB_|RABBITMQ_)"

echo ""
echo "=== 4. Verificar Conexión a BD ==="
docker exec distribuidora-worker node -e "
const mssql = require('mssql');
const config = {
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  server: process.env.DB_SERVER,
  database: process.env.DB_NAME,
  port: parseInt(process.env.DB_PORT || '1433', 10),
  options: { encrypt: true, trustServerCertificate: true }
};
mssql.connect(config).then(() => {
  console.log('✅ Conexión exitosa');
  mssql.close();
}).catch(err => {
  console.error('❌ Error:', err.message);
});
"
```

---

## ⚠️ Problemas Comunes

### Problema 1: Worker no se conecta a BD

**Síntoma:** `Database Connection Failed!` en logs

**Soluciones:**
1. Verifica que SQL Server esté corriendo:
   ```bash
   docker ps | grep sqlserver
   ```

2. Verifica el nombre de la base de datos:
   - En `docker-compose.yml`: `DB_NAME=distribuidora_db`
   - Asegúrate de que la BD exista en SQL Server

3. Verifica las credenciales:
   ```bash
   docker exec distribuidora-worker env | grep DB_
   ```

### Problema 2: Tablas no existen

**Síntoma:** Error al insertar: "Invalid object name 'Categorias'"

**Solución:**
Ejecuta la migración SQL:
```bash
# Opción 1: Desde fuera de Docker
sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -i sql/migrations/002_update_categorias_subcategorias.sql

# Opción 2: Desde dentro de Docker
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'yourStrongPassword123#' \
  -d DistribuidoraDB \
  -Q "$(cat sql/migrations/002_update_categorias_subcategorias.sql)"
```

### Problema 3: RabbitMQ no está recibiendo mensajes

**Síntoma:** La API responde éxito pero no hay mensajes en RabbitMQ

**Verificar:**
```bash
# Ver logs de la API
docker logs distribuidora-api | grep -i "categorias.crear"

# Deberías ver:
# Message published to categorias.crear: <requestId>
```

### Problema 4: Worker no está consumiendo mensajes

**Síntoma:** Hay mensajes en RabbitMQ pero no se procesan

**Verificar:**
1. Que el Worker esté corriendo
2. Que los consumers estén registrados (busca en logs: `All consumers registered`)
3. Que no haya errores en los logs

---

## 🔄 Reiniciar Todo el Sistema

Si nada funciona, reinicia todo:

```bash
# Detener todo
docker-compose down

# Reiniciar
docker-compose up -d

# Ver logs del Worker
docker logs -f distribuidora-worker
```

---

## ✅ Checklist Final

Después de aplicar los cambios, verifica:

- [ ] Worker está corriendo (`docker ps | grep worker`)
- [ ] Worker se conectó a BD (busca `Connected to MSSQL` en logs)
- [ ] Consumers están registrados (busca `All consumers registered` en logs)
- [ ] Las tablas existen en SQL Server
- [ ] El nombre de la BD coincide (`distribuidora_db` o `DistribuidoraDB`)
- [ ] No hay errores en los logs del Worker
- [ ] Los mensajes se están recibiendo (busca `Received message` en logs)
- [ ] Las categorías se están creando (busca `Category created successfully` en logs)

---

## 📞 Si Aún No Funciona

Comparte estos logs:

```bash
# Logs completos del Worker
docker logs distribuidora-worker > worker_logs.txt

# Variables de entorno
docker exec distribuidora-worker env > worker_env.txt

# Estado de contenedores
docker ps > containers_status.txt
```

Y ejecuta una prueba:
```bash
curl -X POST "http://localhost:8000/api/admin/categorias" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Test Debug"}' \
  -v > test_response.txt
```

Con estos archivos podré ayudarte a identificar el problema específico.

