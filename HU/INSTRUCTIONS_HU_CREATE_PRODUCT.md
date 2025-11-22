# 🧩 Instrucciones Técnicas para Implementar la HU: "Gestión de Productos: Crear Nuevo Producto"

**Objetivo**: Implementar la lógica backend para que un administrador pueda crear un nuevo producto en el sistema **Distribuidora Perros y Gatos**, cumpliendo con todos los criterios de aceptación definidos.

> 🔍 Este documento está escrito para ser **consumido y ejecutado por IA**. Cada paso debe interpretarse literalmente. No asumir comportamientos no especificados.

---

## ⚙️ Arquitectura Técnica

- **Producer (API)**: Python (FastAPI)  
- **Consumer (Worker)**: Node.js (Express/TypeScript)  
- **Broker**: RabbitMQ  
- **Infraestructura**: Docker & Docker Compose  
- **Base de datos**: SQL Server  




## 🧾 Datos del Producto (Estructura Obligatoria en BD)

Todo producto debe tener los siguientes campos **almacenados en la base de datos**:

| Campo        | Tipo             | Requerido | Validación |
|--------------|------------------|-----------|------------|
| `nombre`     | string           | ✅        | Único en el sistema. Mínimo 2 caracteres. |
| `descripcion`| string           | ✅        | Mínimo 10 caracteres. Texto libre. |
| `precio`     | number (float)   | ✅        | > 0. Solo valores numéricos positivos. |
| `peso`       | number (integer) | ✅        | > 0. Representa **gramos** (entero). Ej: 500 = 500g, 1000 = 1kg. |
| `categoria`  | string           | ✅        | Debe coincidir con una categoría existente (ej: "Perros", "Gatos"). |
| `subcategoria`| string          | ✅        | Debe coincidir con una subcategoría existente dentro de la categoría seleccionada. |
| `imagenUrl`  | string           | ✅        | URL de la imagen subida (almacenada en sistema de archivos o CDN). |

> ⚠️ **Nota**: El peso se almacena **siempre en gramos como entero**, sin importar si el usuario ingresa kg o g. La UI puede mostrar "1 kg", pero el valor guardado es `1000`.

---

## 🔗 Flujo Backend

1. **FastAPI (Producer)**  
   - Endpoint: `POST /api/admin/productos`  
   - Recibe payload con datos del producto.  
   - Valida campos obligatorios y formato de imagen.  
   - Publica mensaje en **RabbitMQ** con datos del producto.  

2. **RabbitMQ (Broker)**  
   - Cola: `productos.crear`  
   - Mensaje contiene JSON con todos los atributos del producto.  

3. **Node.js Worker (Consumer)**  
   - Escucha cola `productos.crear`.  
   - Procesa validaciones adicionales:  
     - Nombre único (case-insensitive).  
     - Categoría y subcategoría válidas.  
     - Conversión de peso a gramos si viene en kilogramos.  
   - Inserta registro en **SQL Server**.  
   - Devuelve confirmación al Producer.  

4. **Respuesta al Producer**  
   - Si éxito → JSON `{ "status": "success", "message": "Producto creado exitosamente" }`  
   - Si error → JSON `{ "status": "error", "message": "<detalle>" }`  

---

## ✅ Criterios de Aceptación – Implementación Detallada

### AC 1: Creación exitosa
- **Condiciones**:
  - Todos los campos requeridos están completos y válidos.
  - `nombre` no existe en la base de datos.
- **Acciones Backend**:
  - Guardar registro en SQL Server.  
  - Confirmar creación.  
- **Resultado esperado**: El producto aparece en el catálogo público.

---

### AC 2: Validación de campos obligatorios
- **Condiciones**: Al enviar payload, falta un campo obligatorio.  
- **Acciones Backend**:
  - Rechazar petición.  
  - Responder con error: `"Por favor, completa todos los campos obligatorios."`  
- **Restricción**: No usar `window.alert()`. Solo respuesta JSON para Toast en frontend.

---

### AC 3: Asociación a categorías y subcategorías
- **Condiciones**: Categoría y subcategoría deben coincidir con listas predefinidas.  
- **Acciones Backend**:
  - Validar contra tabla de categorías/subcategorías en SQL Server.  
  - Si no existen → error.  
- **Resultado esperado**: Producto visible bajo la categoría/subcategoría correcta.

---

### AC 4: Gestión de imagen y validación numérica

#### Validación de imagen:
- **Formatos permitidos**: `.jpg`, `.jpeg`, `.png`, `.svg`, `.webp`  
- **Tamaño máximo**: 10 MB  
- **Si no cumple** → error: `"Formato o tamaño de imagen no válido."`

#### Validación numérica:
- **Precio**: > 0, float.  
- **Peso**: Entero ≥ 1, siempre almacenado en gramos.  

#### Nombre duplicado:
- Si ya existe → error: `"Ya existe un producto con ese nombre."`

---

### AC 5: Prevención de duplicados en creación (Producer)
- **Condiciones**: Si ya existe un producto con el mismo `nombre` (comparación case-insensitive) y se intenta crear otro con el mismo nombre.
- **Acciones Backend (Producer)**:
  - El Producer (FastAPI) debe verificar en la base de datos si existe un producto con el mismo nombre (case-insensitive) antes de publicar el mensaje en RabbitMQ.
  - Si existe, el Producer debe responder con un error 400 y el mensaje: `"Ya existe un producto con ese nombre."` y **no** publicar nada en RabbitMQ.
- **Resultado esperado**: No se permite la creación duplicada; el sistema devuelve el error y no se genera ningún registro nuevo ni mensaje en la cola.

---

### AC 6: Listar productos creados

- **Endpoint**: `GET /api/admin/productos` (Producer / API)
- **Funcionalidad**:
  - Devuelve una lista de productos activos almacenados en el sistema.
  - Permite filtrar por `categoria_id` y/o `subcategoria_id`.
  - Soporta paginación con los parámetros `skip` (por defecto `0`) y `limit` (por defecto `20`, máximo `100`).
  - Cada elemento en la respuesta debe incluir: `id`, `nombre`, `descripcion`, `precio`, `peso` (en gramos, entero), `categoria` (id y nombre), `subcategoria` (id y nombre), `imagenes` (array de URLs/rutas), y `cantidad_disponible`.
  - Si no hay resultados, devolver `200` con un arreglo vacío `[]`.

- **Códigos de respuesta**:
  - `200 OK`: Lista de productos (posible arreglo vacío).
  - `400 Bad Request`: Parámetros inválidos (por ejemplo, `limit` fuera de rango) con mensaje JSON explicativo.

- **Restricciones y notas**:
  - Sólo deben incluirse productos activos (`activo = 1`).
  - La respuesta debe ser estable y paginable para consumo por la UI.
  - Este endpoint se usará por la interfaz de administración y también podrá adaptarse para vistas públicas si se requiere.


## 🔁 Flujo de Validación (Producer + Consumer)

---

### AC 7: Eliminar producto por id

- **Endpoint**: `DELETE /api/admin/productos/{producto_id}` (Producer / API)
- **Funcionalidad**:
  - Realiza un borrado lógico (soft-delete) marcando `activo = 0` para el producto con el `producto_id` proporcionado.
  - Publica un mensaje en la cola `productos.eliminar` con `{ "producto_id": <id> }` para que consumidores/servicios realicen acciones adicionales si es necesario (por ejemplo, auditoría, limpieza externa).

- **Validaciones**:
  - Si el `producto_id` no existe o ya está inactivo, devolver `404 Not Found` con mensaje JSON `{ "status": "error", "message": "Producto no encontrado." }`.
  - Si ocurre un error interno al actualizar la base de datos, devolver `500` con mensaje JSON explicativo.

- **Códigos de respuesta**:
  - `200 OK`: Eliminación lógica realizada correctamente — ejemplo de cuerpo: `{ "status": "success", "message": "Producto eliminado correctamente" }`.
  - `404 Not Found`: Producto no encontrado.
  - `500 Internal Server Error`: Error interno al procesar la eliminación.

- **Restricciones y notas**:
  - El borrado debe ser lógico (no borrar la fila físicamente) para permitir auditoría y recuperación.
  - No es obligatorio eliminar inmediatamente las imágenes del sistema de archivos; decidir política de retención separadamente (por ejemplo, limpieza programada por worker).
  - El Producer debe encargarse de la validación de existencia y de publicar el mensaje; la operación DB de marcar `activo = 0` puede ejecutarse directamente por el Producer o delegarse al Worker según diseño (preferible que el Producer haga la marca y publique la notificación).


1. **Producer (FastAPI)** valida:  
   - Campos vacíos.  
   - Formato de imagen.  
   - Valores numéricos > 0.  

2. **Consumer (Node.js Worker)** valida:  
   - Nombre único.  
   - Categoría/subcategoría válidas.  
   - Conversión de peso a gramos.  

3. **SQL Server** almacena registro si todo es válido.  

---

### AC 8: Actualizar producto por id

- **Endpoint**: `PUT /api/admin/productos/{producto_id}` (Producer / API)
- **Funcionalidad**:
  - Actualiza los campos del producto identificado por `producto_id` con los valores proporcionados en el cuerpo de la petición.
  - Campos actualizables: `nombre`, `descripcion`, `precio`, `peso_gramos` (o `peso`), `categoria_id`, `subcategoria_id`, `cantidad_disponible`, `activo`.
  - Soporta actualización parcial (el cliente puede enviar sólo los campos que desea modificar).
  - Mantener la validación de negocio: `precio > 0`, `peso_gramos` entero > 0, `nombre` mínimo 2 caracteres, `descripcion` mínimo 10 caracteres cuando se provea.

- **Validaciones adicionales**:
  - `nombre` debe ser único en el sistema (comparación case-insensitive) excepto respecto al propio producto que se está actualizando.
  - `categoria_id` y `subcategoria_id` deben existir y ser consistentes (la subcategoría debe pertenecer a la categoría indicada) si se proporcionan.
  - Si se envía `peso` en kg o en otro formato, documentar y convertir en el Producer/Worker a gramos; internamente se almacena en `peso_gramos` (entero).

- **Flujo esperado**:
  1. El Producer valida los datos proporcionados y la ausencia de duplicados de `nombre` (excluyendo el registro actual).
  2. Si todo es válido, actualiza la fila en la base de datos (`UPDATE ...`) y hace `commit`.
  3. Publica un mensaje en la cola `productos.actualizar` con el payload resultante (id + campos actualizados) para que otros sistemas se sincronicen.

- **Códigos de respuesta**:
  - `200 OK`: Actualización exitosa. Devuelve la representación actualizada del producto (modelo `ProductoResponse`).
  - `400 Bad Request`: Validación fallida (por ejemplo, `precio <= 0`, `nombre` demasiado corto, `nombre` duplicado). Responder con JSON explicativo.
  - `404 Not Found`: Producto no encontrado (id inválido o producto inactivo si la política lo requiere).
  - `500 Internal Server Error`: Error interno al procesar la actualización.

- **Notas y recomendaciones**:
  - El Producer debe ser responsable de las validaciones básicas y de evitar publicar mensajes inconsistentes en RabbitMQ.
  - Considerar aplicar una validación adicional en el Consumer/Worker antes de persistir cambios si la arquitectura requiere una segunda defensa (defense-in-depth).
  - Registrar en una tabla de auditoría (opcional) los cambios críticos como `nombre`, `precio` o `activo` para trazabilidad.


---

### AC 9: Obtener un producto por id

- **Endpoint**: `GET /api/admin/productos/{producto_id}` (Producer / API)
- **Funcionalidad**:
  - Devuelve la representación completa de un producto identificado por `producto_id` usando el modelo `ProductoResponse`.
  - Incluye: `id`, `nombre`, `descripcion`, `precio`, `peso_gramos` (entero), `cantidad_disponible`, `categoria` (id y nombre), `subcategoria` (id y nombre), `imagenes` (array de rutas/URLs), `activo`, `fecha_creacion` y `fecha_actualizacion`.
  - Por defecto sólo devuelve productos activos (`activo = 1`). Si se requiere incluir inactivos para tareas administrativas, añadir un query param `include_inactive=true` y documentarlo.

- **Validaciones**:
  - Si `producto_id` no existe o el producto está inactivo, devolver `404 Not Found` con cuerpo JSON: `{ "status": "error", "message": "Producto no encontrado." }`.
  - Si ocurre un error interno, devolver `500 Internal Server Error` con mensaje JSON explicativo.

- **Códigos de respuesta**:
  - `200 OK`: Devuelve el `ProductoResponse` completo.
  - `404 Not Found`: Producto no encontrado.
  - `500 Internal Server Error`: Error interno al procesar la petición.

- **Notas**:
  - Recomendada consulta eficiente que una `Productos`, `Categorias`, `Subcategorias` y `ProductoImagenes` (o el uso de la vista `vw_productos_detalle`) para construir la respuesta.
  - Si posteriormente se requieren metadatos de paginación o relaciones adicionales, documentar el cambio en este HU.
---

### AC 10: Obtener una imagen por id

- **Endpoint**: `GET /api/admin/productos/{producto_id}/images/{imagen_id}` (Producer / API)
- **Funcionalidad**:
  - Devuelve la información de una imagen asociada a un producto específico.
  - Campos devueltos: `id`, `producto_id`, `ruta_imagen`, `es_principal`, `orden`, `fecha_creacion` (modelo `ProductoImagenResponse`).
  - Requiere que el `producto_id` exista; por defecto el producto debe estar activo (`activo = 1`).

- **Validaciones**:
  - Si el `producto_id` no existe o está inactivo, devolver `404 Not Found` con cuerpo JSON: `{ "status": "error", "message": "Producto no encontrado." }`.
  - Si la `imagen_id` no existe o no pertenece al `producto_id` indicado, devolver `404 Not Found` con cuerpo JSON: `{ "status": "error", "message": "Imagen no encontrada." }`.
  - Si ocurre un error interno, devolver `500 Internal Server Error` con mensaje JSON explicativo.

- **Códigos de respuesta**:
  - `200 OK`: Devuelve el `ProductoImagenResponse` con los datos de la imagen.
  - `404 Not Found`: Producto o imagen no encontrados (incluye imagen no asociada al producto).
  - `500 Internal Server Error`: Error interno al procesar la petición.

- **Notas**:
  - La ruta `ruta_imagen` debe ser una URL o ruta relativa usable por la UI para mostrar la imagen (por ejemplo, prefijada con el path del servidor o el CDN si aplica).
  - Si se requiere borrar también el archivo físico en disco, implementar `DELETE /api/admin/productos/{producto_id}/images/{imagen_id}` (ya existe la operación DELETE pendiente) que realice eliminación física y lógica en la DB según política.

### AC 11: Actualizar una imagen por id

- **Endpoint**: `PUT /api/admin/productos/{producto_id}/images/{imagen_id}` (Producer / API)
- **Funcionalidad**:
  - Permite actualizar la imagen asociada a un producto: reemplazar el archivo de imagen y/o actualizar metadatos (`es_principal`, `orden`).
  - Si se reemplaza el archivo, el servidor deberá validar formato y tamaño, almacenar la nueva imagen (por ejemplo en `uploads/productos/{producto_id}/`) y actualizar la columna `ruta_imagen` en `ProductoImagenes`.
  - Recomendar eliminar el archivo físico anterior al confirmar la actualización para evitar archivos huérfanos.

- **Validaciones**:
  - El `producto_id` debe existir y estar activo (`activo = 1`). Si no, devolver `404` con `{ "status": "error", "message": "Producto no encontrado." }`.
  - La `imagen_id` debe existir y pertenecer al `producto_id` indicado. Si no, devolver `404` con `{ "status": "error", "message": "Imagen no encontrada." }`.
  - Si se envía un archivo, validar extensión entre `.jpg`, `.jpeg`, `.png`, `.svg`, `.webp` y tamaño <= 10 MB; si no cumple, devolver `400` con el mensaje exacto: `"Formato o tamaño de imagen no válido."`.
  - Validar que `orden` sea entero >= 0 y `es_principal` sea booleano si se proporcionan.

- **Flujo esperado**:
  1. El Producer valida existencia del producto y de la imagen (y parámetros básicos).
  2. Si se envía archivo nuevo: validar formato/size, guardar archivo en disco (naming seguro), actualizar `ruta_imagen` en la BD y eliminar el archivo antiguo.
  3. Actualizar campos `es_principal` y/o `orden` si fueron enviados.
  4. Hacer `commit` en la base de datos y devolver `200 OK` con el objeto `ProductoImagenResponse` actualizado.
  5. Publicar un mensaje en la cola `productos.imagen.actualizar` con `{ "producto_id": <id>, "imagen_id": <id>, "ruta_imagen": "...", "es_principal": ..., "orden": ... }`.

- **Códigos de respuesta**:
  - `200 OK`: Actualización exitosa. Devuelve el `ProductoImagenResponse` actualizado.
  - `400 Bad Request`: Validación fallida (por ejemplo, formato/size de imagen inválido) con JSON explicativo.
  - `404 Not Found`: Producto o imagen no encontrados.
  - `500 Internal Server Error`: Error interno al procesar la actualización.

- **Notas**:
  - La operación debe ser atómica: si la actualización de la BD falla después de guardar el nuevo archivo, el servidor debe eliminar el archivo nuevo y restaurar el estado anterior o devolver un error claro para evitar inconsistencias.
  - Si la política requiere, el Worker puede encargarse de la eliminación física en segundo plano (por ejemplo, publicar `productos.imagen.actualizar` y dejar que el worker haga housekeeping).




### AC 12: Eliminar una imagen por id

- **Endpoint**: `DELETE /api/admin/productos/{producto_id}/images/{imagen_id}` (Producer / API)
- **Funcionalidad**:
  - Elimina una imagen asociada a un producto específico, removiendo la fila en `ProductoImagenes` y eliminando el archivo físico localizado en `ruta_imagen` cuando aplique.
  - Publica un mensaje en la cola `productos.imagen.eliminar` con el payload `{ "producto_id": <id>, "imagen_id": <id>, "ruta_imagen": "<ruta_o_null>" }`.

- **Validaciones**:
  - El `producto_id` debe existir y estar activo (`activo = 1`). Si no, devolver `404 Not Found` con `{ "status": "error", "message": "Producto no encontrado." }`.
  - La `imagen_id` debe existir y pertenecer al `producto_id` indicado. Si no, devolver `404 Not Found` con `{ "status": "error", "message": "Imagen no encontrada." }`.

- **Flujo recomendado**:
  1. Verificar existencia del producto y de la imagen (y que la imagen pertenezca al producto indicado).
  2. Ejecutar la eliminación de la fila en la BD (`DELETE FROM ProductoImagenes WHERE id = :imagen_id AND producto_id = :producto_id`) dentro de una transacción.
  3. Si la eliminación en BD fue exitosa, intentar eliminar el archivo físico referenciado en `ruta_imagen` si existe. Si la eliminación del archivo falla, registrar el error y continuar (no debe dejar la BD inconsistente).
  4. Publicar el evento `productos.imagen.eliminar` con la información de la imagen eliminada.

- **Códigos de respuesta**:
  - `200 OK`: Eliminación exitosa. Ejemplo: `{ "status": "success", "message": "Imagen eliminada correctamente" }`.
  - `404 Not Found`: Producto o imagen no encontrados.
  - `500 Internal Server Error`: Error interno al procesar la eliminación.

- **Notas**:
  - Si el archivo físico no existe pero la fila en BD sí, eliminar igualmente la fila y devolver éxito; registrar el incidente para limpieza manual/automática.
  - Registrar un log/auditoría del evento de eliminación (usuario que solicita, timestamp) para trazabilidad.
  - En arquitecturas donde la eliminación física la realice el Worker, se puede optar por sólo publicar `productos.imagen.eliminar` y dejar que el Worker haga la eliminación física; documentar la opción escogida.

## 🧪 Ejemplo de Payload Válido

```json
{
  "nombre": "Croquetas Premium para Gatos",
  "descripcion": "Alimento balanceado con proteína de salmón, ideal para gatos adultos.",
  "precio": 2499,
  "peso": 1500,
  "categoria": "Gatos",
  "subcategoria": "Alimento",
  "imagenFile": "<binary>"
}
