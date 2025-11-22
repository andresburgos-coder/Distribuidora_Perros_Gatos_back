# Solución: Error del Contenedor SQL Server

## Problema
El contenedor de SQL Server estaba fallando con el error:
```
✘ Container sqlserver Error
Exit Code: 137
```

## Causas Identificadas

1. **Ruta incorrecta del healthcheck**: El comando `sqlcmd` estaba en `/opt/mssql-tools18/bin/sqlcmd` pero el healthcheck usaba `/opt/mssql-tools/bin/sqlcmd`
2. **Tiempo de inicio insuficiente**: SQL Server necesita más tiempo para inicializar (start_period muy corto)
3. **Falta de flag de certificado**: Necesitaba el flag `-C` para confiar en el certificado del servidor
4. **Falta de límites de memoria**: SQL Server puede consumir mucha memoria sin límites
5. **Comando incorrecto en Dockerfile**: El Dockerfile de la API usaba `app.main:app` en lugar de `main:app`

## Soluciones Aplicadas

### 1. docker-compose.yml

#### Healthcheck corregido:
```yaml
healthcheck:
  test: ["CMD-SHELL", "/opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P 'yourStrongPassword123#' -C -Q 'SELECT 1' || exit 1"]
  interval: 30s
  timeout: 20s
  retries: 10
  start_period: 120s  # Aumentado de 60s a 120s
```

#### Límites de memoria agregados:
```yaml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

#### Restart policy agregado:
```yaml
restart: unless-stopped
```

#### Variables de entorno corregidas:
- Cambiado `DB_HOST` por `DB_SERVER` para coincidir con el código
- Agregadas todas las variables de entorno necesarias
- Removida la versión obsoleta `version: '3.9'`

### 2. Dockerfile.api

Corregido el comando de inicio:
```dockerfile
# Antes:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Después:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Verificación

Para verificar que todo funciona:

```bash
# Ver estado de todos los contenedores
docker-compose ps

# Verificar healthcheck de SQL Server
docker inspect sqlserver --format='{{.State.Health.Status}}'

# Probar conexión a SQL Server
docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "yourStrongPassword123#" -C -Q "SELECT @@VERSION"

# Verificar API
curl http://localhost:8000/health
```

## Estado Actual

✅ **SQL Server**: Running (healthy)
✅ **RabbitMQ**: Running (healthy)  
✅ **API**: Running
✅ **Worker**: Running

## Comandos Útiles

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs de SQL Server
docker logs sqlserver -f

# Reiniciar solo SQL Server
docker-compose restart sqlserver

# Detener todos los servicios
docker-compose down

# Limpiar volúmenes (¡cuidado! elimina datos)
docker-compose down -v
```

## Notas Adicionales

- SQL Server puede tardar 1-2 minutos en inicializar completamente
- El healthcheck ahora espera 120 segundos antes de comenzar a verificar
- La base de datos `distribuidora_db` se crea automáticamente si no existe
- La contraseña de SA es `yourStrongPassword123#` (configurable en docker-compose.yml)

