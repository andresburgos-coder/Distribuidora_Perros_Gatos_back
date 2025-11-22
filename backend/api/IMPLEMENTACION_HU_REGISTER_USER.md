# Implementación de HU_REGISTER_USER - Registro de Nuevo Cliente con Verificación de Correo

## ✅ Resumen de Implementación

Se ha implementado completamente la HU de registro de usuario con verificación de correo electrónico según las especificaciones en `HU/INSTRUCTIONS_HU_REGISTER_USER.md`.

## 📁 Archivos Creados/Modificados

### Nuevos Archivos
1. **`app/models.py`** - Modelos SQLAlchemy para `Usuario` y `VerificationCode`
2. **`IMPLEMENTACION_HU_REGISTER_USER.md`** - Este documento

### Archivos Modificados
1. **`app/routers/auth.py`** - Implementación completa de los 3 endpoints principales
2. **`app/schemas.py`** - Schemas actualizados según especificaciones de la HU
3. **`app/utils/security.py`** - Funciones para generación y hashing de códigos de verificación
4. **`app/utils/rabbitmq.py`** - Mejoras en manejo de conexión y reintentos
5. **`app/config.py`** - Configuración de rate limiting y verificación de email
6. **`app/database.py`** - Importación de modelos para creación de tablas
7. **`app/middleware/error_handler.py`** - Manejo de errores de validación con mensajes exactos
8. **`app/__init__.py`** - Importación de modelos

## 🎯 Endpoints Implementados

### 1. POST `/register`
**Estado**: ✅ Completamente implementado

**Funcionalidades**:
- ✅ Validación de campos obligatorios (email, password, nombre)
- ✅ Validación de formato de email (Pydantic EmailStr)
- ✅ Validación de contraseña según especificaciones (10+ chars, mayúscula, número, especial)
- ✅ Verificación de unicidad de email (case-insensitive)
- ✅ Hash de contraseña con bcrypt
- ✅ Creación de usuario con `is_active=False`
- ✅ Generación de código de verificación de 6 dígitos
- ✅ Hash seguro del código con HMAC-SHA256
- ✅ Almacenamiento en tabla `VerificationCodes` con expiración de 10 minutos
- ✅ Publicación en RabbitMQ cola `email.verification`
- ✅ Mensajes de respuesta exactos según especificaciones de la HU

**Mensajes de Respuesta** (exactos según HU):
- Campo faltante: `{"status": "error", "message": "Por favor, completa todos los campos obligatorios."}` (400)
- Email inválido: `{"status": "error", "message": "El correo electrónico no tiene un formato válido."}` (400)
- Contraseña inválida: `{"status": "error", "message": "La contraseña debe tener al menos 10 caracteres, incluir una mayúscula, un número y un carácter especial."}` (400)
- Email duplicado: `{"status": "error", "message": "El correo ya está registrado. ¿Deseas iniciar sesión o recuperar tu contraseña?"}` (409)
- Éxito: `{"status": "success", "message": "Por favor, Revisa tu bandeja de entrada para verificar tu cuenta e ingresa el código enviado"}` (201)

### 2. POST `/verify-email`
**Estado**: ✅ Completamente implementado

**Funcionalidades**:
- ✅ Validación de campos obligatorios
- ✅ Búsqueda de usuario por email (case-insensitive)
- ✅ Verificación de código con comparación constante en tiempo (timing-safe)
- ✅ Validación de expiración (10 minutos)
- ✅ Control de intentos de verificación (máximo 5)
- ✅ Activación de usuario (`is_active=True`)
- ✅ Marcado de código como usado
- ✅ Mensajes de respuesta exactos según especificaciones

**Mensajes de Respuesta** (exactos según HU):
- Campo faltante: `{"status": "error", "message": "Por favor, completa todos los campos obligatorios."}` (400)
- Código inválido: `{"status": "error", "message": "Código inválido."}` (400)
- Código expirado: `{"status": "error", "message": "El código ha expirado. Solicita un reenvío."}` (410)
- Éxito: `{"status": "success", "message": "Cuenta verificada exitosamente. Ya puedes iniciar sesión."}` (200)

### 3. POST `/resend-code`
**Estado**: ✅ Completamente implementado

**Funcionalidades**:
- ✅ Validación de campos obligatorios
- ✅ Verificación de existencia de usuario
- ✅ Verificación de que usuario no esté ya activo
- ✅ Rate limiting: máximo 3 reenvíos en 60 minutos
- ✅ Generación de nuevo código de verificación
- ✅ Actualización o creación de registro en `VerificationCodes`
- ✅ Publicación en RabbitMQ
- ✅ Mensajes de respuesta exactos según especificaciones

**Mensajes de Respuesta** (exactos según HU):
- Campo faltante: `{"status": "error", "message": "Por favor, completa todos los campos obligatorios."}` (400)
- Usuario no encontrado: `{"status": "error", "message": "Usuario no encontrado."}` (404)
- Rate limit excedido: `{"status": "error", "message": "Has alcanzado el número máximo de reenvíos. Intenta más tarde."}` (429)
- Éxito: `{"status": "success", "message": "Código reenviado. Revisa tu correo."}` (200)

## 🗄️ Modelos de Base de Datos

### Tabla `usuarios`
```python
- id (Integer, PK, autoincrement)
- email (String(255), unique, indexed, case-insensitive)
- password_hash (String(255))
- nombre_completo (String(100))
- cedula (String(20), nullable, indexed)
- telefono (String(20), nullable)
- direccion_envio (String(500), nullable)
- preferencia_mascotas (String(20), nullable)  # Perros, Gatos, Ambos, Ninguno
- is_active (Boolean, default=False)
- created_at (DateTime)
- updated_at (DateTime)
- ultimo_login (DateTime, nullable)
```

### Tabla `verification_codes`
```python
- id (Integer, PK, autoincrement)
- usuario_id (Integer, FK -> usuarios.id, CASCADE)
- code_hash (String(255))  # Solo hash, nunca texto plano
- expires_at (DateTime, indexed)
- attempts (Integer, default=0)
- sent_count (Integer, default=0)
- created_at (DateTime)
- is_used (Boolean, default=False)
```

## 🔐 Seguridad Implementada

1. **Hashing de Contraseñas**: bcrypt con `passlib`
2. **Hashing de Códigos**: HMAC-SHA256 con `SECRET_KEY` como clave
3. **Comparación Segura**: `hmac.compare_digest()` para prevenir timing attacks
4. **Nunca se almacena texto plano**: Solo hashes de passwords y códigos
5. **Case-insensitive email**: Búsqueda con `func.lower()` en queries
6. **Rate Limiting**: 
   - Máximo 5 intentos de verificación
   - Máximo 3 reenvíos en 60 minutos
7. **Expiración**: Códigos expiran en 10 minutos (configurable)

## 📨 Integración con RabbitMQ

**Cola**: `email.verification`

**Formato del Mensaje**:
```json
{
  "requestId": "<uuid>",
  "action": "send_verification_email",
  "payload": {
    "usuarioId": <int>,
    "email": "correo@mail.com",
    "code": "123456",
    "nombre": "Nombre Completo"
  },
  "meta": {
    "timestamp": "<iso_datetime>",
    "retry": 0
  }
}
```

**Características**:
- ✅ Mensajes persistentes (durable=True)
- ✅ Reintento automático de conexión
- ✅ No falla el registro si RabbitMQ está down
- ✅ Logging de requestId para trazabilidad

## ⚙️ Configuración Agregada

En `app/config.py`:
```python
VERIFICATION_CODE_EXPIRE_MINUTES: int = 10
MAX_VERIFICATION_ATTEMPTS: int = 5
MAX_RESEND_CODE_ATTEMPTS: int = 3
RESEND_CODE_WINDOW_MINUTES: int = 60
```

## 🧪 Pruebas Recomendadas

### 1. Registro Exitoso
```bash
POST /register
{
  "email": "test@example.com",
  "password": "ValidPass123!",
  "nombre": "Test User",
  "cedula": "12345678",
  "telefono": "+57 300 0000000",
  "direccion_envio": "Calle 123",
  "preferencia_mascotas": "Perros"
}
```

### 2. Verificación de Email
```bash
POST /verify-email
{
  "email": "test@example.com",
  "code": "123456"
}
```

### 3. Reenvío de Código
```bash
POST /resend-code
{
  "email": "test@example.com"
}
```

## 📋 Checklist de Especificaciones HU

- [x] Endpoint `POST /register` implementado con validaciones
- [x] Generación de código de verificación (6 dígitos)
- [x] Almacenamiento de `code_hash` (nunca texto plano)
- [x] `expires_at` = ahora + 10 minutos
- [x] Publicación en `email.verification` con `requestId`
- [x] Endpoint `POST /verify-email` implementado
- [x] Activación de cuenta cuando código es válido
- [x] Endpoint `POST /resend-code` con rate-limit
- [x] Mensajes de error y success exactos según HU
- [x] Política de rate-limiting implementada
- [x] Hashing seguro de passwords (bcrypt) y códigos (HMAC-SHA256)
- [x] Validación de contraseña con mensaje exacto
- [x] Validación de email case-insensitive
- [x] Control de intentos de verificación
- [x] Expiración de códigos a los 10 minutos

## 🚀 Próximos Pasos

1. **Worker de Node.js**: Implementar el consumer de RabbitMQ para enviar emails
2. **Testing**: Crear tests unitarios y de integración
3. **Migraciones**: Considerar usar Alembic para migraciones de BD
4. **Login**: Implementar el endpoint de login (HU_LOGIN_USER)
5. **Documentación**: Actualizar Swagger/OpenAPI con ejemplos

## 📝 Notas Importantes

- Los mensajes de respuesta son **exactos** según las especificaciones de la HU para compatibilidad con el frontend
- El código de verificación se incluye en el mensaje de RabbitMQ (asumiendo conexión segura)
- Si RabbitMQ falla, el registro sigue siendo exitoso (el worker puede reintentar)
- La búsqueda de email es case-insensitive usando `func.lower()`
- Los códigos se hashean con HMAC-SHA256 usando `SECRET_KEY`
- La comparación de códigos usa `hmac.compare_digest()` para prevenir timing attacks

