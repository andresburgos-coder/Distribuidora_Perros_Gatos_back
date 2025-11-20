# 📦 Instrucciones Técnicas para Implementar la HU: "Gestión de Pedidos: Visualizar y Actualizar Estado de Pedidos"

**Objetivo**: Implementar la lógica backend para que un administrador pueda visualizar todos los pedidos, filtrarlos por estado, ver detalles y actualizar el estado de un pedido en Distribuidora Perros y Gatos. El documento está pensado para ser leído y ejecutado por una IA o por un desarrollador backend; cada paso debe interpretarse literalmente.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — expone endpoints REST para listar/personalizar búsquedas, obtener detalle de un pedido y solicitar la actualización de su estado; publica mensajes en RabbitMQ para operaciones que requieren procesamiento por Worker.
- Broker: RabbitMQ — cola para actualización de estado de pedidos (`pedidos.actualizar_estado`) y (opcional) `pedidos.respuesta` para confirmaciones.
- Consumer (Worker): Node.js con Express y TypeScript — consume mensajes de actualización, valida reglas de negocio y aplica cambios en SQL Server.
- Base de datos: SQL Server — tablas `Pedidos`, `PedidoItems`, `Clientes`, y `PedidosHistorialEstado` (audit).
- Infraestructura: Docker & Docker Compose (servicios: `api`, `worker`, `rabbitmq`, `sqlserver`).

---

## 🧾 Modelo de Datos (mínimo requerido en BD)
- Tabla `Pedidos`:
  - `id` (GUID o bigint) — Identificador único del pedido.
  - `cliente_id` (FK -> Clientes.id)
  - `fecha_creacion` (datetime)
  - `total` (decimal)
  - `estado` (string) — Valores permitidos: `Pendiente de envío`, `Enviado`, `Entregado`, `Cancelado`.
  - `direccion_envio` (string)
  - `last_updated_by` (string) — id/name del admin que modificó el estado por última vez.
  - `last_updated_at` (datetime)

- Tabla `PedidoItems`:
  - `id`, `pedido_id` (FK), `producto_id`, `cantidad`, `precio_unitario`.

- Tabla `Clientes` (mínimo para mostrar datos):
  - `id`, `nombre`, `email`, `telefono`, `direccion`.

- Tabla `PedidosHistorialEstado` (audit):
  - `id` (GUID o bigint)
  - `pedido_id` (FK)
  - `estado_anterior` (string)
  - `estado_nuevo` (string)
  - `userId` (string) — quien realizó el cambio
  - `comentario` (string, opcional)
  - `created_at` (datetime)

Notas:
- `estado` debe validarse y almacenarse exactamente como uno de los valores permitidos.
- Registrar siempre una fila en `PedidosHistorialEstado` cuando se actualice `estado`.

---

## 🔗 Flujo Backend (alto nivel)
1. El admin realiza peticiones a la API (FastAPI) para listar, filtrar o ver detalles.
2. Para actualizar estado, la API valida el request y publica un mensaje en RabbitMQ en la cola `pedidos.actualizar_estado`.
3. El Worker consume el mensaje, valida la existencia del pedido y la transición de estado (reglas de negocio), aplica la actualización en SQL Server dentro de una transacción, inserta registro en `PedidosHistorialEstado` y publica resultado (éxito/error) para que la API responda o lo consuma un sistema de notificaciones.
4. La API responde al cliente con JSON estandarizado con mensajes exactos para los toasts del frontend.

---

## 🧩 Endpoints (Producer — FastAPI)
- **Listar pedidos (con filtros y paginación)**
  - Método: `GET`
  - Ruta: `/api/admin/pedidos`
  - Query params (opcionales):
    - `estado` (string) — `Pendiente de envío`, `Enviado`, `Entregado`, `Cancelado`.
    - `q` (string) — búsqueda por `id` o `cliente_nombre` parcial.
    - `fechaDesde`, `fechaHasta` (ISO dates) — rango de fechas.
    - `page`, `pageSize` — paginación.
  - Respuesta (ejemplo):
    ```json
    {
      "status": "success",
      "data": [ { "id": "...", "cliente": "...", "fecha": "...", "total": 123.45, "estado": "Pendiente de envío" }, ... ],
      "meta": { "page": 1, "pageSize": 20, "total": 200 }
    }
    ```
  - Si no hay pedidos, devolver `data: []`.

- **Ver detalles de un pedido**
  - Método: `GET`
  - Ruta: `/api/admin/pedidos/{id}`
  - Respuesta: incluir `id`, `cliente` (nombre, email), `direccion_envio`, `fecha_creacion`, `total`, `estado`, y `items` con `producto`, `cantidad`, `precio_unitario`.
  - Si el pedido no existe → HTTP 404 con body exacto: `{ "status": "error", "message": "Pedido no encontrado." }`.

- **Actualizar estado de un pedido**
  - Método: `PUT`
  - Ruta: `/api/admin/pedidos/{id}/estado`
  - Payload (JSON): `{ "estado": "Enviado", "userId": "admin-1", "comentario": "Salida a transporte" }` — `comentario` opcional.
  - Validaciones iniciales en Producer:
    - `estado` presente y uno de los valores permitidos.
    - `userId` presente (recomendado para auditoría).
  - Errores en Producer (HTTP 400) con mensajes JSON exactos:
    - Faltan campos obligatorios: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }`.
    - Estado inválido: `{ "status": "error", "message": "Estado inválido." }`.
  - Si formato válido → publicar mensaje en la cola `pedidos.actualizar_estado` con `requestId`, `pedidoId`, `estado`, `userId`, `comentario` y `timestamp`.

- **Buscar por ID / cliente / rango**
  - Ya cubierto por `GET /api/admin/pedidos` con `q` y `fechaDesde`/`fechaHasta`.

---

## 📨 Broker & Mensajes (RabbitMQ)
- Cola para actualizar estado: `pedidos.actualizar_estado`.
- Cola opcional de respuesta: `pedidos.respuesta` (o uso de `reply-to` para RPC si se necesita confirmación síncrona).

Estructura de mensaje (actualizar estado):
```
{
  "requestId": "<uuid>",
  "action": "actualizar_estado",
  "payload": { "pedidoId": "<id>", "estado": "Enviado", "userId": "admin-1", "comentario": "..." },
  "meta": { "timestamp": "<iso>" }
}
```
Reglas:
- `requestId` único por operación.
- `meta.userId` recomendado para auditoría.
- Mensajes JSON UTF-8.

---

## 🛠 Consumer (Worker — Node.js / TypeScript) responsabilidades
1. Conectarse a RabbitMQ y consumir `pedidos.actualizar_estado`.
2. Por cada mensaje:
  - Validar schema (campos obligatorios: `pedidoId`, `estado`, `userId`).
  - Validar tipos y que `estado` esté en la lista permitida.
  - Validar existencia del pedido (`Pedidos.id`). Si no existe → publicar/retornar error `{ "status": "error", "message": "Pedido no encontrado." }`.
  - Validar transición de estado (reglas de negocio):
    - Recomendado: permitir solo las siguientes transiciones:
      - `Pendiente de envío` -> `Enviado`
      - `Enviado` -> `Entregado`
      - Cualquier estado -> `Cancelado` (siempre y cuando no esté `Entregado`)
    - Si la transición no está permitida → devolver `{ "status": "error", "message": "Transición de estado no permitida." }`.
  - Abrir transacción en SQL Server y realizar:
    - Leer estado actual con aislamiento/lock apropiado.
    - Actualizar `Pedidos.estado`, `last_updated_by = userId`, `last_updated_at = NOW()`.
    - Insertar registro en `PedidosHistorialEstado` con `estado_anterior`, `estado_nuevo`, `userId`, `comentario`, `created_at`.
    - Commit.
  - Publicar resultado:
    - Éxito: `{ "status": "success", "message": "Estado actualizado exitosamente" }`.
    - Errores legibles (pedido no encontrado, transición no permitida, error DB) con los mensajes exactos para toasts.
3. Auditar y loggear `requestId`, `pedidoId`, `meta.timestamp` y `userId`.
4. Reintentos: reintentar en errores transitorios y evadir duplicados con idempotencia (usar `requestId` o marcar intento procesado).

Mensajes de error exactos (para toast en frontend):
- Campo obligatorio faltante: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }`.
- Estado inválido: `{ "status": "error", "message": "Estado inválido." }`.
- Pedido no encontrado: `{ "status": "error", "message": "Pedido no encontrado." }`.
- Transición no permitida: `{ "status": "error", "message": "Transición de estado no permitida." }`.
- Éxito: `{ "status": "success", "message": "Estado actualizado exitosamente" }`.

---

## ✅ Criterios de Aceptación mapeados técnicamente
- **AC 1: Visualización de todos los pedidos**
  - Endpoint `GET /api/admin/pedidos` devuelve todos los pedidos con `id`, `cliente`, `fecha`, `total` y `estado`.
  - Respuesta formateada para paginación.

- **AC 2: Filtrar pedidos por estado**
  - `GET /api/admin/pedidos?estado=Enviado` filtra correctamente por estado.

- **AC 3: Actualizar el estado de un pedido**
  - `PUT /api/admin/pedidos/{id}/estado` valida y publica el mensaje; Worker aplica el cambio y devuelve success.
  - El frontend recibe el toast con el mensaje exacto.

- **AC 4: Ver detalles de un pedido**
  - `GET /api/admin/pedidos/{id}` muestra detalle completo: productos, cantidades, precios, dirección de envío, cliente y estado.

Reglas adicionales:
- Estados permitidos: `Pendiente de envío`, `Enviado`, `Entregado`, `Cancelado`.
- Registrar siempre auditoría en `PedidosHistorialEstado` con `userId` y `created_at`.

---

## 🔎 Validaciones exactas (para IA sin ambigüedad)
- `pedidoId`:
  - Requerido: sí (en path o payload según endpoint).
  - Debe existir en `Pedidos`.
- `estado`:
  - Requerido: sí
  - Debe ser uno de: `Pendiente de envío`, `Enviado`, `Entregado`, `Cancelado`.
- `userId`:
  - Recomendado para auditoría; si no está, guardar `system`.

Mensajes exactos para UI (toasts):
- Campo obligatorio faltante: `Por favor, completa todos los campos obligatorios.`
- Estado inválido: `Estado inválido.`
- Pedido no encontrado: `Pedido no encontrado.`
- Transición de estado no permitida: `Transición de estado no permitida.`
- Estado actualizado exitosamente: `Estado actualizado exitosamente`.

---

## 🔁 Ejemplos de Payloads y Respuestas
- Ejemplo: API publica en `pedidos.actualizar_estado`:
```json
{
  "requestId": "123e4567-e89b-12d3-a456-426614174000",
  "action": "actualizar_estado",
  "payload": { "pedidoId": "pedido-123", "estado": "Enviado", "userId": "admin-1", "comentario": "Salida a transporte" },
  "meta": { "timestamp": "2025-11-20T12:00:00Z" }
}
```
- Respuesta esperada del Worker (éxito):
```json
{ "status": "success", "message": "Estado actualizado exitosamente" }
```
- Respuesta esperada del Worker (transición inválida):
```json
{ "status": "error", "message": "Transición de estado no permitida." }
```

---

## 🧩 Consideraciones de implementación y operaciones
- Transacciones: usar transacción para leer el estado actual y escribir el nuevo estado junto con el registro en `PedidosHistorialEstado`.
- Concurrency / idempotencia: usar `requestId` para evitar procesar el mismo cambio varias veces; bloquear fila del pedido o usar nivel de aislamiento apropiado.
- Notificaciones al cliente: asunto fuera de alcance de esta HU; dejar hook/evento `pedido.estado.cambiado` para que otro servicio (notificaciones) lo consuma.
- Búsquedas: indexar `estado`, `fecha_creacion`, `cliente_id` para consultas rápidas.
- Permisos: endpoints protegidos (solo administradores).
- Logs y reintentos: Worker debe reintentar en errores transitorios y registrar `requestId` y `pedidoId`.

---

## ✅ Checklist técnico para entrega (para que la IA verifique antes de dar la HU como completa)
- [ ] Endpoint `GET /api/admin/pedidos` implementado con filtros `estado`, `q`, `fechaDesde`/`fechaHasta` y paginación.
- [ ] Endpoint `GET /api/admin/pedidos/{id}` implementado con detalle completo del pedido.
- [ ] Endpoint `PUT /api/admin/pedidos/{id}/estado` implementado; Producer valida y publica en `pedidos.actualizar_estado`.
- [ ] Worker consume `pedidos.actualizar_estado`, valida transiciones y aplica cambio en transacción.
- [ ] Registro en `PedidosHistorialEstado` por cada cambio de estado con `userId` y `created_at`.
- [ ] Mensajes de error y success devueltos exactamente como se especifica (para toasts frontend).
- [ ] Indexes y locking aplicados para rendimiento y consistencia.

---

## 📌 Preguntas abiertas / puntos a clarificar
- ¿Deseamos enviar notificaciones automáticas al cliente cuando su pedido cambia de estado? (Fuera de alcance; recomiendo publicar evento `pedido.estado.cambiado` que consuma el servicio de notificaciones.)
- ¿Permitir búsqueda avanzada (por dirección, teléfono) o suficientes `q` por id/nombre y rango de fechas?
- ¿Política para `Cancelado` después de `Entregado` (debe rechazarse)? Recomiendo no permitir `Cancelado` si `estado` es `Entregado`.

---

## 📌 Notas finales
- Documento exclusivo para la capa backend. Mantener mensajes exactos para toasts en frontend.
- Colocar archivo en `HU/INSTRUCTIONS_HU_MANAGE_ORDERS.md`.

---

Archivo: `HU/INSTRUCTIONS_HU_MANAGE_ORDERS.md`
