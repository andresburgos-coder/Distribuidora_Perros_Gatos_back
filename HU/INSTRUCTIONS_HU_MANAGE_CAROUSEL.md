# 🖼️ Instrucciones Técnicas para Implementar la HU: "Gestión de Contenido: Administrar Carrusel de la Página de Inicio"

**Objetivo**: Implementar la lógica backend para que un administrador pueda subir, eliminar y reordenar las imágenes del carrusel de la página de inicio en Distribuidora Perros y Gatos. El documento está pensado para ser leído y ejecutado por una IA o por un desarrollador backend; cada paso debe interpretarse literalmente.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — expone endpoints REST para subir imágenes, eliminar, reordenar y listar el carrusel; valida formato inicial y publica mensajes en RabbitMQ.
- Broker: RabbitMQ — colas para operaciones de creación, eliminación y reordenamiento.
- Consumer (Worker): Node.js con Express y TypeScript — consume mensajes, valida reglas de negocio, almacena archivos en sistema de archivos o CDN y persiste metadatos en SQL Server.
- Base de datos: SQL Server — persistencia de `CarruselImagenes`.
- Infraestructura: Docker & Docker Compose (servicios: `api`, `worker`, `rabbitmq`, `sqlserver`, opcional `cdn` o volumen compartido para imágenes).

---

## 🧾 Modelo de Datos (mínimo requerido en BD)
- Tabla `CarruselImagenes`:
  - `id` (GUID o bigint) — Identificador único.
  - `imagenUrl` (string) — URL pública de la imagen (CDN o ruta de archivos).
  - `thumbnailUrl` (string, opcional) — URL de miniatura si se genera.
  - `orden` (int) — Orden de aparición en el carrusel. Valores consecutivos empezando en `1`.
  - `linkUrl` (string, opcional) — (Pendiente: confirmar con el equipo) URL destino al hacer clic en la imagen.
  - `created_by` (string) — id/name del administrador que subió la imagen.
  - `created_at` (datetime)
  - `updated_at` (datetime)
  - `activo` (bit) — indica si la imagen está activa en el carrusel (true/false).

Notas:
- El campo `orden` determina la posición; menor `orden` = primera posición.
- Máximo 5 imágenes activas en el carrusel. Si se intenta añadir la 6ª imagen activa, la operación debe rechazarse con mensaje exacto (ver Mensajes de error).
- Si no existen imágenes activas, no se muestra el carrusel en frontend.

---

## 🔗 Flujo Backend (alto nivel)
1. Producer (FastAPI) recibe request del admin (upload/delete/reorder/list).
2. Producer valida inputs básicos (presencia y formato de imagen) y publica mensaje JSON en la cola RabbitMQ correspondiente.
3. Worker consume mensajes, realiza validaciones finales (conteo total de activas, unicidad de orden, validación de linkUrl si aplica), guarda el archivo (filesystem o CDN), escribe/actualiza registro en SQL Server y publica resultado de la operación.
4. Producer responde al cliente con JSON estandarizado para éxito o error (mensajes exactos para toasts en frontend).

---

## 🧩 Endpoints (Producer — FastAPI)
- **Listar imágenes del carrusel (para admin o público)**
  - Método: `GET`
  - Ruta: `/api/carrusel` (o `/api/admin/carrusel` para admin)
  - Respuesta (ejemplo):
    ```json
    { "status": "success", "data": [ { "id": "...", "imagenUrl": "...", "orden": 1, "linkUrl": "..." }, ... ] }
    ```
  - Si no hay imágenes activas, retornar `data: []`.

- **Subir imagen al carrusel**
  - Método: `POST`
  - Ruta: `/api/admin/carrusel`
  - Tipo: `multipart/form-data` con campos:
    - `imagenFile` (file) — requerido
    - `linkUrl` (string) — opcional (pendiente clarificar), si se provee validar como URL
    - `created_by` (string) — id o nombre del admin (recomendado para auditoría)
  - Validaciones iniciales en Producer:
    - `imagenFile` presente.
    - Formatos permitidos: `.jpg`, `.jpeg`, `.png`, `.svg`, `.webp`.
    - Tamaño máximo: 10 MB.
    - `created_by` presente preferente; si no, usar `unknown`.
  - Errores en Producer (HTTP 400) con mensajes JSON exactos para toast:
    - Falta campo obligatorio: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (cuando falte `imagenFile`).
    - Formato o tamaño inválido: `{ "status": "error", "message": "Formato o tamaño de imagen no válido." }`.
  - Si formato válido → publicar mensaje en la cola `carrusel.imagen.crear` con información meta (no enviar el archivo binario por RabbitMQ; en su lugar, preferible subir el archivo a un almacenamiento compartido o adjuntar el path temporal; si se incluye binario, usar mecanismo base64 y validar límites). Recomendada: la API guarda temporalmente el archivo en un volumen compartido y publica `imagenPath` en el mensaje.

- **Eliminar imagen del carrusel**
  - Método: `DELETE`
  - Ruta: `/api/admin/carrusel/{id}`
  - Producer publica mensaje en `carrusel.imagen.eliminar` con `id` y `userId`.
  - Mensajes de error/éxito estándar (para toast):
    - Éxito: `{ "status": "success", "message": "Imagen eliminada exitosamente" }`.
    - Error (no encontrada): `{ "status": "error", "message": "Imagen no encontrada." }`.

- **Reordenar imágenes del carrusel**
  - Método: `PUT`
  - Ruta: `/api/admin/carrusel/reordenar`
  - Payload (JSON): `{ "ordenes": [ { "id": "img-1", "orden": 1 }, { "id": "img-2", "orden": 2 } ] }`
  - Validaciones en Producer:
    - `ordenes` presente y no vacío.
    - Cada `orden` > 0 y entero.
    - No duplicar `orden` en la lista.
  - Mensajes de error en Producer:
    - `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (si falta `ordenes`).
    - `{ "status": "error", "message": "El orden debe ser un número entero positivo y único." }` (si hay órdenes inválidos o duplicados).
  - Si válido → publicar en `carrusel.imagen.reordenar`.
  - Respuesta esperada al cliente en éxito: `{ "status": "success", "message": "Orden actualizado exitosamente" }`.

---

## 📨 Broker & Mensajes (RabbitMQ)
- Colas sugeridas:
  - `carrusel.imagen.crear` — crear/subir imagen (mensaje incluye `imagenPath` o `imagenBase64`, `created_by`, `linkUrl` opcional, `requestId`).
  - `carrusel.imagen.eliminar` — eliminar imagen por `id`.
  - `carrusel.imagen.reordenar` — reordenar lista de ids con sus nuevos `orden`.
  - (Opcional) `carrusel.respuesta` o usar `reply-to` para confirmación síncrona.

Ejemplo de mensaje (crear):
```
{
  "requestId": "<uuid>",
  "action": "crear_imagen",
  "payload": { "imagenPath": "/tmp/uploads/img-123.png", "linkUrl": "https://...", "created_by": "admin-1" },
  "meta": { "timestamp": "<iso>" }
}
```

Reglas:
- `requestId` único por operación.
- `meta.created_by` recomendado para auditoría.
- Evitar enviar binarios grandes por RabbitMQ; preferir referencia a almacenamiento compartido.

---

## 🛠 Consumer (Worker — Node.js / TypeScript) responsabilidades
1. Conectarse a RabbitMQ y consumir `carrusel.imagen.crear`, `carrusel.imagen.eliminar`, `carrusel.imagen.reordenar`.
2. Para `crear`:
  - Validar schema del mensaje y existencia del `imagenPath` si aplica.
  - Validar nuevamente el formato y tamaño del archivo en el almacenamiento temporal.
  - Contar cuántas imágenes activas existen; si ya hay 5 imágenes activas → rechazar con error exacto: `{ "status": "error", "message": "El carrusel ya tiene el número máximo de imágenes." }`.
  - Determinar `orden` para la nueva imagen: si no se proporciona, asignar `orden = (max_orden_actual + 1)`.
  - Mover/optimizar la imagen a almacenamiento permanente (filesystem público o CDN). Generar `imagenUrl` y `thumbnailUrl` opcionales.
  - Insertar registro en `CarruselImagenes` con `imagenUrl`, `orden`, `linkUrl` (si proveído), `created_by`, `created_at`.
  - Asegurar que no existan conflictos de `orden`. Si hay colisión, realinear órdenes (reindexar) o ajustar según la política definida (preferible reindexar para mantener consecutividad 1..N).
  - Publicar respuesta de éxito: `{ "status": "success", "message": "Imagen agregada al carrusel" }`.

3. Para `eliminar`:
  - Validar existencia del `id` en DB.
  - Eliminar (o marcar `activo = false`) la fila y borrar archivo del almacenamiento permanente si corresponde.
  - Reindexar `orden` de las imágenes restantes para mantener consecutividad (opcional pero recomendado).
  - Responder con `{ "status": "success", "message": "Imagen eliminada exitosamente" }`.

4. Para `reordenar`:
  - Validar que todos los `id` existan.
  - Validar que nueva lista de `orden` no exceda 1..5.
  - Aplicar las actualizaciones en una transacción para evitar estados intermedios inconsistentes.
  - Responder: `{ "status": "success", "message": "Orden actualizado exitosamente" }`.

Mensajes de error exactos (para toast en frontend):
- Falta campo obligatorio: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }`.
- Formato/size inválido: `{ "status": "error", "message": "Formato o tamaño de imagen no válido." }`.
- Carrusel lleno: `{ "status": "error", "message": "El carrusel ya tiene el número máximo de imágenes." }`.
- Imagen no encontrada: `{ "status": "error", "message": "Imagen no encontrada." }`.

---

## ✅ Criterios de Aceptación mapeados técnicamente
- **AC 1: Subir y añadir una nueva imagen**
  - Producer valida presence y formato/tamaño, publica en `carrusel.imagen.crear`.
  - Worker valida límite (<=5), almacena la imagen y crea registro en `CarruselImagenes`.
  - Respuesta success: `{ "status":"success","message":"Imagen agregada al carrusel" }`.

- **AC 2: Eliminar una imagen**
  - Producer publica en `carrusel.imagen.eliminar`.
  - Worker marca `activo=false` o elimina físicamente y reindexa; responde con success.
  - Respuesta success: `{ "status":"success","message":"Imagen eliminada exitosamente" }`.

- **AC 3: Reordenar las imágenes**
  - Producer publica lista de `ordenes` en `carrusel.imagen.reordenar`.
  - Worker valida y aplica la nueva ordenación en transacción, responde con success.

- **AC 4: Visualización de las imágenes actuales**
  - Producer expone `GET /api/carrusel` que retorna miniaturas (`thumbnailUrl`) y `imagenUrl` con sus `orden`.
  - Si no hay imágenes activas → `data: []` (no mostrar carrusel en frontend).
  - Si hay < 5 → mostrar las existentes.

Reglas adicionales:
- Máximo 5 imágenes activas; intentar añadir más debe rechazar la operación con mensaje exacto.
- Mantener `orden` consecutivo desde 1.

---

## 🔎 Validaciones exactas (para IA sin ambigüedad)
- `imagenFile`:
  - Requerido al crear.
  - Formatos permitidos: `.jpg`, `.jpeg`, `.png`, `.svg`, `.webp`.
  - Tamaño máximo: 10 MB.
- `orden` en reordenamiento:
  - Tipo: integer, > 0.
  - Único en la lista enviada.
  - Rango permitido: 1..5.
- `linkUrl` (opcional):
  - Pendiente de confirmación del equipo. Si se acepta, validar con patrón URL (`https?://...`) y longitud razonable (<= 2048).

Mensajes estándar (texto exacto para toasts):
- Campo obligatorio faltante: `Por favor, completa todos los campos obligatorios.`
- Formato o tamaño inválido: `Formato o tamaño de imagen no válido.`
- Carrusel lleno: `El carrusel ya tiene el número máximo de imágenes.`
- Imagen no encontrada: `Imagen no encontrada.`
- Imagen agregada: `Imagen agregada al carrusel`.
- Imagen eliminada: `Imagen eliminada exitosamente`.
- Orden actualizado: `Orden actualizado exitosamente`.

---

## 🔁 Ejemplos de Payloads y Respuestas
- Ejemplo: mensaje `carrusel.imagen.crear` (cuando API publica `imagenPath` a almacenamiento compartido):
```json
{
  "requestId": "123e4567-e89b-12d3-a456-426614174000",
  "action": "crear_imagen",
  "payload": { "imagenPath": "/tmp/uploads/img-123.png", "linkUrl": "https://promo.example.com", "created_by": "admin-1" },
  "meta": { "timestamp": "2025-11-20T12:00:00Z" }
}
```
- Respuesta Worker (éxito):
```json
{ "status": "success", "message": "Imagen agregada al carrusel" }
```
- Ejemplo: reordenar (Producer -> `carrusel.imagen.reordenar`):
```json
{ "requestId": "...", "action": "reordenar", "payload": { "ordenes": [ { "id": "img-1", "orden": 2 }, { "id": "img-2", "orden": 1 } ] }, "meta": { "userId": "admin-1" } }
```
- Respuesta Worker (error carrusel lleno):
```json
{ "status": "error", "message": "El carrusel ya tiene el número máximo de imágenes." }
```

---

## 🧩 Consideraciones de implementación y operaciones
- Almacenamiento de archivos: preferible usar CDN o volumen compartido; la API guarda temporalmente y Worker mueve a almacenamiento definitivo.
- No enviar binarios grandes por RabbitMQ. Si se debe, usar chunking o base64 con límites claros.
- Concurrency: operaciones de crear/reordenar/eliminar deben ejecutarse en transacciones y con bloqueo para evitar inconsistencias en `orden`.
- Reindexado: cuando se elimina o inserta en medio, reindexar órdenes para mantener 1..N consecutivos.
- Seguridad: validar auth/roles en los endpoints Producer (solo admins pueden usar estas APIs).
- Logging y retrys: Worker debe reintentar errores transitorios y registrar `requestId` y `meta.created_by`.

---

## ✅ Checklist técnico para entrega (para que la IA verifique antes de dar la HU como completa)
- [ ] Endpoints FastAPI implementados: subir, eliminar, reordenar y listar carrusel.
- [ ] Producer valida archivo y publica en las colas correctas.
- [ ] Worker consume colas, valida límite de 5 y persiste en `CarruselImagenes` con `imagenUrl` y `orden`.
- [ ] Mensajes de error y success devueltos exactamente como se especifica (para toasts frontend).
- [ ] Reindexado de `orden` implementado al eliminar o insertar en medio.
- [ ] Manejo de concurrencia y transacciones en Worker implementado.
- [ ] (Pendiente) Decisión sobre `linkUrl` y validación de URL.

---

## 📌 Preguntas abiertas / puntos a clarificar
- ¿Se permite añadir un `linkUrl` por imagen? Si la respuesta es sí, confirmar validación (solo https, longitud máxima y si se permiten enlaces internos/externos).
- Política al subir imagen cuando ya hay 5 activas: ¿rechazar siempre o permitir reemplazar una existente (p. ej. subir y elegir cuál reemplazar)? Actualmente el documento exige rechazar y devolver error.

---

## 📌 Notas finales
- Documento exclusivo para backend. Mantener mensajes exactos para toasts en frontend.
- Colocar archivo en `HU/INSTRUCTIONS_HU_MANAGE_CAROUSEL.md`.

---

Archivo: `HU/INSTRUCTIONS_HU_MANAGE_CAROUSEL.md`
