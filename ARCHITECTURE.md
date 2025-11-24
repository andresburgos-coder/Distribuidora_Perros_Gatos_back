# 🏗️ Arquitectura Backend - Distribuidora Perros y Gatos

## 📋 Contenido
1. [Visión General](#visión-general)
2. [Estructura de Carpetas](#estructura-de-carpetas)
3. [Componentes y Tecnologías](#componentes-y-tecnologías)
4. [Flujo de Datos](#flujo-de-datos)
5. [API Endpoints](#api-endpoints)
6. [Colas RabbitMQ](#colas-rabbitmq)
7. [Modelo de Datos SQL Server](#modelo-de-datos-sql-server)
8. [Historias de Usuario Implementadas](#historias-de-usuario-implementadas)

---

## 🎯 Visión General 

La arquitectura del backend de **Distribuidora Perros y Gatos** utiliza un modelo **producer-consumer** con procesamiento asincrónico mediante **RabbitMQ**. 

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (React/Vue)                      │
│                                                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
          ┌──────────────────────────────────┐
          │   FastAPI (Producer/API)        │
          │   Python - Puerto 8000           │
          │                                   │
          │  • Validaciones iniciales         │
          │  • Lógica de negocio            │
          │  • Consultas directas a BD      │
          │  • Publicación en RabbitMQ      │
          └──────────────────────────────────┘
                     │              │
        ┌────────────┼──────────────┴─────────────┐
        │            │                             │
        ▼            ▼                             ▼
   ┌─────────┐  ┌──────────────┐  ┌────────────────────────┐
   │SQL Server│  │  RabbitMQ    │  │ Sistema de Archivos    │
   │   (DB)  │  │  (Broker)    │  │ / CDN (Imágenes)       │
   └─────────┘  │              │  └────────────────────────┘
                │ • Colas      │
                │ • Mensajes   │
                └──────┬───────┘
                       │
                       ▼
          ┌──────────────────────────────────┐
          │  Node.js Worker (Consumer)      │
          │  Express/TypeScript - Puerto    │
          │                                   │
          │  • Procesamiento asincrónico     │
          │  • Envío de emails               │
          │  • Operaciones pesadas           │
          │  • Persistencia en BD            │
          └──────────────────────────────────┘
```

---


## 🛠️ Componentes y Tecnologías

### FastAPI (Producer/API)
- **Framework**: FastAPI (Python)
- **Puerto**: 8000
- **Responsabilidades**:
  - Exponer endpoints REST
  - Validación inicial de datos
  - Lógica sincrónica simple
  - Publicación de mensajes en RabbitMQ
  - Autenticación (JWT + cookies)
  - Consultas directas a SQL Server (lecturas)
- **Dependencias**:
  - `fastapi`, `uvicorn`
  - `sqlalchemy`, `pyodbc` (SQL Server)
  - `pydantic` (validación)
  - `pika` (RabbitMQ)
  - `python-jose`, `passlib`, `bcrypt` (seguridad)

### Node.js Worker (Consumer)
- **Framework**: Express.js + TypeScript
- **Puerto**: 3000 (interno, no expuesto)
- **Responsabilidades**:
  - Consumir mensajes de RabbitMQ
  - Procesamiento asincrónico y pesado
  - Envío de emails
  - Operaciones de larga duración
  - Persistencia en SQL Server
- **Dependencias**:
  - `express`, `typescript`
  - `mssql`, `tedious` (SQL Server)
  - `amqplib` (RabbitMQ)
  - `nodemailer` (envío de emails)

### RabbitMQ (Message Broker)
- **Puerto**: 5672 (AMQP), 15672 (Management)
- **Colas** (ver sección detallada)
- **Mensajes**: JSON con `requestId`, `action`, `payload`, `meta`

### SQL Server (Base de Datos)
- **Puerto**: 1433
- **Autenticación**: SQL Server Authentication
- **Tablas**: ~14+ tablas (ver sección detallada)

### Volumen Compartido (Uploads)
- Sistema de archivos para imágenes (productos, carrusel)
- Mapeado en `api` y `worker` para acceso compartido
- Alternativa: usar CDN (AWS S3, CloudFront, etc.)

---

## 📊 Flujo de Datos

### Ejemplo 1: Crear Producto (con RabbitMQ)
```
1. Cliente envía → POST /api/admin/productos
2. FastAPI valida y publica en cola `productos.crear`
3. Worker consume mensaje de `productos.crear`
4. Worker valida reglas de negocio adicionales
5. Worker inserta en BD (Productos, InventarioHistorial)
6. Worker retorna success → API responde al cliente
```

### Ejemplo 2: Listar Productos (lectura directa)
```
1. Cliente envía → GET /api/home/productos
2. FastAPI consulta BD directamente
3. FastAPI devuelve lista formateada al cliente
```

### Ejemplo 3: Iniciar Sesión (con fusión de carrito)
```
1. Cliente envía → POST /api/auth/login
2. FastAPI valida credenciales
3. FastAPI emite JWT + refresh token (cookies)
4. FastAPI fusiona carritos (anónimo + autenticado)
5. FastAPI devuelve acceso_token + estado de fusión
6. (Opcional) Publica en `auth.events` para auditoría
```

---

## 🌐 API Endpoints

### Autenticación (`/api/auth/*`)
```
POST   /api/auth/register              # Registro nuevo usuario
POST   /api/auth/verify-email          # Verificar código de email
POST   /api/auth/resend-code           # Reenviar código
POST   /api/auth/login                 # Iniciar sesión
POST   /api/auth/logout                # Cerrar sesión
POST   /api/auth/refresh               # Renovar token
```

### Administración - Categorías (`/api/admin/categorias/*`)
```
POST   /api/admin/categorias           # Crear categoría
PUT    /api/admin/categorias/{id}      # Actualizar nombre
DELETE /api/admin/categorias/{id}      # Eliminar (si no hay productos)
GET    /api/admin/categorias           # Listar todas
```

### Administración - Subcategorías (`/api/admin/categorias/{catId}/subcategorias/*`)
```
POST   /api/admin/categorias/{catId}/subcategorias     # Crear
PUT    /api/admin/subcategorias/{id}                   # Actualizar
DELETE /api/admin/subcategorias/{id}                   # Eliminar
GET    /api/admin/categorias/{catId}/subcategorias     # Listar
```

### Administración - Productos (`/api/admin/productos/*`)
```
POST   /api/admin/productos            # Crear producto
GET    /api/admin/productos            # Listar todos
GET    /api/admin/productos/{id}       # Detalle
PUT    /api/admin/productos/{id}       # Actualizar
DELETE /api/admin/productos/{id}       # Eliminar
```

### Administración - Inventario (`/api/admin/productos/*`)
```
GET    /api/admin/productos/search     # Buscar por nombre/ID
GET    /api/admin/productos/{id}/stock # Ver existencias
POST   /api/admin/productos/{id}/reabastecer  # Agregar stock
GET    /api/admin/productos/{id}/inventario/historial  # Historial
```

### Administración - Carrusel (`/api/admin/carrusel/*`)
```
GET    /api/carrusel                   # Listar público
POST   /api/admin/carrusel             # Subir imagen
DELETE /api/admin/carrusel/{id}        # Eliminar
PUT    /api/admin/carrusel/reordenar   # Reordenar
```

### Administración - Pedidos (`/api/admin/pedidos/*`)
```
GET    /api/admin/pedidos              # Listar con filtros
GET    /api/admin/pedidos/{id}         # Detalle
PUT    /api/admin/pedidos/{id}/estado  # Actualizar estado
```

### Administración - Usuarios (`/api/admin/usuarios/*`)
```
GET    /api/admin/usuarios             # Listar
GET    /api/admin/usuarios/{id}        # Perfil detallado
GET    /api/admin/usuarios/{id}/pedidos  # Pedidos del usuario
```

### Home/Cliente - Productos (`/api/home/*`, `/api/productos/*`)
```
GET    /api/home/productos             # Listar por categoría/subcategoría
GET    /api/productos/{id}             # Detalle de producto
POST   /api/cart/add                   # Agregar al carrito
GET    /api/cart                       # Ver carrito
POST   /api/checkout                   # Procesar compra
```

### Health
```
GET    /health                         # Estado del API
```

---

## 📬 Colas RabbitMQ

| Queue | Origen | Consumer | Propósito | Referencia HU |
|-------|--------|----------|-----------|----------------|
| `email.verification` | API | Worker | Envio de códigos de verificación | REGISTER_USER |
| `categorias.crear` | API | Worker | Crear categoría principal | MANAGE_CATEGORIES |
| `categorias.actualizar` | API | Worker | Actualizar categoría | MANAGE_CATEGORIES |
| `subcategorias.crear` | API | Worker | Crear subcategoría | MANAGE_CATEGORIES |
| `subcategorias.actualizar` | API | Worker | Actualizar subcategoría | MANAGE_CATEGORIES |
| `productos.crear` | API | Worker | Crear nuevo producto | CREATE_PRODUCT |
| `productos.actualizar` | API | Worker | Actualizar producto | (Future HU) |
| `inventario.reabastecer` | API | Worker | Reabastecer stock | MANAGE_INVENTORY |
| `carrusel.imagen.crear` | API | Worker | Subir imagen al carrusel | MANAGE_CAROUSEL |
| `carrusel.imagen.eliminar` | API | Worker | Eliminar imagen del carrusel | MANAGE_CAROUSEL |
| `carrusel.imagen.reordenar` | API | Worker | Reordenar imágenes | MANAGE_CAROUSEL |
| `pedidos.actualizar_estado` | API | Worker | Actualizar estado de pedido | MANAGE_ORDERS |
| `cart.events` | API | Worker (opt) | Analytics de carrito | HOME_PRODUCTS |
| `auth.events` | API | Worker (opt) | Auditoría de autenticación | LOGIN_USER |

**Estructura de Mensaje RabbitMQ**:
```json
{
  "requestId": "<uuid>",
  "action": "crear_categoria",
  "payload": { "nombre": "Aves", "userId": "admin-1" },
  "meta": { "timestamp": "2025-11-20T12:00:00Z", "retry": 0 }
}
```

---

## 🗄️ Modelo de Datos SQL Server

### Tablas Core

#### `Usuarios`
- `id` (PK)
- `email` (UNIQUE, case-insensitive)
- `password_hash` (bcrypt)
- `nombre`
- `cedula`
- `telefono`
- `direccion_envio`
- `preferencia_mascotas` (Perros/Gatos/Ambos/Ninguno)
- `is_active` (bool)
- `failed_login_attempts` (int, default 0)
- `locked_until` (nullable datetime)
- `created_at`, `updated_at`

#### `VerificationCodes`
- `id` (PK)
- `usuario_id` (FK → Usuarios)
- `code_hash` (HMAC SHA256)
- `expires_at` (datetime, +10 min)
- `attempts` (int)
- `sent_count` (int)
- `created_at`

#### `RefreshTokens`
- `id` (PK)
- `usuario_id` (FK → Usuarios)
- `token_hash` (JWT/opaque token hash)
- `expires_at` (datetime, ~7-30 days)
- `revoked` (bool, default false)
- `user_agent` (optional)
- `ip` (optional)
- `created_at`

#### `Categorias`
- `id` (PK)
- `nombre` (UNIQUE, case-insensitive)
- `created_at`, `updated_at`

#### `Subcategorias`
- `id` (PK)
- `categoria_id` (FK → Categorias)
- `nombre` (UNIQUE per categoria, case-insensitive)
- `created_at`, `updated_at`

#### `Productos`
- `id` (PK)
- `nombre` (UNIQUE, case-insensitive)
- `descripcion`
- `precio` (decimal)
- `peso` (int, gramos)
- `stock` (int)
- `categoria_id` (FK → Categorias)
- `subcategoria_id` (FK → Subcategorias)
- `imagenUrl`
- `created_at`, `updated_at`

#### `CarruselImagenes`
- `id` (PK)
- `imagenUrl`
- `thumbnailUrl` (optional)
- `orden` (int, 1-5)
- `linkUrl` (optional)
- `activo` (bool)
- `created_by` (string)
- `created_at`, `updated_at`

#### `Carts`
- `id` (PK)
- `usuario_id` (FK → Usuarios, nullable)
- `session_id` (string, nullable)
- `created_at`, `updated_at`

#### `CartItems`
- `id` (PK)
- `cart_id` (FK → Carts)
- `producto_id` (FK → Productos)
- `cantidad` (int)
- `created_at`

#### `Pedidos`
- `id` (PK)
- `usuario_id` (FK → Usuarios)
- `fecha_creacion` (datetime)
- `total` (decimal)
- `estado` (Pendiente de envío/Enviado/Entregado/Cancelado)
- `direccion_envio`
- `last_updated_by` (string)
- `last_updated_at` (datetime)
- `created_at`

#### `PedidoItems`
- `id` (PK)
- `pedido_id` (FK → Pedidos)
- `producto_id` (FK → Productos)
- `cantidad` (int)
- `precio_unitario` (decimal)
- `created_at`

#### `InventarioHistorial`
- `id` (PK)
- `producto_id` (FK → Productos)
- `cantidad_anterior` (int)
- `cantidad_cambiada` (int)
- `cantidad_nueva` (int)
- `userId` (string)
- `created_at`

#### `PedidosHistorialEstado`
- `id` (PK)
- `pedido_id` (FK → Pedidos)
- `estado_anterior` (string)
- `estado_nuevo` (string)
- `userId` (string)
- `comentario` (string, optional)
- `created_at`

#### `AuthEvents` (optional, auditoría)
- `id` (PK)
- `usuario_id` (FK → Usuarios, nullable)
- `event_type` (login_success/login_failed/logout)
- `ip` (string)
- `user_agent` (string)
- `created_at`

**Índices recomendados**:
- Usuarios: `email` (UNIQUE), `is_active`, `locked_until`
- Categorias/Subcategorias: `nombre` (UNIQUE, case-insensitive)
- Productos: `categoria_id`, `subcategoria_id`, `nombre`
- Pedidos: `usuario_id`, `estado`, `fecha_creacion`
- CartItems: `cart_id`, `producto_id`
- InventarioHistorial: `producto_id`, `created_at`

---

## 📖 Historias de Usuario Implementadas

| HU | Archivo | Descripción |
|----|---------|-------------|
| 1 | `INSTRUCTIONS_HU_CREATE_PRODUCT.md` | Crear nuevo producto (admin) |
| 2 | `INSTRUCTIONS_HU_MANAGE_CATEGORIES.md` | Crear/modificar categorías y subcategorías (admin) |
| 3 | `INSTRUCTIONS_HU_MANAGE_INVENTORY.md` | Reabastecer existencias (admin) |
| 4 | `INSTRUCTIONS_HU_MANAGE_CAROUSEL.md` | Gestionar carrusel (subir/eliminar/reordenar imágenes) |
| 5 | `INSTRUCTIONS_HU_MANAGE_ORDERS.md` | Visualizar y actualizar estado de pedidos (admin) |
| 6 | `INSTRUCTIONS_HU_MANAGE_USERS.md` | Visualizar detalles de clientes (admin) |
| 7 | `INSTRUCTIONS_HU_HOME_PRODUCTS.md` | Ver productos y agregar al carrito (cliente) |
| 8 | `INSTRUCTIONS_HU_REGISTER_USER.md` | Registro con verificación de email (cliente) |
| 9 | `INSTRUCTIONS_HU_LOGIN_USER.md` | Iniciar sesión con JWT + fusión de carrito (cliente) |

Cada HU contiene especificaciones detalladas de:
- Endpoints FastAPI
- Validaciones y reglas de negocio
- Colas RabbitMQ y estructura de mensajes
- Responsabilidades del Worker
- Mensajes exactos para UI (toasts)
- Modelos de datos requeridos

---

## 🚀 Deployment & Infrastructure

### Docker Services

```yaml
services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2019-latest
    ports:
      - "1433:1433"
    
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
  
  api:
    build: ./backend/api
    ports:
      - "8000:8000"
    depends_on:
      - sqlserver
      - rabbitmq
    volumes:
      - ./uploads:/app/uploads
  
  worker:
    build: ./backend/worker
    depends_on:
      - sqlserver
      - rabbitmq
    volumes:
      - ./uploads:/app/uploads
```

---

## 📝 Convenciones

- **Endpoints públicos (lectura)**: sin autenticación requerida, pero pueden ser restringidas por roles
- **Endpoints admin**: requieren autenticación + rol admin
- **Endpoints cliente**: requieren autenticación válida
- **Mensajes JSON**: siempre incluyen `status`, `message` y `data` (cuando aplique)
- **Códigos HTTP**: 200 (éxito), 400 (validación), 401 (auth), 403 (autorización), 404 (no encontrado), 409 (conflicto), 429 (rate limit), 500 (error servidor)
- **Timestamps**: ISO 8601 (UTC)
- **Paginación**: `page` y `pageSize` en query params

---

## 🔐 Seguridad

- **Contraseñas**: bcrypt/argon2 (nunca texto plano)
- **Tokens**: JWT con expiración + cookies HttpOnly para refresh
- **Rate limiting**: por IP y por usuario
- **SQL Injection**: prepared statements (SQLAlchemy + MSSQL driver)
- **CORS**: configurado para origen(es) permitido(s)
- **HTTPS**: requerido en producción
- **Logs**: nunca registrar passwords, tokens o datos sensibles en texto claro

---

## 📚 Referencias

- HU en `HU/` folder
- Scripts SQL en `sql/` folder
- FastAPI docs: `/docs` (Swagger UI)
- RabbitMQ Management: `http://localhost:15672` (guest/guest)

