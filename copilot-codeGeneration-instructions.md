# Instrucciones de Copilot Code Generation

## Cómo Ejecutar Comandos

Para ejecutar cualquier comando de taskipy, utiliza la siguiente sintaxis:

```bash
poetry run task <nombre-del-comando>
```

Por ejemplo:

```bash
poetry run task format
```

## Comandos Disponibles

### Gestión de Código

| Comando | Descripción | Uso |
|---------|-------------|-----|
| `format` | Formatea automáticamente el código eliminando importaciones no utilizadas, ordenando las importaciones, aplicando formateo de Black con longitud de línea de 88 caracteres y formateando los docstrings | `poetry run task format` |
| `format-docs` | Formatea los docstrings para que cumplan con una longitud máxima de 88 caracteres, con una nueva línea después de las comillas triples de apertura y resumen en su propia línea | `poetry run task format-docs` |
| `check-format` | Verifica que el código cumpla con las reglas de formateo sin modificarlo | `poetry run task check-format` |
| `lint` | Ejecuta pylint para analizar la calidad del código | `poetry run task lint` |
| `clean` | Elimina archivos temporales y cachés generados durante el desarrollo | `poetry run task clean` |

### Pruebas

| Comando | Descripción | Uso |
|---------|-------------|-----|
| `test` | Ejecuta todas las pruebas unitarias con pytest en la carpeta tests/ | `poetry run task test` |
| `test-cov` | Ejecuta las pruebas y genera un informe de cobertura de código en formato terminal y HTML | `poetry run task test-cov` |

### Ejecución de la Aplicación

| Comando | Descripción | Uso |
|---------|-------------|-----|
| `serve` | Inicia el servidor FastAPI en modo desarrollo con recarga automática | `poetry run task serve` |

### Gestión de Dependencias

| Comando | Descripción | Uso |
|---------|-------------|-----|
| `deps-update` | Actualiza todas las dependencias según las restricciones del pyproject.toml | `poetry run task deps-update` |
| `deps-install` | Instala todas las dependencias definidas en el proyecto | `poetry run task deps-install` |
| `deps-add` | Añade nuevas dependencias al entorno principal | `poetry run task deps-add pandas` |
| `deps-add-dev` | Añade nuevas dependencias al grupo de desarrollo | `poetry run task deps-add-dev mypy` |

### Seguridad y Construcción

| Comando | Descripción | Uso |
|---------|-------------|-----|
| `security` | Realiza un análisis de seguridad del código usando Bandit | `poetry run task security` |
| `build` | Construye el paquete para distribución | `poetry run task build` |

### Flujos de Trabajo Combinados

| Comando | Descripción | Uso |
|---------|-------------|-----|
| `pre-commit` | Ejecuta formateo, verificación de estilo y pruebas (ideal antes de hacer commits) | `poetry run task pre-commit` |
| `check-all` | Ejecuta todas las verificaciones de calidad del código (check-format, lint y test-cov) | `poetry run task check-all` |

## Ejemplos de Flujos de Trabajo

### Desarrollo Diario

```bash
# Actualizar dependencias
poetry run task deps-update

# Iniciar el servidor de desarrollo
poetry run task serve
```

### Antes de Hacer Commit

```bash
# Formatear código y ejecutar todas las verificaciones
poetry run task pre-commit
```

### Verificación Completa del Proyecto

```bash
# Ejecutar todas las verificaciones incluida la cobertura de código
poetry run task check-all
```

### Preparar para Producción

```bash
# Verificar seguridad y construir el paquete
poetry run task security && poetry run task build
```

### Formateo de Docstrings

```bash
# Formatear solo los docstrings sin afectar el resto del código
poetry run task format-docs
```

El comando `format-docs` produce un estilo de docstring como este:

```python
def mi_funcion(param):
    """
    Descripción de la función.

    Args:
        param: Descripción del parámetro

    Returns:
        Descripción del valor de retorno
    """
    return resultado
```