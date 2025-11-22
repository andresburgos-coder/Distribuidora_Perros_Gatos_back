# Guía de Inicio - Distribuidora Perros y Gatos Backend API

## Problemas Resueltos

Se han corregido los siguientes problemas para poder iniciar el proyecto:

### 1. Dependencias Instaladas
- ✅ Todas las dependencias de `requirements.txt` han sido instaladas en el entorno virtual
- ✅ Se actualizó SQLAlchemy a versión 2.0.44 para compatibilidad con Python 3.13
- ✅ Se instaló `email-validator` requerido por Pydantic para `EmailStr`
- ✅ Se instaló `pyodbc` desde wheels precompilados

### 2. Error `setup_error_handlers` Corregido
- ✅ Creado el archivo `app/middleware/error_handler.py` con la función `setup_error_handlers`
- ✅ La función maneja errores de validación, base de datos y excepciones generales
- ✅ Agregado `__init__.py` en el módulo `middleware` para permitir imports

### 3. Correcciones de Compatibilidad
- ✅ Cambiado `regex` por `pattern` en los schemas de Pydantic (compatible con Pydantic 2.x)
- ✅ Agregado import de `Request` en `app/routers/auth.py`
- ✅ Removidos emojis de los mensajes de print para compatibilidad con Windows

### 4. Manejo de Base de Datos
- ✅ Modificado `init_db()` para no fallar si no hay conexión a la base de datos
- ✅ El servidor puede iniciar sin conexión a SQL Server (útil para desarrollo)

## Cómo Iniciar el Proyecto

### Opción 1: Usando el script de inicio (Windows)
```bash
# Desde PowerShell
.\start.ps1

# O desde CMD
start.bat
```

### Opción 2: Manualmente
```bash
# Activar el entorno virtual
.\venv\Scripts\Activate.ps1  # PowerShell
# o
venv\Scripts\activate.bat     # CMD

# Iniciar el servidor
python main.py
```

### Opción 3: Directamente con Python
```bash
.\venv\Scripts\python.exe main.py
```

## Configuración

### Variables de Entorno
El proyecto usa un archivo `.env` para configuración. Las variables principales son:

- **Database**: `DB_SERVER`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Server**: `API_HOST`, `API_PORT`, `DEBUG`
- **Security**: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- **CORS**: `CORS_ORIGINS`, `ALLOWED_HOSTS`

### Nota sobre la Base de Datos
El proyecto está configurado para SQL Server. Si no tienes SQL Server configurado, el servidor iniciará pero mostrará una advertencia sobre la conexión a la base de datos.

## Verificar que Funciona

Una vez iniciado, el servidor estará disponible en:
- **URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Documentación**: http://localhost:8000/docs

Puedes verificar que funciona con:
```bash
curl http://localhost:8000/health
```

## Dependencias Principales

- FastAPI 0.104.1
- Uvicorn 0.24.0
- SQLAlchemy >=2.0.44
- Pydantic >=2.5.0
- PyODBC >=5.0.0
- Python-JOSE 3.3.0
- Passlib 1.7.4

## Próximos Pasos

1. Configurar la base de datos SQL Server si es necesario
2. Actualizar las credenciales en el archivo `.env`
3. Implementar los endpoints que están marcados como "Not implemented"

