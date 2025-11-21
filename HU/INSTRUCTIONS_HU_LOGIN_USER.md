# 🔐 Instrucciones Técnicas para Implementar la HU: "Inicio de Sesión de Clientes Registrados"

**Objetivo**: Implementar el flujo backend seguro y robusto para que clientes registrados inicien sesión con sus credenciales, manteniendo sesiones seguras con JWT y cookies, permitiendo la persistencia/fusión de carritos y defendiendo contra accesos no autorizados. Este documento es exclusivamente backend y debe ser legible por una IA o por un desarrollador.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — endpoints REST para login, logout y refresh de tokens; validar credenciales, emitir JWTs y manejar fusión de carritos.
- Broker: RabbitMQ — opcional: `auth.events` para auditoría/analytics (login/logout/fallo) y notificaciones de seguridad.
- Consumer (Worker): Node.js/TypeScript — opcional: procesar `auth.events` (alertas, analítica, bloqueo centralizado).
- Base de datos: SQL Server — tablas `Usuarios`, `RefreshTokens`, `Carts`, `CartItems`, y auditoría `AuthEvents` (opcional).
- Infraestructura: Docker & Docker Compose (`api`, `worker` opcional, `rabbitmq` opcional, `sqlserver`).

---

## 🧾 Modelo de Datos (mínimo requerido)
- `Usuarios` (ya existente, ampliar si falta):
  - `id`, `email` (único, indexado case-insensitive), `password_hash`, `is_active` (bool), `failed_login_attempts` (int), `locked_until` (datetime nullable), `created_at`, `updated_at`.
- `RefreshTokens`:
  - `id`, `usuario_id` (FK), `token_hash`, `expires_at`, `revoked` (bool), `created_at`, `user_agent` (opcional), `ip` (opcional).
- `Carts` / `CartItems`: manejar carritos anónimos (`session_id`) y autenticados (`user_id`).
- (Opcional) `AuthEvents` para auditoría: `id`, `usuario_id`(nullable), `event_type` (`login_success`, `login_failed`, `logout`), `ip`, `user_agent`, `created_at`.

Notas:
- `email` indexado con collation case-insensitive o guardar `LOWER(email)` para unicidad.
- `RefreshTokens.token_hash` para no almacenar token en texto claro.

---

## 🔗 Flujo Backend (alto nivel)
1. Cliente envía `POST /api/auth/login` con `email` y `password` (y opcional `session_id` para carrito anónimo).
2. Producer valida campos, busca usuario por email, verifica `is_active` y que la cuenta no esté bloqueada (por `locked_until`).
3. Producer verifica `password` contra `password_hash` (bcrypt/argon2). Si éxito:
   - resetear contador `failed_login_attempts` y `locked_until`.
   - generar `access_token` (JWT) y `refresh_token` (JWT o random opaque token), almacenar hash del refresh en DB.
   - establecer cookie segura `refresh_token` con flags `HttpOnly`, `Secure`, `SameSite=Strict` o `Lax` según necesidad; devolver `access_token` en body o cookie `access_token` con `HttpOnly` si se prefiere.
   - Si existe `session_id` con carrito anónimo, fusionar carrito anónimo con carrito del usuario (ver sección de fusión).
   - (Opcional) publicar `auth.events` con `login_success`.
4. Si falla la autenticación:
   - incrementar `failed_login_attempts`; si alcanza límite (ej. 5) poner `locked_until = now() + lock_duration` (ej. 15 minutos) y responder con mensaje genérico.
   - publicar `auth.events` con `login_failed` (no incluir password).
5. Logout: `POST /api/auth/logout` invalida refresh token (marcar `revoked=true`) y borrar cookie.
6. Refresh: `POST /api/auth/refresh` usa `refresh_token` desde cookie para emitir nuevo `access_token` y, si aplica, rotar refresh token (rotación segura).

---

## 🧩 Endpoints (Producer — FastAPI)
- **Login**
  - Método: `POST`
  - Ruta: `/api/auth/login`
  - Payload (JSON): `{ "email": "correo@mail.com", "password": "P@ssw0rd!", "session_id": "<opcional>" }`
  - Validaciones iniciales:
    - `email` y `password` presentes.
  - Mensajes exactos para UI (toasts):
    - Campo obligatorio faltante: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (HTTP 400).
    - Credenciales inválidas / genérico: `{ "status": "error", "message": "Correo o contraseña incorrectos" }` (HTTP 401).
    - Cuenta no activa: `{ "status": "error", "message": "Cuenta no verificada. Revisa tu correo." }` (HTTP 403).
    - Cuenta bloqueada por múltiples intentos: `{ "status": "error", "message": "Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta más tarde." }` (HTTP 423).
    - Login exitoso: `{ "status": "success", "message": "Inicio de sesión exitoso" }` (HTTP 200). Además devolver `access_token` y setear cookie `refresh_token`.
  - Efectos:
    - Emitir `access_token` (JWT) con claims mínimos: `sub` (usuario id), `email`, `iat`, `exp` (p.ej. 15 min).
    - Generar `refresh_token` (opaque o JWT) con expiración más larga (p.ej. 7-30 días), almacenar `token_hash` en `RefreshTokens` con metadata.
    - Cookie `refresh_token` con `HttpOnly`, `Secure`, `SameSite=Strict` (o Lax según integraciones) y `Path=/api/auth/refresh` o `/`.
    - Fusionar carritos si `session_id` provisto (ver lógica abajo) y retornar info de fusión en la respuesta.

- **Logout**
  - Método: `POST`
  - Ruta: `/api/auth/logout`
  - Autenticación: `refresh_token` cookie o `Authorization: Bearer <access>`.
  - Acción: Invalidar refresh token actual en DB (`revoked=true`) y borrar cookie en la respuesta.
  - Respuesta estándar: `{ "status": "success", "message": "Cierre de sesión exitoso" }` (HTTP 200).

- **Refresh token**
  - Método: `POST`
  - Ruta: `/api/auth/refresh`
  - Uso: leer `refresh_token` desde cookie `HttpOnly`.
  - Validaciones: refresh token existe en DB, no expirado, no revocado.
  - Efectos: emitir nuevo `access_token` y, si aplica, rotar refresh token (invalidar antiguo y crear nuevo), actualizar cookie.
  - Respuesta: `{ "status": "success", "access_token": "<jwt>" }` (HTTP 200).

---

## 🔁 Fusión de carritos (reglas exactas)
- Contexto: el usuario añade items en sesión anónima (con `session_id`) antes de iniciar sesión. Al autenticar, se debe fusionar el carrito anónimo con el carrito del usuario persistente.
- Reglas de fusión:
  1. Obtener `cart_anonymous` por `session_id` y `cart_user` por `user_id`.
  2. Para cada `CartItem` en `cart_anonymous`:
     - Si el mismo `producto_id` existe en `cart_user`, sumar cantidades: `new_qty = min(stock, qty_user + qty_anon)`.
     - Si no existe, trasladar item al `cart_user` con `cantidad = min(stock, qty_anon)`.
  3. Si `new_qty` excede `stock` del producto, ajustar a `stock` y registrar en la respuesta que hubo un ajuste.
  4. Después de fusionar, eliminar `cart_anonymous`.
- Respuesta al login (ejemplo): además del token, incluir un campo `cart_merge` con `{ "merged": true, "items_adjusted": [ { "productoId": "p1", "requested": 5, "final": 3 } ] }` si aplica.
- Mensajes UI sugeridos (toasts):
  - Fusión exitosa sin ajustes: `{ "status": "success", "message": "Productos del carrito fusionados correctamente" }`.
  - Fusión con ajustes por stock: `{ "status": "warning", "message": "Algunos productos se ajustaron por disponibilidad." }`.

---

## 🔐 Seguridad y políticas de protección
- Passwords: almacenar con `bcrypt` o `argon2` (saltar + pepper si procede).
- Tokens: `access_token` corto (p.ej. 15 min), `refresh_token` largo y rotable.
- Cookies: `HttpOnly`, `Secure`, `SameSite=Strict` (o `Lax` si se necesita cross-site POST para terceros), `Path=/`.
- Rate-limiting: limitar intentos de login por IP y por cuenta (ej. 5 intentos en 15 minutos).
- Lockout: al exceder `failed_login_attempts` (ej. 5), poner `locked_until = now() + 15 minutos`.
- Logging: registrar `AuthEvents` con `requestId`, `usuario_id` (si conocido), `ip`, `user_agent`, `event_type` — no registrar passwords ni tokens en texto claro.
- Idempotencia: usar `requestId` opcional para operaciones que publiquen eventos.

---

## 📨 Broker & Mensajes (opcional)
- Cola sugerida: `auth.events` para publicar:
  - `login_success` — payload: `{ "requestId":"...", "usuarioId":"...", "ip":"...", "userAgent":"...", "timestamp":"..." }`.
  - `login_failed` — payload similar pero sin `usuarioId` si no disponible.
  - `logout` — payload con `usuarioId`.
- Uso: auditoría, alertas de seguridad, sincronización con SIEM.

---

## 🔎 Mensajes exactos para UI (toasts) — sin ambigüedad
- Campo obligatorio faltante: `Por favor, completa todos los campos obligatorios.`
- Credenciales inválidas: `Correo o contraseña incorrectos` (usar siempre mensaje genérico para no filtrar si el email existe).
- Cuenta no verificada: `Cuenta no verificada. Revisa tu correo.`
- Cuenta bloqueada temporalmente: `Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta más tarde.`
- Inicio de sesión exitoso: `Inicio de sesión exitoso`.
- Productos del carrito fusionados correctamente: `Productos del carrito fusionados correctamente`.
- Algunos productos ajustados por disponibilidad: `Algunos productos se ajustaron por disponibilidad.`
- Cierre de sesión exitoso: `Cierre de sesión exitoso`.

---

## 🔁 Ejemplos de Payloads y Respuestas
- Login (request):
```json
POST /api/auth/login
{ "email": "correo@mail.com", "password": "P@ssw0rd!", "session_id": "sess-abc" }
```
- Login (respuesta éxito): (HTTP 200, plus cookie `refresh_token` set)
```json
{ "status": "success", "message": "Inicio de sesión exitoso", "access_token": "<jwt>", "cart_merge": { "merged": true, "items_adjusted": [] } }
```
- Login (credenciales inválidas): (HTTP 401)
```json
{ "status": "error", "message": "Correo o contraseña incorrectos" }
```
- Login (cuenta no verificada): (HTTP 403)
```json
{ "status": "error", "message": "Cuenta no verificada. Revisa tu correo." }
```
- Refresh (request): cookie `refresh_token` enviada automáticamente.
- Refresh (respuesta éxito): (HTTP 200)
```json
{ "status": "success", "access_token": "<jwt>" }
```
- Logout (request): cookie `refresh_token` enviada; respuesta (HTTP 200)
```json
{ "status": "success", "message": "Cierre de sesión exitoso" }
```

---

## 🧩 Consideraciones de implementación y concurrencia
- Concurrency: actualizar `failed_login_attempts` y `locked_until` con operaciones atómicas para evitar race conditions.
- Refresh token rotation: implementar rotación para mitigar token theft: al usar refresh, invalidar token viejo y crear uno nuevo.
- Protección CSRF: si se guarda `access_token` en cookie accesible por JS, asegurar protección CSRF; preferible usar cookie `HttpOnly` para `refresh_token` y enviar `access_token` en respuesta para uso por frontend in-memory.
- Fusión de carritos: operación en transacción SQL para evitar duplicados y condiciones de carrera; verificar stock al sumar cantidades.
- Compatibilidad: SameSite y Secure deben configurarse acorde al entorno (local vs producción).

---

## ✅ Checklist técnico para entrega
- [ ] Endpoint `POST /api/auth/login` implementado con validaciones, bloqueo por intentos y emisión de tokens.
- [ ] Endpoint `POST /api/auth/logout` para invalidar refresh token y borrar cookie.
- [ ] Endpoint `POST /api/auth/refresh` implementado y seguro (rotación opcional).
- [ ] Persistencia de `RefreshTokens` con `token_hash` y lógica de revocación.
- [ ] Lógica de fusión de carritos en login implementada y respetando `stock`.
- [ ] Mensajes exactos para toast implementados en respuestas.
- [ ] Rate-limiting y lockout aplicados.
- [ ] (Opcional) Publicación de `auth.events` a RabbitMQ para auditoría.

---

## 📌 Preguntas / puntos a clarificar
- ¿Preferimos `access_token` en respuesta JSON y `refresh_token` en cookie `HttpOnly`, o ambos en `HttpOnly` cookies? (Recomendación: `access_token` en memoria + `refresh_token` HttpOnly cookie.)
- ¿Duración recomendada para `refresh_token` (7, 14 o 30 días)?
- ¿Política exacta de bloqueo (número de intentos y duración)?

---

## 📌 Notas finales
- Documento exclusivo para backend. Mantener mensajes exactos para toasts en frontend.
- Colocar archivo en `HU/INSTRUCTIONS_HU_LOGIN_USER.md`.

---

Archivo: `HU/INSTRUCTIONS_HU_LOGIN_USER.md`
