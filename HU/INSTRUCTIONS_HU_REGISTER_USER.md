# ✉️ Instrucciones Técnicas para Implementar la HU: "Registro de Nuevo Cliente con Verificación de Correo"

**Objetivo**: Implementar el flujo backend para el registro de nuevos clientes con verificación de correo electrónico en Distribuidora Perros y Gatos. Este documento está pensado para que una IA o un desarrollador backend pueda seguirlo literalmente y obtener resultados coherentes.

---

## ⚙️ Arquitectura (Backend únicamente)
- Producer (API): Python con FastAPI — expone endpoints REST para registro, verificación y reenvío de código; valida formatos y publica mensajes en RabbitMQ para envío de correo.
- Broker: RabbitMQ — cola `email.verification` para delegar envío de emails al Worker.
- Consumer (Worker): Node.js con Express/TypeScript — consume `email.verification` y envía correos (SMTP/servicio externo). Maneja reintentos y audit logs.
- Base de datos: SQL Server — tablas `Usuarios`, `VerificationCodes` (o `EmailVerifications`).
- Infraestructura: Docker & Docker Compose (`api`, `worker`, `rabbitmq`, `sqlserver`).

---

## 🧾 Modelo de Datos (mínimo requerido)
- Tabla `Usuarios`:
  - `id` (GUID o bigint)
  - `email` (string) — único, indexado (case-insensitive)
  - `password_hash` (string)
  - `nombre` (string)
  - `cedula` (string) — opcional/según país
  - `telefono` (string)
  - `direccion_envio` (string)
  - `preferencia_mascotas` (string) — `Perros`/`Gatos`/`Ambos`/`Ninguno` (opcional)
  - `is_active` (bit) — `false` hasta verificar email
  - `created_at`, `updated_at`

- Tabla `VerificationCodes` (o `EmailVerifications`):
  - `id` (GUID o bigint)
  - `usuario_id` (FK -> Usuarios.id)
  - `code_hash` (string) — almacenar sólo hash del código (no texto claro)
  - `expires_at` (datetime)
  - `attempts` (int) — conteo de intentos de verificación
  - `sent_count` (int) — cantidad de reenvíos
  - `created_at` (datetime)

Notas:
- Guardar sólo `password_hash` (bcrypt/argon2) y `code_hash` (HMAC/SHA256 con salt) para la verificación.
- Indexar `Usuarios.email` como único y case-insensitive (collation o columna normalizada `LOWER(email)` con índice único).

---

## 🔗 Flujo Backend (alto nivel)
1. Cliente envía `POST /api/auth/register` con datos del formulario.
2. Producer valida formatos y unicidad del email; si válido crea registro `Usuarios` con `is_active=false` y genera código de verificación (6 dígitos aleatorios), guarda hash en `VerificationCodes` con `expires_at = NOW() + 10 minutos`, publica mensaje en RabbitMQ `email.verification` con `requestId` y `usuario_id` (no incluir el código en logs públicos; el Worker obtiene el código seguro o la API puede incluir el código en el mensaje si el broker está protegido — preferible la API genere y pase el código al Worker dentro del mensaje con cifrado/transporte seguro).
3. Worker consume y envía el email con el código; incrementa `sent_count`.
4. API responde al cliente con mensaje de bienvenida instruyendo revisar correo y a la vista de confirmación de código.
5. Cliente envía `POST /api/auth/verify-email` con `email` (o `usuarioId`) y `code`.
6. Producer revalida y comprueba el hash del código; si válido y dentro del periodo, activa `Usuarios.is_active=true`, borra/invalidade el record en `VerificationCodes` y responde success. Si inválido o expirado, responde error con mensaje claro y opción para `POST /api/auth/resend-code`.

---

## 🧩 Endpoints (Producer — FastAPI)
- **Registro**
  - Método: `POST`
  - Ruta: `/api/auth/register`
  - Payload (JSON):
    ```json
    {
      "email": "correo@mail.com",
      "password": "P@ssw0rdSegura!",
      "nombre": "Nombre Completo",
      "cedula": "12345678",
      "telefono": "+57 300 0000000",
      "direccion_envio": "Calle 123",
      "preferencia_mascotas": "Perros"  // opcional
    }
    ```
  - Validaciones en Producer:
    - Todos los campos obligatorios deben estar presentes (al menos `email`, `password`, `nombre`).
    - `email` formato RFC-like (contiene `@` y dominio).
    - `password` cumple reglas (ver sección "Restricciones de contraseña").
    - `email` no debe existir ya en `Usuarios` (case-insensitive).
  - Respuestas exactas (para toast/UI):
    - Campo obligatorio faltante: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (HTTP 400)
    - Email inválido: `{ "status": "error", "message": "El correo electrónico no tiene un formato válido." }` (HTTP 400)
    - Contraseña inválida (ver mensaje detallado abajo): `{ "status":"error","message":"La contraseña debe tener al menos 10 caracteres, incluir una mayúscula, un número y un carácter especial." }` (HTTP 400)
    - Email duplicado: `{ "status": "error", "message": "El correo ya está registrado. ¿Deseas iniciar sesión o recuperar tu contraseña?" }` (HTTP 409)
    - Registro aceptado: `{ "status": "success", "message": "Por favor, Revisa tu bandeja de entrada para verificar tu cuenta e ingresa el código enviado" }` (HTTP 201)
  - Efectos secundarios:
    - Crear `Usuarios` (is_active=false).
    - Crear/actualizar `VerificationCodes` con nuevo código (hash) y `expires_at` = ahora + 10 minutos, `sent_count` = 1.
    - Publicar mensaje en RabbitMQ `email.verification` para que Worker envíe el correo.

- **Verificar código de correo**
  - Método: `POST`
  - Ruta: `/api/auth/verify-email`
  - Payload (JSON): `{ "email": "correo@mail.com", "code": "123456" }`
  - Validaciones en Producer:
    - Campos presentes.
    - Email existente y tiene un registro activo en `VerificationCodes`.
    - Código comparado con `code_hash` (comparación segura): si coincide y `expires_at` > now → activar usuario.
  - Respuestas exactas:
    - Campo obligatorio faltante: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (HTTP 400)
    - Código inválido: `{ "status": "error", "message": "Código inválido." }` (HTTP 400)
    - Código expirado: `{ "status": "error", "message": "El código ha expirado. Solicita un reenvío." }` (HTTP 410)
    - Verificación exitosa: `{ "status": "success", "message": "Cuenta verificada exitosamente. Ya puedes iniciar sesión." }` (HTTP 200)
  - Efectos secundarios:
    - Activar `Usuarios.is_active = true`.
    - Insertar auditoría/registro de verificación (opcional).
    - Eliminar o invalidar el registro en `VerificationCodes`.

- **Reenviar código**
  - Método: `POST`
  - Ruta: `/api/auth/resend-code`
  - Payload: `{ "email": "correo@mail.com" }`
  - Validaciones:
    - Email existe y usuario no esté ya activo.
    - Respetar rate-limit: permitir reenvío máximo (ej. 3) en un periodo de X minutos (configurable).
  - Respuestas exactas:
    - Reenvío exitoso: `{ "status": "success", "message": "Código reenviado. Revisa tu correo." }` (HTTP 200)
    - Reenvío bloqueado por límite: `{ "status": "error", "message": "Has alcanzado el número máximo de reenvíos. Intenta más tarde." }` (HTTP 429)
    - Si no existe usuario: `{ "status": "error", "message": "Usuario no encontrado." }` (HTTP 404)
  - Efectos:
    - Generar nuevo código (o reutilizar el actual cambiando `expires_at`), incrementar `sent_count`, publicar mensaje `email.verification`.

---

## 🔐 Restricciones de contraseña (reglas exactas)
- Longitud mínima: 10 caracteres
- Debe contener al menos una letra mayúscula (A-Z)
- Debe contener al menos un número (0-9)
- Debe contener al menos un carácter especial (por ejemplo: !@#$%^&*)
- Mensaje exacto para toast cuando falla: `{ "status":"error","message":"La contraseña debe tener al menos 10 caracteres, incluir una mayúscula, un número y un carácter especial." }`

---

## 📨 Broker & Mensajes (RabbitMQ)
- Cola: `email.verification`
- Mensaje (ejemplo):
  ```json
  {
    "requestId": "<uuid>",
    "action": "send_verification_email",
    "payload": { "usuarioId": "<id>", "email": "correo@mail.com", "code": "123456" },
    "meta": { "timestamp": "<iso>", "retry": 0 }
  }
  ```
- Reglas:
  - `requestId` único por operación para idempotencia.
  - El `code` puede incluirse en el mensaje si la conexión al broker y al worker es segura; preferible cifrar o permitir que la API entregue el código a Worker a través de canal seguro.
  - Worker no debe loggear el `code` en texto claro en logs accesibles.
  - Worker debe implementar reintentos exponenciales solo para errores transitorios (no reintentar si la dirección es claramente inválida).

---

## 🛠 Consumer (Worker — Node.js / TypeScript) responsabilidades
1. Consumir `email.verification`.
2. Construir y enviar el email (usar plantilla con código de 6 dígitos y tiempo de expiración de 10 minutos).
3. Incrementar `sent_count` en `VerificationCodes` o en el DB mediante API/consulta.
4. Registrar evento de envío en logs y en tabla de auditoría (sin incluir el código en texto claro).
5. Manejar reintentos y backoff; respetar `sent_count` y política de rate-limit.
6. No exponer códigos en logs; en su lugar loggear `requestId`, `usuarioId`, `timestamp` y `status`.

---

## 🔎 Validaciones exactas y mensajes para UI (sin ambigüedad)
- Campo obligatorio faltante: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }`
- Email inválido: `{ "status": "error", "message": "El correo electrónico no tiene un formato válido." }`
- Contraseña inválida: `{ "status":"error","message":"La contraseña debe tener al menos 10 caracteres, incluir una mayúscula, un número y un carácter especial." }`
- Email duplicado: `{ "status": "error", "message": "El correo ya está registrado. ¿Deseas iniciar sesión o recuperar tu contraseña?" }`
- Registro aceptado (mensaje de bienvenida / instrucción): `{ "status": "success", "message": "Por favor, Revisa tu bandeja de entrada para verificar tu cuenta e ingresa el código enviado" }`
- Código inválido: `{ "status": "error", "message": "Código inválido." }`
- Código expirado: `{ "status": "error", "message": "El código ha expirado. Solicita un reenvío." }`
- Reenvío successful: `{ "status": "success", "message": "Código reenviado. Revisa tu correo." }`
- Reenvío bloqueado: `{ "status": "error", "message": "Has alcanzado el número máximo de reenvíos. Intenta más tarde." }`

---

## 🔁 Ejemplos de Payloads y Respuestas
- Registro exitoso (request):
```json
POST /api/auth/register
{
  "email": "correo@mail.com",
  "password": "P@ssw0rdSegura!",
  "nombre": "Ana Perez",
  "cedula": "12345678",
  "telefono": "+57 300 0000000",
  "preferencia_mascotas": "Perros"
}
```
- Respuesta (éxito):
```json
{ "status": "success", "message": "Por favor, Revisa tu bandeja de entrada para verificar tu cuenta e ingresa el código enviado" }
```

- Verificación (request):
```json
POST /api/auth/verify-email
{ "email": "correo@mail.com", "code": "123456" }
```
- Respuesta (éxito):
```json
{ "status": "success", "message": "Cuenta verificada exitosamente. Ya puedes iniciar sesión." }
```

- Reenvío (request):
```json
POST /api/auth/resend-code
{ "email": "correo@mail.com" }
```
- Respuesta (reenvío exitoso):
```json
{ "status": "success", "message": "Código reenviado. Revisa tu correo." }
```

---

## 🧩 Consideraciones de seguridad y operativas
- Almacenamiento: nunca guardar códigos en texto plano; almacenar sólo hashes y comparar con función segura.
- Rate-limiting: proteger endpoints `register` y `resend-code` contra abuso: por IP y por cuenta (`sent_count` max 3 por hora, configurable).
- Idempotencia: usar `requestId` para evitar enviar múltiples correos por la misma operación.
- Logs: no incluir `password` ni `code` en logs. Registrar `requestId`, `usuarioId`, `email`, `status`.
- Expiración: los códigos expiran a los 10 minutos; si expira, permitir generar uno nuevo mediante `resend-code`.
- Reglas de bloqueo: si `attempts` de verificación excede (ej. 5) bloquear nuevas verificaciones temporalmente y requerir reenvío.
- Seguridad de correo: usar proveedor confiable (SendGrid, SES) y validaciones de SPF/DKIM para entregabilidad.

---

## ✅ Checklist técnico para entrega
- [ ] Endpoint `POST /api/auth/register` implementado con validaciones y creación de usuario (`is_active=false`).
- [ ] Generación de código de verificación (6 dígitos), almacenamiento de `code_hash` y `expires_at` = ahora + 10 minutos.
- [ ] Publicación en `email.verification` con `requestId` y payload seguro.
- [ ] Worker implementado para enviar el correo y registrar `sent_count`.
- [ ] Endpoint `POST /api/auth/verify-email` implementado y activa la cuenta cuando el código es válido.
- [ ] Endpoint `POST /api/auth/resend-code` implementado con rate-limit y mensajes exactos.
- [ ] Mensajes de error y success devueltos exactamente como se especifica (para toasts frontend).
- [ ] Política de rate-limiting y bloqueo por intentos implementada.
- [ ] Hashing seguro de passwords y códigos implementado.

---

## 📌 Preguntas / puntos a clarificar (si el equipo desea responder)
- ¿Desean código numérico de 6 dígitos o token alfanumérico más largo? (Recomendado: 6 dígitos para UX, token alfanumérico para enlaces de verificación)
- ¿Permitir verificación mediante link (token en URL) además del código numérico? (si se permite, generar token único y expiración equivalente)
- ¿Cuál es la política exacta de reintentos/reenvíos (ej. máximo 3 reenvíos por hora)?

---

## 📌 Notas finales
- Documento exclusivo para backend; los mensajes exactos aquí deben usarse por el frontend para los toasts.
- Ubicación del archivo: `HU/INSTRUCTIONS_HU_REGISTER_USER.md`.

---

Archivo: `HU/INSTRUCTIONS_HU_REGISTER_USER.md`
