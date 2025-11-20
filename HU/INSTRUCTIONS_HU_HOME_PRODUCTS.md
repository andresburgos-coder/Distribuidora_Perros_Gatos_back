# 🛍️ Instrucciones Técnicas para Implementar la HU: "Visualización y Gestión de Productos en Inicio"

**Objetivo**: Implementar la lógica backend necesaria para que clientes (autenticados y no autenticados) puedan visualizar productos organizados por categoría y subcategoría desde la página de inicio, ver detalles clave y añadir productos al carrito. El documento está orientado exclusivamente al backend y pensado para ser leído y seguido por una IA o un desarrollador backend.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — endpoints REST para listar productos por categoría/subcategoría, consultar detalle y gestionar carrito (añadir productos). La API realiza validaciones sincrónicas y puede publicar eventos de carrito en RabbitMQ.
- Broker: RabbitMQ — cola opcional `cart.events` para que el Worker procese eventos de carrito (analytics, reservados temporales, sincronizaciones).
- Consumer (Worker): Node.js con Express/TypeScript — opcional: procesa eventos de carrito, reserva stock temporal o sincroniza datos para análisis.
- Base de datos: SQL Server — tablas `Productos`, `Categorias`, `Subcategorias`, `Carts`, `CartItems`, `Usuarios`.
- Infraestructura: Docker & Docker Compose (`api`, `worker` opcional, `rabbitmq` opcional, `sqlserver`).

---

## 🧾 Modelo de Datos (mínimo requerido en BD)
- Tabla `Productos`:
  - `id` (GUID o bigint)
  - `nombre` (string)
  - `descripcion` (string)
  - `precio` (decimal)
  - `peso` (int) — gramos
  - `stock` (int) — unidades disponibles, >= 0
  - `categoria` (string) — nombre/clave de categoría
  - `subcategoria` (string)
  - `imagenUrl` (string)
  - `created_at`, `updated_at`

- Tabla `Carts`:
  - `id` (GUID or bigint)
  - `user_id` (nullable) — FK a `Usuarios` para usuarios autenticados
  - `session_id` (string, nullable) — identificador para carritos anónimos
  - `created_at`, `updated_at`

- Tabla `CartItems`:
  - `id`, `cart_id` (FK), `producto_id` (FK), `cantidad` (int)

- Tabla `Categorias` / `Subcategorias` — ya existentes según HU anteriores.

Notas:
- Soportar carritos anónimos usando `session_id` (cookie) o `cart_token` para usuarios no autenticados.
- No se descuenta `stock` al añadir al carrito por defecto; se hace al crear el pedido. Sin embargo, la API debe validar que `cantidad` <= `stock` al añadir.

---

## 🔗 Flujo Backend (alto nivel)
1. Página de inicio solicita productos al Producer (FastAPI) mediante endpoints de catálogo.
2. FastAPI consulta SQL Server y retorna productos organizados por categoría y subcategoría.
3. Al pedir "Agregar al carrito", el cliente envía petición `POST` al Producer. El Producer valida existencia del producto y stock disponible y guarda/actualiza `CartItems`.
4. Opcionalmente, el Producer publica evento en `cart.events` para que el Worker procese analytics o intentos de reservar stock temporal.
5. Si el usuario intenta proceder a comprar sin autenticarse, la API informa con mensaje exacto para mostrar toast y redirección a login.

---

## 🧩 Endpoints (Producer — FastAPI)
- **Listar productos organizados (home)**
  - Método: `GET`
  - Ruta: `/api/home/productos`
  - Query params (opcionales): `categoria`, `subcategoria`, `page`, `pageSize`.
  - Respuesta (ejemplo):
    ```json
    {
      "status": "success",
      "data": {
        "Perros": {
          "Alimento": [ { "id": "p1", "nombre": "Croquetas", "precio": 2499, "peso": 1500, "stock": 10, "imagenUrl": "..." }, ... ],
          "Accesorios": [ ... ]
        },
        "Gatos": { ... }
      }
    }
    ```
  - Si no hay productos en una categoría/subcategoría, retornar array vacío.

- **Obtener detalle de producto**
  - Método: `GET`
  - Ruta: `/api/productos/{id}`
  - Respuesta: `{ "status": "success", "data": { "id": "...", "nombre": "...", "precio": 123.45, "peso": 500, "stock": 3, "imagenUrl": "...", "descripcion": "..." } }`
  - Si no existe: `{ "status": "error", "message": "Producto no encontrado." }` (HTTP 404).

- **Añadir producto al carrito**
  - Método: `POST`
  - Ruta: `/api/cart/add`
  - Autenticación: opcional (token Bearer para usuarios autenticados). Si no autenticado, requiere `session_id` cookie o `cart_token` header.
  - Payload (JSON): `{ "productoId": "p1", "cantidad": 2 }`.
  - Validaciones en Producer (sincrónica):
    - `productoId` presente y válido.
    - `cantidad` presente y entero > 0.
    - `cantidad` <= `stock` del producto.
  - Respuestas exactas (para toast):
    - Campo obligatorio faltante: `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }` (HTTP 400).
    - Cantidad inválida: `{ "status": "error", "message": "La cantidad debe ser un número entero positivo." }` (HTTP 400).
    - Producto no encontrado: `{ "status": "error", "message": "Producto no encontrado." }` (HTTP 404).
    - Sin existencias (o insuficientes): `{ "status": "error", "message": "Sin existencias" }` (HTTP 409).
    - Éxito al agregar: `{ "status": "success", "message": "Producto agregado al carrito" }` (HTTP 200).
  - Comportamiento adicional:
    - Si el usuario no está autenticado y no se proporciona `session_id`, la API puede generar y retornar `cart_token` para el cliente (instruir poner en cookie).
    - Si `cantidad` solicitada ya existe en `CartItems` para ese `cart_id`, sumar a la cantidad previa, siempre respetando `stock`.

- **Intento de compra sin autenticación (front-end flow)**
  - Al intentar `POST /api/checkout` o `POST /api/orders` sin estar autenticado, la API debe responder HTTP 401 con body exacto: `{ "status": "error", "message": "Por favor, inicia sesión o regístrate para continuar." }`.
  - El frontend mostrará toast con ese mensaje y botón que redirige a `/login`.

- **Obtener estado del carrito**
  - Método: `GET`
  - Ruta: `/api/cart` (requiere `cart_token` o auth)
  - Respuesta: lista de items con `productoId`, `nombre`, `cantidad`, `precio`, `subtotal`.

---

## 📨 Broker & Mensajes (RabbitMQ) — Opcional
- Cola sugerida: `cart.events` — Producer publica eventos al añadir/quitar items para:
  - Analytics (recomendaciones)
  - Reservas temporales (si se implementa)
  - Sincronización con otros sistemas

Ejemplo evento (añadir al carrito):
```json
{
  "requestId": "<uuid>",
  "action": "cart_add",
  "payload": { "cartId": "<id>", "productoId": "p1", "cantidad": 2, "userId": "admin-1 or null" },
  "meta": { "timestamp": "<iso>" }
}
```
Regla: no enviar binarios ni datos sensibles por las colas.

---

## 🛠 Consumer (Worker — Node.js / TypeScript) — Opcional responsabilidades
- Consumir `cart.events` para registrar eventos en sistemas de analytics.
- Si se decide implementar reservas temporales, el Worker puede:
  - Marcar una reserva temporal decrementando `available_for_reservation` o usando una tabla `StockReservations` con `expires_at`.
  - Liberar reservas expiradas en un job periódico.
- Garantizar idempotencia usando `requestId`.

---

## 🔎 Validaciones exactas (para IA sin ambigüedad)
- `cantidad`:
  - Requerido: sí
  - Tipo: integer
  - Valor: > 0
  - Mensaje exacto si inválido: `La cantidad debe ser un número entero positivo.`
- `productoId`:
  - Requerido: sí
  - Debe existir en `Productos`.
  - Mensaje exacto si no existe: `Producto no encontrado.`
- Stock insuficiente:
  - Mensaje exacto: `Sin existencias` (usar HTTP 409 para conflicto)
- Intento de compra sin auth:
  - Mensaje exacto: `Por favor, inicia sesión o regístrate para continuar.` (HTTP 401)
- Éxito al agregar al carrito:
  - Mensaje exacto: `Producto agregado al carrito` (HTTP 200)

---

## 🔁 Ejemplos de Payloads y Respuestas
- Añadir al carrito (Producer):
```json
POST /api/cart/add
{ "productoId": "prod-123", "cantidad": 2 }
```
- Respuesta éxito:
```json
{ "status": "success", "message": "Producto agregado al carrito" }
```
- Respuesta insuficiente stock:
```json
{ "status": "error", "message": "Sin existencias" }
```
- Intento checkout sin auth:
```json
POST /api/checkout  (sin Authorization)
Response 401:
{ "status": "error", "message": "Por favor, inicia sesión o regístrate para continuar." }
```
- Ejemplo respuesta de `GET /api/home/productos` (simplificado):
```json
{ "status": "success", "data": { "Perros": { "Alimento": [ { "id":"p1","nombre":"Croquetas","precio":2499,"peso":1500,"stock":5,"imagenUrl":"..." } ] }, "Gatos": { ... } } }
```

---

## 🧩 Consideraciones de implementación y UX
- Botón "Agregar al carrito": si `stock` == 0, frontend debe mostrar botón deshabilitado o texto `Sin existencias`. Backend devuelve `Sin existencias` si cliente intenta añadir cantidad > stock.
- Carritos anónimos: usar `session_id`/`cart_token` y persistir en `Carts` para que el cliente que vuelva con la misma cookie recupere su carrito.
- Validaciones de stock deben ser hechas en Producer; Worker puede ejecutar tareas asíncronas (reservas, analytics).
- Concurrency: si se implementa reserva temporal, usar transacciones y/o tabla `StockReservations` para evitar overselling.
- Paginación y caching: aplicar paginación en listados y considerar cache (Redis/HTTP cache) para la página de inicio si es necesario para rendimiento.
- Mostrar peso en la card (convertir gramos a "X kg" en frontend); backend siempre almacena en gramos.

---

## ✅ Checklist técnico para entrega (para que la IA verifique antes de dar la HU como completa)
- [ ] Endpoint `GET /api/home/productos` implementado y devuelve productos organizados por `categoria` -> `subcategoria`.
- [ ] Endpoint `GET /api/productos/{id}` implementado con detalle y `stock`.
- [ ] Endpoint `POST /api/cart/add` implementado, valida `cantidad` y `stock`, soporta carritos anónimos mediante `session_id` o `cart_token`.
- [ ] Mensajes de error y success devueltos exactamente como se especifica (para toasts frontend).
- [ ] Botón "Agregar al carrito" funciona con carritos anónimos y autenticados.
- [ ] Indexes en `Productos.categoria`, `Productos.subcategoria` y `Productos.nombre` para consultas rápidas.
- [ ] (Opcional) `cart.events` publicado por la API para analytics/reservas si se requiere.

---

## 📌 Preguntas abiertas / puntos a clarificar
- ¿Desean bloquear stock al añadir al carrito (reservas temporales) o solo validar stock al añadir y reducir stock al crear pedido? (Recomendación: validar al añadir y reservar al checkout; si reservas temporales, definir duración y estrategia de expiración.)
- Política para carritos anónimos: ¿usar `cart_token` en cookie o depender solo del frontend para mantener localStorage? (Recomendación: emita `cart_token` y persista servidor-side.)

---

## 📌 Notas finales
- Este documento es exclusivo para backend. Mantener mensajes exactos de respuesta para que el frontend construya los toasts y comportamientos adecuados.
- Ubicación del archivo: `HU/INSTRUCTIONS_HU_HOME_PRODUCTS.md`.

---

Archivo: `HU/INSTRUCTIONS_HU_HOME_PRODUCTS.md`
