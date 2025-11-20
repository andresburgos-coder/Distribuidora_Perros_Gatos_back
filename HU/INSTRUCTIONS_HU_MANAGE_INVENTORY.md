# 🧾 Instrucciones Técnicas para Implementar la HU: "Gestión de Inventario: Reabastecer Existencias de Productos"

**Objetivo**: Implementar la lógica backend para que un administrador pueda reabastecer existencias de productos en Distribuidora Perros y Gatos. El documento está pensado para ser leído y ejecutado por una IA o por un desarrollador backend; cada paso debe interpretarse literalmente.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — expone endpoints REST para buscar productos, ver existencias actuales y solicitar reabastecimiento; publica mensajes en RabbitMQ.
- Broker: RabbitMQ — colas para operaciones de reabastecimiento/actualización de stock.
- Consumer (Worker): Node.js con Express y TypeScript — consume mensajes, valida reglas de negocio y actualiza SQL Server.
- Base de datos: SQL Server — persistencia de `Productos` y `InventarioHistorial`.
- Infraestructura: Docker & Docker Compose (servicios: `api`, `worker`, `rabbitmq`, `sqlserver`).

---

## 🧾 Modelo de Datos (mínimo requerido en BD)
- Tabla `Productos` (existente):
  - `id` (GUID o bigint) — Identificador único.
  - `nombre` (string) — Nombre del producto.
  - `stock` (int) — Existencias actuales (unidades). Debe ser >= 0.
  - `last_stock_updated_by` (string) — Identificador del último usuario que modificó el stock.
  - `last_stock_updated_at` (datetime) — Fecha y hora del último cambio.
  - otros campos del producto (precio, categoria, etc.) — no obligatorios aquí.
- Tabla `InventarioHistorial` (nuevo):
  - `id` (GUID o bigint).
  - `producto_id` (FK -> Productos.id).
  - `cantidad_anterior` (int).
  - `cantidad_cambiada` (int) — cantidad añadida (positivo) o removida (negativo) — en esta HU será positiva.
  - `cantidad_nueva` (int).
  - `userId` (string) — quien hizo la modificación.
  - `created_at` (datetime) — fecha y hora del cambio.

Notas:
- `stock` debe mantenerse entero (int) y no permitir valores negativos.
- Registrar siempre una fila en `InventarioHistorial` por cada reabastecimiento exitoso.

---

## 🔗 Flujo Backend (alto nivel)
1. Producer (FastAPI) ofrece endpoints para buscar productos, obtener existencias actuales y solicitar reabastecimiento.
2. Producer valida inputs básicos (presencia y tipo) y publica un mensaje JSON en la cola `inventario.reabastecer` cuando la solicitud es válida.
3. Worker (Node.js/TypeScript) consume `inventario.reabastecer`, valida existencia del producto y reglas de negocio adicionales, aplica la actualización en SQL Server dentro de una transacción y guarda un registro en `InventarioHistorial`.
4. Worker devuelve resultado al Producer (por RPC o publicando en una cola de respuesta) o el Producer puede consultar estado si se prefiere asincronía.
5. Producer responde al cliente con JSON estandarizado para éxito o error.

---

## 🧩 Endpoints (Producer — FastAPI)
- **Buscar producto por nombre o ID**
  - Método: `GET`
  - Ruta: `/api/admin/productos/search` (query) o `/api/admin/productos/{id}`
  - Query params: `q` (nombre parcial) o `id`.
  - Respuesta: lista de productos con `id`, `nombre`, `stock`, y otros metadatos.
  - Mensaje de error de no encontrado (si se busca por id): `{ "status": "error", "message": "Producto no encontrado." }`.

- **Ver existencias actuales**
  - Método: `GET`
  - Ruta: `/api/admin/productos/{id}/stock`
  - Respuesta: `{ "status": "success", "data": { "id": "...", "nombre": "...", "stock": 42 } }`.

- **Reabastecer existencias (solicitud del administrador)**
  - Método: `POST`
  - Ruta: `/api/admin/productos/{id}/reabastecer` o `/api/admin/inventario/reabastecer`
  - Payload (JSON): `{ "cantidad": 10 }` (cantidad a añadir; entero positivo)
  - Validaciones iniciales en Producer:
    - `cantidad` presente y es número entero > 0.
    - `id` del producto presente y con formato válido.
  - Errores en Producer (HTTP 400) con mensajes JSON exactos (para toast en frontend):
    - Campo obligatorio faltante: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (si falta `cantidad` o `id` en el body en rutas donde procede).
    - Cantidad inválida: `{ "status": "error", "message": "La cantidad debe ser un número positivo." }` (si es 0, negativa o no numérica).
    - Identificador producto inválido: `{ "status": "error", "message": "Producto no encontrado." }` (si `id` no existe, Producer puede retornar 404 o publicar y dejar que el Worker valide; se recomienda que Producer verifique formato y existencia rápida si tiene acceso a DB).
  - Si formato válido → publicar mensaje en la cola `inventario.reabastecer` con el payload ampliado (ver Mensajes).

- **Historial de inventario de un producto**
  - Método: `GET`
  - Ruta: `/api/admin/productos/{id}/inventario/historial`
  - Respuesta: lista paginada de objetos `{ "cantidad_anterior": X, "cantidad_cambiada": Y, "cantidad_nueva": Z, "userId": "...", "created_at": "..." }`.
  - El encabezado o body de la respuesta puede incluir `lastModifiedBy` y `lastModifiedAt` si se desea una vista rápida del último cambio.

---

## 📨 Broker & Mensajes (RabbitMQ)
- Cola para reabastecer: `inventario.reabastecer`
- (Opcional) Cola de respuesta: `inventario.respuesta` o uso de `reply-to` si se desea confirmación sincrónica.

Estructura de mensaje (reabastecer):
```
{
  "requestId": "<uuid>",
  "action": "reabastecer",
  "payload": { "productoId": "<id>", "cantidad": 10 },
  "meta": { "userId": "admin-1", "timestamp": "<iso>" }
}
```
Reglas:
- `requestId` único por operación para trazabilidad.
- `meta.userId` obligatorio para auditoría si está disponible.
- Mensajes deben ser JSON válidos y UTF-8.

---

## 🛠 Consumer (Worker — Node.js / TypeScript) responsabilidades
1. Conectarse a RabbitMQ y consumir la cola `inventario.reabastecer`.
2. Por cada mensaje:
  - Validar schema (campos obligatorios: `productoId`, `cantidad`).
  - Validar tipos: `cantidad` integer > 0.
  - Validar existencia del `productoId` en `Productos`.
  - Iniciar transacción en SQL Server y hacer:
    - Leer `stock` actual del producto con bloqueo apropiado para evitar condiciones de carrera (SELECT FOR UPDATE o equivalente/usar aislamiento correcto).
    - Calcular `cantidad_nueva = stock + cantidad`.
    - Actualizar `Productos.stock = cantidad_nueva`, `last_stock_updated_by = meta.userId`, `last_stock_updated_at = NOW()`.
    - Insertar fila en `InventarioHistorial` con `cantidad_anterior`, `cantidad_cambiada` (la `cantidad` del payload), `cantidad_nueva`, `userId`, `created_at`.
    - Commit.
  - Si ocurre violación (producto no existe) → rollback y devolver error.
  - Manejar errores transitorios con reintentos limitados; para errores permanentes devolver error legible.
3. Publicar resultado en cola de respuesta o en la forma acordada:
  - Éxito: `{ "status": "success", "message": "Existencias actualizadas exitosamente" }`.
  - Error (producto no encontrado): `{ "status": "error", "message": "Producto no encontrado." }`.
  - Error (cantidad inválida): `{ "status": "error", "message": "La cantidad debe ser un número positivo." }`.
4. Auditoría: incluir `requestId` y `meta.userId` en logs.

---

## ✅ Criterios de Aceptación mapeados técnicamente
- **AC 1: Reabastecimiento exitoso**
  - Producer valida inputs y publica en `inventario.reabastecer`.
  - Worker verifica existencia del producto, actualiza `stock` y registra historial.
  - Respuesta final al cliente: `{ "status": "success", "message": "Existencias actualizadas exitosamente" }`.

- **AC 2: Validación de cantidad a agregar**
  - Producer y Worker deben rechazar `cantidad` = 0, negativa o no numérica.
  - Mensaje de error exacto para toast: `{ "status": "error", "message": "La cantidad debe ser un número positivo." }`.

- **AC 3: Búsqueda y selección de producto**
  - Producer expone endpoint `GET /api/admin/productos/search?q=<texto>` que permite buscar por `nombre` o `id` y devuelve `id`, `nombre`, `stock`.

- **AC 4: Visualización de existencias actuales**
  - Producer debe devolver `stock` actual en el endpoint de detalle y antes de enviar la solicitud de reabastecimiento.
  - Además, **cuando un producto tiene mínimo 10 unidades en stock** se debe generar un toast automático (mensaje exacto para toast: `El producto tiene al menos 10 unidades en stock.`). Este toast debe poder generarse por la API o por una notificación del sistema tras la consulta del stock.

- **Historial**
  - Cada reabastecimiento crea una entrada en `InventarioHistorial` que incluye `userId` (nombre o id del administrador) y `created_at`.
  - El endpoint de historial retorna la información necesaria para mostrar: nombre de la última persona que realizó cambios y fecha/hora.

---

## 🔎 Validaciones exactas (sin ambigüedad)
- `productoId`:
  - Requerido: sí
  - Debe existir en `Productos`.
- `cantidad`:
  - Requerido: sí
  - Tipo: integer
  - Valor: > 0
  - Mensajes exactos:
    - Campo obligatorio faltante: `Por favor, completa todos los campos obligatorios.`
    - Cantidad inválida: `La cantidad debe ser un número positivo.`
    - Producto no encontrado: `Producto no encontrado.`
    - Reabastecimiento exitoso: `Existencias actualizadas exitosamente` (dentro de objeto JSON con clave `message`).
    - Toast automático cuando stock >= 10: `El producto tiene al menos 10 unidades en stock.`

---

## 🔁 Ejemplos de Payloads y Respuestas
- Ejemplo: solicitud de reabastecimiento enviada por Producer a `inventario.reabastecer`:
```json
{
  "requestId": "123e4567-e89b-12d3-a456-426614174000",
  "action": "reabastecer",
  "payload": { "productoId": "prod-123", "cantidad": 20 },
  "meta": { "userId": "admin-1", "timestamp": "2025-11-20T12:00:00Z" }
}
```
- Respuesta esperada del Worker (éxito):
```json
{ "status": "success", "message": "Existencias actualizadas exitosamente" }
```
- Respuesta esperada del Worker (error cantidad inválida):
```json
{ "status": "error", "message": "La cantidad debe ser un número positivo." }
```
- Respuesta esperada del Worker (producto no encontrado):
```json
{ "status": "error", "message": "Producto no encontrado." }
```

---

## 🧩 Consideraciones de implementación y concurrencia
- Transacciones: usar transacción por reabastecimiento para leer-modificar-escribir `stock` y para insertar `InventarioHistorial`.
- Bloqueo / condiciones de carrera: usar SELECT ... WITH (UPDLOCK) o un nivel de aislamiento apropiado para evitar pérdidas de updates concurrentes.
- Validación duplicada: Producer valida formatos y tipos; Worker vuelve a validar estrictamente contra DB.
- Reintentos: Worker debe implementar reintentos para errores transitorios (ej. timeout DB, error de red) con backoff exponencial limitado.
- Auditoría y trazabilidad: registrar `requestId`, `meta.userId`, `timestamp` en logs y en `InventarioHistorial`.

---

## ✅ Checklist técnico para entrega (para que la IA verifique antes de dar la HU como completa)
- [ ] Endpoints FastAPI implementados: buscar producto, ver stock, reabastecer, historial.
- [ ] Producer valida `cantidad` y publica en `inventario.reabastecer`.
- [ ] Worker consume `inventario.reabastecer`, valida existencia y aplica la actualización en transacción.
- [ ] Insertar registro en `InventarioHistorial` por cada reabastecimiento.
- [ ] Mensajes de error y success devueltos exactamente como se especifica (para toasts frontend).
- [ ] Endpoint de historial retorna `userId` y `created_at` para cada registro y permite ver el último usuario que modificó el inventario.
- [ ] Manejo de concurrencia y reintentos implementado en Worker.

---

## 📌 Notas finales y recomendaciones operativas
- Este documento es exclusivo para la capa backend. Mantener los mensajes exactos para toasts en frontend.
- Si se desea notificar automáticamente (toast) cuando `stock >= 10`, se puede diseñar el Producer para chequear `stock` tras la operación y emitir una notificación o publicar un evento `inventario.notificacion` con el mensaje `El producto tiene al menos 10 unidades en stock.`
- Registrar siempre `meta.userId` para auditoría. Si no hay userId, guardar `system` o `unknown`.
- Para pruebas manuales recomendamos: reabastecer producto existente, intentar reabastecer con 0 y con texto, consultar historial y verificar `last_stock_updated_by`.

---

Archivo: `HU/INSTRUCTIONS_HU_MANAGE_INVENTORY.md`
