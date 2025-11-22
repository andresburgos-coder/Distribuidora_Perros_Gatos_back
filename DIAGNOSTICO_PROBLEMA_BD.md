# 🔍 Diagnóstico: Por qué no se crea en la base de datos

## Problema Identificado

Si la API responde con éxito pero no se persiste en la base de datos, el problema está en el **Worker** (procesamiento asíncrono).

## Pasos para Diagnosticar

### 1. Verificar que el Worker está corriendo

```bash
docker ps | grep worker
```

O ver todos los contenedores:
```bash
docker ps
```

Si el worker no está corriendo:
```bash
docker-compose up -d worker
```

### 2. Ver los logs del Worker

```bash
docker logs distribuidora-worker
```

O en tiempo real:
```bash
docker logs -f distribuidora-worker
```

**Busca estos mensajes:**
- ✅ `Connected to MSSQL` - Conexión a BD exitosa
- ✅ `All consumers registered and waiting for messages` - Consumers registrados
- ✅ `Received message: ...` - Mensajes recibidos de RabbitMQ
- ✅ `Category created successfully: ...` - Categoría creada exitosamente
- ❌ `Database Connection Failed!` - Error de conexión
- ❌ `Error creating category:` - Error al crear categoría

### 3. Verificar RabbitMQ

Abre en navegador: `http://localhost:15672`
- Usuario: `guest`
- Password: `guest`

Ve a la pestaña **"Queues"** y busca:
- `categorias.crear`
- `subcategorias.crear`

**Si las colas tienen mensajes acumulados:**
- El Worker no está procesando los mensajes
- Revisa los logs del Worker para ver errores

**Si las colas están vacías:**
- Los mensajes se están procesando
- El problema puede estar en la persistencia a BD

### 4. Verificar Conexión a Base de Datos

Ejecuta este comando para verificar que el Worker puede conectarse:

```bash
docker exec -it distribuidora-worker node -e "
const mssql = require('mssql');
const config = {
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  server: process.env.DB_SERVER,
  database: process.env.DB_NAME,
  port: parseInt(process.env.DB_PORT || '1433', 10),
  options: {
    encrypt: true,
    trustServerCertificate: true
  }
};
mssql.connect(config).then(() => {
  console.log('✅ Conexión exitosa a BD');
  mssql.close();
}).catch(err => {
  console.error('❌ Error de conexión:', err.message);
  process.exit(1);
});
"
```

### 5. Verificar que las Tablas Existen

Conecta a SQL Server y ejecuta:

```sql
USE DistribuidoraDB;  -- o distribuidora_db según tu configuración
GO

SELECT * FROM Categorias;
SELECT * FROM Subcategorias;
```

**Si las tablas no existen:**
- Ejecuta el script de migración: `sql/migrations/002_update_categorias_subcategorias.sql`

### 6. Verificar Variables de Entorno del Worker

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

**⚠️ IMPORTANTE:** Verifica que `DB_NAME` coincida con el nombre de tu base de datos.

### 7. Probar Creación Manual desde el Worker

```bash
docker exec -it distribuidora-worker node -e "
const mssql = require('mssql');
const config = {
  user: 'SA',
  password: 'yourStrongPassword123#',
  server: 'sqlserver',
  database: 'distribuidora_db',
  port: 1433,
  options: {
    encrypt: true,
    trustServerCertificate: true
  }
};
mssql.connect(config).then(async (pool) => {
  const result = await pool.request()
    .input('nombre', mssql.VarChar, 'Test Manual')
    .query('INSERT INTO Categorias (nombre, created_at, updated_at) OUTPUT INSERTED.id VALUES (@nombre, GETUTCDATE(), GETUTCDATE())');
  console.log('✅ Categoría creada manualmente:', result.recordset[0]);
  await pool.close();
}).catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
"
```

---

## Problemas Comunes y Soluciones

### Problema 1: Worker no está corriendo
**Solución:**
```bash
docker-compose up -d worker
docker logs -f distribuidora-worker
```

### Problema 2: Error de conexión a BD
**Síntomas en logs:**
```
Database Connection Failed! Bad Config: ...
```

**Soluciones:**
1. Verifica que SQL Server esté corriendo:
   ```bash
   docker ps | grep sqlserver
   ```

2. Verifica las variables de entorno del Worker

3. Verifica que el nombre de la BD sea correcto

### Problema 3: Tablas no existen
**Solución:**
Ejecuta la migración:
```bash
# Conecta a SQL Server y ejecuta:
sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -i sql/migrations/002_update_categorias_subcategorias.sql
```

O desde Docker:
```bash
docker exec -i sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -d DistribuidoraDB -i /path/to/migration.sql
```

### Problema 4: Nombre de BD incorrecto
**Síntoma:** El Worker se conecta pero no encuentra las tablas

**Verificar:**
- En `docker-compose.yml`: `DB_NAME=distribuidora_db`
- En el schema SQL: puede ser `DistribuidoraDB`

**Solución:** Asegúrate de que ambos coincidan o actualiza la variable de entorno.

### Problema 5: RabbitMQ no está recibiendo mensajes
**Síntoma:** La API responde éxito pero no hay mensajes en RabbitMQ

**Verificar logs de la API:**
```bash
docker logs distribuidora-api | grep -i rabbitmq
```

**Busca:**
- `Message published to categorias.crear` ✅
- `Failed to publish message` ❌

### Problema 6: Worker no está consumiendo mensajes
**Síntoma:** Hay mensajes en RabbitMQ pero no se procesan

**Verificar:**
1. Que el Worker esté corriendo
2. Que los consumers estén registrados (busca en logs: `All consumers registered`)
3. Que no haya errores en los logs del Worker

---

## Comandos de Diagnóstico Rápido

### Ver estado completo del sistema:
```bash
echo "=== Contenedores ==="
docker ps

echo "=== Logs Worker (últimas 50 líneas) ==="
docker logs --tail 50 distribuidora-worker

echo "=== Logs API (últimas 50 líneas) ==="
docker logs --tail 50 distribuidora-api

echo "=== Variables de entorno Worker ==="
docker exec distribuidora-worker env | grep -E "(DB_|RABBITMQ_)"
```

### Reiniciar todo el sistema:
```bash
docker-compose down
docker-compose up -d
docker logs -f distribuidora-worker
```

---

## Solución Rápida (si nada funciona)

1. **Detener todo:**
   ```bash
   docker-compose down
   ```

2. **Limpiar volúmenes (opcional, solo si quieres empezar de cero):**
   ```bash
   docker-compose down -v
   ```

3. **Reiniciar:**
   ```bash
   docker-compose up -d
   ```

4. **Verificar logs:**
   ```bash
   docker logs -f distribuidora-worker
   ```

5. **Hacer una prueba:**
   ```bash
   curl -X POST "http://localhost:8000/api/admin/categorias" \
     -H "Content-Type: application/json" \
     -d '{"nombre": "Test"}'
   ```

6. **Verificar en BD:**
   ```sql
   SELECT * FROM Categorias WHERE nombre = 'Test';
   ```

---

## Checklist de Verificación

- [ ] Worker está corriendo (`docker ps`)
- [ ] Worker se conectó a BD (`Connected to MSSQL` en logs)
- [ ] Consumers están registrados (`All consumers registered` en logs)
- [ ] RabbitMQ está corriendo (puerto 15672 accesible)
- [ ] Las colas existen en RabbitMQ
- [ ] Las tablas existen en SQL Server
- [ ] El nombre de la BD coincide en todas partes
- [ ] No hay errores en los logs del Worker
- [ ] Los mensajes se están recibiendo (`Received message` en logs)

---

Si después de seguir estos pasos aún no funciona, comparte los logs del Worker y te ayudo a identificar el problema específico.

