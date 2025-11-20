# 🧭 Instrucciones Técnicas para Implementar la HU: "Gestión de Catálogo: Crear y Administrar Categorías y Subcategorías"

**Objetivo**: Implementar la lógica backend para que un administrador pueda crear, modificar y organizar categorías y subcategorías de productos en Distribuidora Perros y Gatos. Este documento está pensado para ser leído y ejecutado por una IA o por un desarrollador backend; cada paso debe interpretarse literalmente.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — expone endpoints REST para crear/editar categorías y subcategorías y publica mensajes en RabbitMQ.
- Broker: RabbitMQ — colas para operaciones de creación y actualización.
- Consumer (Worker): Node.js con Express y TypeScript — consume mensajes, ejecuta validaciones finales y realiza operaciones en SQL Server.
- Base de datos: SQL Server — persistencia de `categorias` y `subcategorias`.
- Infraestructura: Docker & Docker Compose (servicios: `api`, `worker`, `rabbitmq`, `db`).

---

## 🧾 Requerimientos de Datos (Modelo obligatorio en BD)
- Tabla `Categorias` (entidad principal):
  - `id` (GUID o bigint) — Identificador único.
  - `nombre` (string) — Requerido, único a nivel de categoría (case-insensitive), mínimo 2 caracteres.
  - `created_at` (datetime) — Fecha creación.
  - `updated_at` (datetime) — Fecha última modificación.
- Tabla `Subcategorias` (entidad dependiente):
  - `id` (GUID o bigint) — Identificador único.
  - `categoria_id` (FK) — Referencia a `Categorias.id`.
  - `nombre` (string) — Requerido, único dentro de la misma `categoria_id` (case-insensitive), mínimo 2 caracteres.
  - `created_at`, `updated_at` (datetime).

Notas de persistencia:
- La unicidad debe aplicarse de forma case-insensitive (ej.: `perros` == `Perros`). En SQL Server esto se logra usando una collation case-insensitive en el índice/columna o normalizando (ej. guardar `LOWER(nombre)` en una columna auxiliar con índice único).
- No establecer borrado físico en cascada para categorías/subcategorías cuando existan productos asociados; en su lugar, validar y rechazar eliminaciones.

---

## 🔗 Flujo Backend (alto nivel)
1. El Producer (FastAPI) recibe la petición REST del administrador.
2. FastAPI valida formato básico y campos obligatorios.
3. FastAPI publica un mensaje JSON en la cola de RabbitMQ correspondiente.
4. El Worker (Node.js/TypeScript) consume el mensaje, ejecuta validaciones adicionales contra la base de datos y realiza la inserción/actualización en SQL Server.
5. El Worker devuelve (por RPC o publicando en una cola de respuesta) el resultado al Producer o registra el estado para que la API lo consulte.
6. La API responde al cliente con JSON estandarizado para éxito o error.

---

## 🧩 Endpoints (Producer — FastAPI)
- **Crear categoría principal**
  - Método: `POST`
  - Ruta: `/api/admin/categorias`
  - Payload (JSON): `{ "nombre": "NombreCategoria" }`
  - Validaciones iniciales en Producer:
    - `nombre` presente y longitud >= 2.
    - No permite strings vacíos o solo espacios.
  - Si validación falla → respuesta JSON con status HTTP 400 y body exacto (para toast):
    - `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (cuando falte `nombre`).
    - `{ "status": "error", "message": "El nombre de la categoría debe tener al menos 2 caracteres." }` (cuando sea demasiado corto).
  - Si formato válido → publicar mensaje en la cola `categorias.crear` con el payload ampliado (ver sección Mensajes).

- **Crear subcategoría**
  - Método: `POST`
  - Ruta: `/api/admin/categorias/{categoriaId}/subcategorias` o `/api/admin/subcategorias`
  - Payload (JSON): `{ "categoriaId": "<id>", "nombre": "NombreSubcategoria" }`
  - Validaciones iniciales en Producer:
    - `categoriaId` presente y con formato válido.
    - `nombre` presente y longitud >= 2.
  - Errores en Producer (HTTP 400) con mensajes:
    - `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (si falta campo).
    - `{ "status": "error", "message": "La categoría especificada no parece válida." }` (si `categoriaId` con formato inválido).
  - Si formato válido → publicar mensaje en la cola `subcategorias.crear`.

- **Modificar nombre de categoría / subcategoría**
  - Método: `PUT`
  - Rutas sugeridas: `/api/admin/categorias/{id}`, `/api/admin/subcategorias/{id}`
  - Payload: `{ "nombre": "NuevoNombre" }`
  - Producer valida `nombre` y publica en `categorias.actualizar` o `subcategorias.actualizar`.

- **Borrado**
  - No se permite borrar si existen productos asociados. El Producer puede exponer `DELETE` pero el Worker debe validar y rechazar si hay productos vinculados. Mensaje de error estándar: `{ "status":"error","message":"No se permite eliminar la categoría/subcategoría porque tiene productos asociados." }`.

---

## 📨 Broker & Mensajes (RabbitMQ)
- Cola para crear categoría: `categorias.crear`
- Cola para crear subcategoría: `subcategorias.crear`
- Cola para actualizar categoría: `categorias.actualizar`
- Cola para actualizar subcategoría: `subcategorias.actualizar`
- (Opcional) Cola de respuesta/RPC: `categorias.respuesta` o usar un mecanismo de reply-to si se requiere confirmación sincrónica.

Estructura de mensaje (crear categoría):
```
{
  "requestId": "<uuid>",
  "action": "crear_categoria",
  "payload": { "nombre": "Aves" },
  "meta": { "userId": "<admin-id>", "timestamp": "<iso>" }
}
```
Estructura de mensaje (crear subcategoría):
```
{
  "requestId": "<uuid>",
  "action": "crear_subcategoria",
  "payload": { "categoriaId": "<id>", "nombre": "Juguetes" },
  "meta": { "userId": "<admin-id>", "timestamp": "<iso>" }
}
```

Reglas para mensajes:
- `requestId` debe ser único por operación para trazabilidad.
- `meta.userId` opcional pero recomendado para auditoría.
- Mensajes deben ser JSON válidos y con encoding UTF-8.

---

## 🛠 Consumer (Worker — Node.js / TypeScript) responsabilidades
1. Conectarse a RabbitMQ y consumir las colas indicadas.
2. Para cada mensaje:
  - Validación de schema (campos obligatorios, longitud mínima).
  - Validaciones lógicas y de negocio contra SQL Server:
    - **Unicidad de nombre (case-insensitive)** en el mismo nivel:
      - Para categorías → verificar que no exista otra categoría con `LOWER(nombre)` igual.
      - Para subcategorías → verificar que dentro de `categoria_id` no exista otra subcategoría con `LOWER(nombre)` igual.
    - **Existencia de la categoría** (cuando se crea una subcategoría) → si `categoriaId` no existe → error.
    - **Restricción de eliminación**: si se procesa una eliminación, comprobar si existen productos asociados (tabla `Productos`) y rechazar si hay al menos uno.
  - Si todas las validaciones pasan → insertar o actualizar en SQL Server.
  - Manejar condiciones de carrera concurrente al verificar unicidad (usar transacción + bloqueo optimista/índice único) o realizar un intento de inserción con índice único y capturar violación de unicidad.
3. Publicar resultado:
  - En caso de éxito → enviar confirmación con: `{ "status": "success", "message": "Categoría creada exitosamente" }` o mensajes equivalentes para subcategoría/actualización.
  - En caso de error → enviar: `{ "status": "error", "message": "Detalle legible para el usuario" }`.

Mensajes de error exactos (para toast en frontend):
- Nombre duplicado: `{ "status": "error", "message": "Ya existe una categoría con ese nombre." }` (para categorías)
- Subcategoría duplicada en misma categoría: `{ "status": "error", "message": "Ya existe una subcategoría con ese nombre en la categoría seleccionada." }`
- Categoría inexistente al crear subcategoría: `{ "status": "error", "message": "La categoría seleccionada no existe." }`
- Eliminación con productos: `{ "status":"error","message":"No se permite eliminar la categoría/subcategoría porque tiene productos asociados." }`

---

## ✅ Criterios de Aceptación mapeados técnicamente
- **AC 1: Creación exitosa de categoría principal**
  - Producer valida inputs y publica en `categorias.crear`.
  - Worker confirma unicidad (case-insensitive) y la inserta en `Categorias`.
  - Respuesta final al cliente: `{ "status":"success","message":"Categoría creada exitosamente" }`.

- **AC 2: Creación exitosa de subcategoría**
  - Producer valida `categoriaId` y `nombre`; publica en `subcategorias.crear`.
  - Worker valida existencia de `categoriaId` y unicidad del `nombre` dentro de esa categoría.
  - Inserta en `Subcategorias` y responde con success.

- **AC 3: Validación de nombres únicos**
  - Rechazar creación si hay duplicado al mismo nivel.
  - Mensaje de error exacto para toast indicado arriba.

- **AC 4: Visualización de la estructura de categorías**
  - Exponer endpoint (GET) en Producer para consultar árbol de categorías y subcategorías: `/api/admin/categorias` que retorna todas las categorías con su lista de subcategorías. (Producer puede leer directamente DB o consultar estado sincronizado si se requiere.)

Reglas adicionales:
- No permitir eliminación de categorías/subcategorías si existen productos asociados; solo permitir renombrar.
- No hay límite en la cantidad de categorías o subcategorías.

---

## 🔎 Validaciones exactas (para que la IA siga sin ambigüedad)
- `nombre` (categoría o subcategoría):
  - Tipo: string
  - Requerido: sí
  - Longitud mínima: 2 caracteres
  - Trim: eliminar espacios al inicio/final antes de validar longitud y unicidad
  - Comparación de unicidad: case-insensitive y trim-based (ej.: comparadores sobre `LOWER(TRIM(nombre))`).
- `categoriaId` (al crear subcategoría):
  - Requerido: sí
  - Debe existir en `Categorias`.

Mensajes al cliente (strings exactos para UI toast):
- Campo obligatorio faltante: `Por favor, completa todos los campos obligatorios.`
- Nombre demasiado corto: `El nombre debe tener al menos 2 caracteres.`
- Nombre duplicado (categoría): `Ya existe una categoría con ese nombre.`
- Nombre duplicado (subcategoría): `Ya existe una subcategoría con ese nombre en la categoría seleccionada.`
- Categoría inexistente: `La categoría seleccionada no existe.`
- Eliminación bloqueada por productos asociados: `No se permite eliminar la categoría/subcategoría porque tiene productos asociados.`

---

## 🔁 Ejemplos de Payloads
- Crear categoría (Producer envia a `categorias.crear`):
```json
{
  "requestId": "123e4567-e89b-12d3-a456-426614174000",
  "action": "crear_categoria",
  "payload": { "nombre": "Aves" },
  "meta": { "userId": "admin-1", "timestamp": "2025-11-20T12:00:00Z" }
}
```

- Crear subcategoría (Producer envia a `subcategorias.crear`):
```json
{
  "requestId": "...",
  "action": "crear_subcategoria",
  "payload": { "categoriaId": "<categoria-id>", "nombre": "Juguetes" },
  "meta": { "userId": "admin-1", "timestamp": "2025-11-20T12:01:00Z" }
}
```

- Respuesta esperada del Worker (éxito):
```json
{ "status": "success", "message": "Categoría creada exitosamente" }
```
- Respuesta esperada del Worker (error duplicado):
```json
{ "status": "error", "message": "Ya existe una categoría con ese nombre." }
```

---

## 🧩 Consideraciones de implementación y operaciones
- Concurrency: al validar unicidad en el Worker, usar transacciones o índices únicos para evitar condiciones de carrera. Si se detecta violación de índice único en inserción, devolver el mensaje de duplicado al usuario.
- Collation/normalización: para garantizar case-insensitive, establecer collation o guardar `LOWER(nombre)` en campo índice auxiliar.
- Auditoría: incluir `meta.userId` y `timestamp` en el mensaje para registrar quién realizó la operación.
- Logging y retrys: Worker debe implementar reintentos para errores transitorios y registrar fallos permanentes con el `requestId`.
- Docker: servicios recomendados en `docker-compose`: `api`, `worker`, `rabbitmq`, `sqlserver`.

---

## ✅ Checklist técnico para entrega (para que la IA verifique antes de dar la HU como completa)
- [ ] Endpoints FastAPI implementados: crear/actualizar categoría y subcategoría, listar árbol.
- [ ] Producer valida campos obligatorios y publica en las colas correctas.
- [ ] Worker consume colas y aplica validaciones de unicidad case-insensitive.
- [ ] Worker valida existencia de `categoriaId` al crear subcategoria.
- [ ] No se permite eliminación si existen productos asociados.
- [ ] Mensajes de error devueltos exactamente como se especifica (para toasts frontend).
- [ ] Tablas `Categorias` y `Subcategorias` creadas con índices para unicidad case-insensitive.
- [ ] Pruebas manuales: crear categoría, crear subcategoría, intentar duplicado, intentar eliminar con productos.

---

## 📌 Notas finales
- Este documento es exclusivo para la capa backend. No incluye implementaciones frontend ni instrucciones de UI más allá de los mensajes de toast que debe mostrar.
- Mantener mensajes de error exactamente como están escritos para consistencia con el frontend.
- Si se prefiere otra convención de nombres para colas o endpoints, documentarlo y mantenerla consistente en ambos lados (Producer y Consumer).

---

Archivo: `HU/INSTRUCTIONS_HU_MANAGE_CATEGORIES.md`
