# 🧾 Instrucciones Técnicas para Implementar la HU: "Gestión de Usuarios: Visualizar Detalles de Clientes"

**Objetivo**: Implementar la lógica backend para que un administrador pueda visualizar la lista de usuarios registrados, ver el perfil detallado de un cliente y consultar el historial de pedidos asociados. El documento está pensado para ser leído y ejecutado por una IA o por un desarrollador backend; cada paso debe interpretarse literalmente.

---

## ⚙️ Alcance (Backend únicamente)
- Producer (API): Python con FastAPI — expone endpoints REST para listar/filtrar usuarios y mostrar perfil y pedidos asociados. Estas operaciones son de lectura; la API accede a SQL Server directamente.
- Consumer (Worker): Node.js/TypeScript — no es necesario para las operaciones de solo lectura; documentar uso opcional si se requiere procesamiento asíncrono (ej. generación de reportes en batch).
- Broker: RabbitMQ — no obligatorio para esta HU (lecturas sincrónicas). Si se desea auditoría asíncrona o exportes, usar colas específicas (documentado abajo).
- Base de datos: SQL Server — tablas `Usuarios`, `UsuariosMascotas` (o campo preferencia), `Pedidos`, `PedidoItems`.
- Infraestructura: Docker & Docker Compose (servicios: `api`, `sqlserver`, `rabbitmq` opcional).

---

## 🧾 Modelo de Datos (mínimo requerido en BD)
- Tabla `Usuarios`:
  - `id` (GUID o bigint) — Identificador único.
  - `nombre` (string) — Nombre completo.
  - `cedula` (string) — Documento de identidad.
  - `email` (string) — Correo electrónico.
  - `telefono` (string) — Teléfono de contacto.
  - `direccion_envio` (string) — Dirección principal de envío.
  - `preferencia_mascotas` (string) — Valores permitidos: `Perros`, `Gatos`, `Ambos`, `Ninguno` (opcional alternativamente tabla `UsuariosMascotas`).
  - `created_at`, `updated_at` (datetime)

- (Opcional) Tabla `UsuariosMascotas` (si se requiere modelado relacional):
  - `id`, `usuario_id` (FK), `tipo` (`Perro`/`Gato`), `descripcion` (opcional)

- Tabla `Pedidos` (ya descrita en HU de pedidos):
  - `id`, `cliente_id` (FK -> Usuarios.id), `fecha_creacion`, `total`, `estado`, `direccion_envio`, etc.

- Tabla `PedidoItems`: items por pedido.

Notas:
- El administrador no puede actualizar datos de usuario en esta HU (solo lectura).
- Indexar `email`, `cedula`, y `nombre` para búsquedas rápidas.

---

## 🔗 Flujo Backend (alto nivel)
1. El administrador solicita la lista de usuarios o realiza una búsqueda a través de la API (FastAPI).
2. La API realiza consultas directamente a SQL Server (consultas optimizadas con índices) y devuelve resultados paginados.
3. Para ver el perfil detallado la API consulta `Usuarios` y `Pedidos` (y `PedidoItems`) y devuelve un objeto compuesto.
4. Si se desea operación asíncrona (exportar grandes volúmenes, generación de reportes), la API puede publicar un mensaje en RabbitMQ que un Worker procese.

---

## 🧩 Endpoints (Producer — FastAPI)
- **Listar usuarios (con filtros y paginación)**
  - Método: `GET`
  - Ruta: `/api/admin/usuarios`
  - Query params (opcionales):
    - `q` (string) — búsqueda por `id`, `nombre`, `cedula` o `email` parcial.
    - `page` (int), `pageSize` (int)
    - `sort` (string) — campo para ordenar, ej. `nombre` o `created_at`.
  - Respuesta (ejemplo):
    ```json
    {
      "status": "success",
      "data": [ { "id": "...", "nombre": "...", "cedula": "...", "email": "...", "direccion_envio": "..." }, ... ],
      "meta": { "page": 1, "pageSize": 20, "total": 123 }
    }
    ```
  - Si no hay resultados: `data: []`.

- **Buscar usuario por ID / parámetros**
  - Método: `GET`
  - Ruta: `/api/admin/usuarios/{id}`
  - Respuesta (perfil detallado): incluir campos `id`, `nombre`, `cedula`, `email`, `telefono`, `direccion_envio`, `preferencia_mascotas` y `pedidosResumen` (véase abajo).
  - Si no existe: HTTP 404 con body exacto para toast: `{ "status": "error", "message": "Usuario no encontrado." }`.

- **Pedidos asociados a un usuario (detalle)**
  - Método: `GET`
  - Ruta: `/api/admin/usuarios/{id}/pedidos`
  - Query params (opcionales): `page`, `pageSize`, `estado` para filtrar por estado del pedido.
  - Respuesta: lista de pedidos con `id`, `fecha_creacion`, `total`, `estado`. Además, un endpoint de detalle de pedido está disponible en `GET /api/admin/pedidos/{pedidoId}` (reusar HU de pedidos).

- **Nota**: no exponer endpoints de actualización de usuario en esta HU.

---

## 🔎 Contratos de respuesta / formatos exactos (para toasts y UI)
- Respuesta error usuario no encontrado: `{ "status": "error", "message": "Usuario no encontrado." }`.
- Error campo obligatorio faltante (si aplica en búsquedas con body): `{ "status": "error", "message": "Por favor, completa todos los campos obligatorios." }`.
- Respuesta éxito (lista/objeto): siempre `{ "status": "success", "data": ... }`.

---

## 🔁 Ejemplos de Requests y Respuestas
- Listar usuarios (GET): `/api/admin/usuarios?page=1&pageSize=20`
  - Respuesta ejemplo:
```json
{
  "status": "success",
  "data": [
    { "id": "user-1", "nombre": "Ana Perez", "cedula": "12345678", "email": "ana@example.com", "direccion_envio": "Calle Falsa 123" },
    { "id": "user-2", "nombre": "Juan Soto", "cedula": "87654321", "email": "juan@example.com", "direccion_envio": "Av. Siempre Viva 1" }
  ],
  "meta": { "page": 1, "pageSize": 20, "total": 2 }
}
```

- Perfil detallado (GET): `/api/admin/usuarios/user-1`
  - Respuesta ejemplo:
```json
{
  "status": "success",
  "data": {
    "id": "user-1",
    "nombre": "Ana Perez",
    "cedula": "12345678",
    "email": "ana@example.com",
    "telefono": "+57 300 000 0000",
    "direccion_envio": "Calle Falsa 123",
    "preferencia_mascotas": "Perros",
    "pedidosResumen": {
      "totalPedidos": 5,
      "ultimoPedido": { "id": "pedido-45", "fecha": "2025-11-10T10:00:00Z", "total": 4500, "estado": "Entregado" }
    }
  }
}
```

- Pedidos del usuario (GET): `/api/admin/usuarios/user-1/pedidos?page=1&pageSize=10`
  - Respuesta ejemplo:
```json
{
  "status": "success",
  "data": [
    { "id": "pedido-45", "fecha_creacion": "2025-11-10T10:00:00Z", "total": 4500, "estado": "Entregado" },
    { "id": "pedido-46", "fecha_creacion": "2025-11-15T15:30:00Z", "total": 1200, "estado": "Pendiente de envío" }
  ],
  "meta": { "page": 1, "pageSize": 10, "total": 2 }
}
```

---

## 🛠 Indexes y rendimiento
- Crear índices en SQL Server para: `Usuarios.email`, `Usuarios.cedula`, `Usuarios.nombre` (puede ser índice full-text o index sobre columnas utilizadas en búsquedas parciales).
- Indexar `Pedidos.cliente_id`, `Pedidos.fecha_creacion` y `Pedidos.estado` para consultas de historial por usuario y filtros por fecha/estado.
- Paginación obligatoria en endpoints que devuelvan listados.

---

## 🧩 Consideraciones de seguridad y privacidad
- Endpoints deben estar protegidos por autenticación y autorización: solo administradores pueden acceder.
- Asegurar que datos sensibles (p. ej. números de pago) no se expongan aquí.
- Restringir exportes masivos de datos a procesos auditados o asíncronos.

---

## 🔁 Integración con Worker / RabbitMQ (opcional)
- Para tareas pesadas (exportar CSV de todos los usuarios, generación de reportes, sincronización con CRM), la API puede publicar un mensaje en RabbitMQ (`usuarios.exportar`) que un Worker consuma.
- Mensajes deben incluir `requestId` y `userId` (quien solicitó la operación) para trazabilidad.

---

## ✅ Checklist técnico para entrega (para que la IA verifique antes de dar la HU como completa)
- [ ] Endpoint `GET /api/admin/usuarios` implementado con `q`, `page`, `pageSize` y ordenamiento.
- [ ] Endpoint `GET /api/admin/usuarios/{id}` implementado y retorna perfil detallado con `preferencia_mascotas` y `pedidosResumen`.
- [ ] Endpoint `GET /api/admin/usuarios/{id}/pedidos` implementado con paginación y filtros por `estado`.
- [ ] Índices creados para búsquedas por `email`, `cedula` y `nombre`.
- [ ] Mensajes de error y success devueltos exactamente como se especifica (para toasts frontend).
- [ ] Permisos y autenticación aplicados (solo admins).
- [ ] (Opcional) Cola `usuarios.exportar` documentada si se requiere export.

---

## 📌 Preguntas abiertas / puntos a clarificar
- ¿Desean modelar las preferencias de mascotas como una columna (`preferencia_mascotas`) o como una tabla relacional (`UsuariosMascotas`)? Recomendación: usar columna para simplicidad si solo se necesita saber `Perros`/`Gatos`/`Ambos`.
- ¿Se requiere exportar datos de usuarios (CSV/Excel) desde la UI? Si sí, documentar y habilitar `usuarios.exportar`.

---

## 📌 Notas finales
- Documento exclusivo para backend. Mantener mensajes exactos para toasts en frontend.
- Ubicación del archivo: `HU/INSTRUCTIONS_HU_MANAGE_USERS.md`.

---

Archivo: `HU/INSTRUCTIONS_HU_MANAGE_USERS.md`
