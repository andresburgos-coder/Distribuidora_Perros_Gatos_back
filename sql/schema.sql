-- SQL Server Database Schema for Distribuidora Perros y Gatos
-- Creates all tables and relationships

-- Create Database (if not exists)
USE master;
GO

IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'distribuidora_db')
BEGIN
    CREATE DATABASE distribuidora_db;
END
GO

USE distribuidora_db;
GO

-- ============================================================
-- 1. USUARIOS Table
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Usuarios')
BEGIN
    CREATE TABLE Usuarios (
        id INT PRIMARY KEY IDENTITY(1,1),
        nombre_completo NVARCHAR(100) NOT NULL,
        email NVARCHAR(100) NOT NULL UNIQUE,
        cedula NVARCHAR(20) NOT NULL UNIQUE,
        password_hash NVARCHAR(MAX) NOT NULL,
        es_admin BIT DEFAULT 0,
        is_active BIT DEFAULT 0,
        fecha_registro DATETIME DEFAULT GETUTCDATE(),
        ultimo_login DATETIME NULL,
        created_at DATETIME DEFAULT GETUTCDATE(),
        updated_at DATETIME DEFAULT GETUTCDATE()
    );
    
    CREATE INDEX idx_email ON Usuarios(email);
    CREATE INDEX idx_cedula ON Usuarios(cedula);
    CREATE INDEX idx_nombre ON Usuarios(nombre_completo);
END
GO

-- ============================================================
-- 2. CATEGORIAS Table
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Categorias')
BEGIN
    CREATE TABLE Categorias (
        id INT PRIMARY KEY IDENTITY(1,1),
        nombre NVARCHAR(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL UNIQUE,
        descripcion NVARCHAR(500) NULL,
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        fecha_actualizacion DATETIME DEFAULT GETUTCDATE()
    );
    
    CREATE INDEX idx_categoria_nombre ON Categorias(nombre);
END
GO

-- ============================================================
-- 3. SUBCATEGORIAS Table
-- ============================================================
    IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Subcategorias')
BEGIN
    CREATE TABLE Subcategorias (
        id INT PRIMARY KEY IDENTITY(1,1),
        categoria_id INT NOT NULL,
        nombre NVARCHAR(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
        descripcion NVARCHAR(500) NULL,
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_subcategoria_categoria FOREIGN KEY (categoria_id) 
            REFERENCES Categorias(id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_subcategoria_categoria ON Subcategorias(categoria_id);
    CREATE UNIQUE INDEX idx_subcategoria_nombre_categoria ON Subcategorias(categoria_id, nombre);
END
GO

-- ============================================================
-- 4. PRODUCTOS Table
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Productos')
BEGIN
    CREATE TABLE Productos (
        id INT PRIMARY KEY IDENTITY(1,1),
        nombre NVARCHAR(100) NOT NULL,
        descripcion NVARCHAR(500) NULL,
        precio DECIMAL(10, 2) NOT NULL CHECK (precio > 0),
        peso_gramos INT NOT NULL CHECK (peso_gramos > 0),
        cantidad_disponible INT DEFAULT 0 CHECK (cantidad_disponible >= 0),
        categoria_id INT NOT NULL,
        subcategoria_id INT NOT NULL,
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        fecha_actualizacion DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_producto_categoria FOREIGN KEY (categoria_id) 
            REFERENCES Categorias(id),
        -- Si la política de negocio lo permite, habilitar ON DELETE CASCADE para que
        -- al eliminar una subcategoría también se eliminen sus productos asociados.
        -- Esto evita violaciones de FK cuando la aplicación borra subcategorías.
        CONSTRAINT fk_producto_subcategoria FOREIGN KEY (subcategoria_id) 
            REFERENCES Subcategorias(id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_producto_categoria ON Productos(categoria_id);
    CREATE INDEX idx_producto_subcategoria ON Productos(subcategoria_id);
    CREATE INDEX idx_producto_nombre ON Productos(nombre);
END
GO

-- ============================================================
-- 5. PRODUCTO_IMAGENES Table
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'ProductoImagenes')
BEGIN
    CREATE TABLE ProductoImagenes (
        id INT PRIMARY KEY IDENTITY(1,1),
        producto_id INT NOT NULL,
        ruta_imagen NVARCHAR(MAX) NOT NULL,
        es_principal BIT DEFAULT 0,
        orden INT DEFAULT 0,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_imagen_producto FOREIGN KEY (producto_id) 
            REFERENCES Productos(id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_imagen_producto ON ProductoImagenes(producto_id);
END
GO

-- ============================================================
-- 6. CARRUSEL_IMAGENES Table
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CarruselImagenes')
BEGIN
    CREATE TABLE CarruselImagenes (
        id INT PRIMARY KEY IDENTITY(1,1),
        orden INT NOT NULL UNIQUE CHECK (orden >= 1 AND orden <= 5),
        ruta_imagen NVARCHAR(MAX) NOT NULL,
        link_url NVARCHAR(500) NULL,
        activo BIT DEFAULT 1,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        fecha_actualizacion DATETIME DEFAULT GETUTCDATE()
    );
    
    CREATE INDEX idx_carrusel_orden ON CarruselImagenes(orden);
END
GO

-- ============================================================
-- 7. CARTS Table (Shopping Carts)
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Carts')
BEGIN
    CREATE TABLE Carts (
        id INT PRIMARY KEY IDENTITY(1,1),
        usuario_id INT NULL,
        session_id NVARCHAR(100) NULL,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        fecha_actualizacion DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_cart_usuario FOREIGN KEY (usuario_id) 
            REFERENCES Usuarios(id) ON DELETE CASCADE,
        CONSTRAINT chk_cart_identificador CHECK (usuario_id IS NOT NULL OR session_id IS NOT NULL)
    );
    
    CREATE INDEX idx_cart_usuario ON Carts(usuario_id);
    CREATE INDEX idx_cart_session ON Carts(session_id);
END
GO

-- ============================================================
-- 8. CART_ITEMS Table
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'CartItems')
BEGIN
    CREATE TABLE CartItems (
        id INT PRIMARY KEY IDENTITY(1,1),
        cart_id INT NOT NULL,
        producto_id INT NOT NULL,
        cantidad INT NOT NULL CHECK (cantidad > 0),
        precio_unitario DECIMAL(10, 2) NOT NULL,
        fecha_agregado DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_cartitem_cart FOREIGN KEY (cart_id) 
            REFERENCES Carts(id) ON DELETE CASCADE,
        CONSTRAINT fk_cartitem_producto FOREIGN KEY (producto_id) 
            REFERENCES Productos(id)
    );
    
    CREATE INDEX idx_cartitem_cart ON CartItems(cart_id);
    CREATE INDEX idx_cartitem_producto ON CartItems(producto_id);
END
GO

-- ============================================================
-- 9. PEDIDOS Table (Orders)
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Pedidos')
BEGIN
    CREATE TABLE Pedidos (
        id INT PRIMARY KEY IDENTITY(1,1),
        usuario_id INT NOT NULL,
        estado NVARCHAR(50) DEFAULT 'Pendiente' CHECK (estado IN ('Pendiente', 'Enviado', 'Entregado', 'Cancelado')),
        total DECIMAL(10, 2) NOT NULL DEFAULT 0,
        direccion_entrega NVARCHAR(500) NOT NULL,
        telefono_contacto NVARCHAR(20) NOT NULL,
        nota_especial NVARCHAR(500) NULL,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        fecha_actualizacion DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_pedido_usuario FOREIGN KEY (usuario_id) 
            REFERENCES Usuarios(id)
    );
    
    CREATE INDEX idx_pedido_usuario ON Pedidos(usuario_id);
    CREATE INDEX idx_pedido_estado ON Pedidos(estado);
    CREATE INDEX idx_pedido_fecha ON Pedidos(fecha_creacion);
END
GO

-- ============================================================
-- 10. PEDIDO_ITEMS Table
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'PedidoItems')
BEGIN
    CREATE TABLE PedidoItems (
        id INT PRIMARY KEY IDENTITY(1,1),
        pedido_id INT NOT NULL,
        producto_id INT NOT NULL,
        cantidad INT NOT NULL CHECK (cantidad > 0),
        precio_unitario DECIMAL(10, 2) NOT NULL,
        CONSTRAINT fk_pedidoitem_pedido FOREIGN KEY (pedido_id) 
            REFERENCES Pedidos(id) ON DELETE CASCADE,
        CONSTRAINT fk_pedidoitem_producto FOREIGN KEY (producto_id) 
            REFERENCES Productos(id)
    );
    
    CREATE INDEX idx_pedidoitem_pedido ON PedidoItems(pedido_id);
END
GO

-- ============================================================
-- 11. PEDIDOS_HISTORIAL_ESTADO Table (Order Status History)
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'PedidosHistorialEstado')
BEGIN
    CREATE TABLE PedidosHistorialEstado (
        id INT PRIMARY KEY IDENTITY(1,1),
        pedido_id INT NOT NULL,
        estado_anterior NVARCHAR(50) NULL,
        estado_nuevo NVARCHAR(50) NOT NULL,
        usuario_id INT NULL,
        nota NVARCHAR(300) NULL,
        fecha DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_historial_pedido FOREIGN KEY (pedido_id) 
            REFERENCES Pedidos(id) ON DELETE CASCADE,
        CONSTRAINT fk_historial_usuario FOREIGN KEY (usuario_id) 
            REFERENCES Usuarios(id)
    );
    
    CREATE INDEX idx_historial_pedido ON PedidosHistorialEstado(pedido_id);
    CREATE INDEX idx_historial_fecha ON PedidosHistorialEstado(fecha);
END
GO

-- ============================================================
-- 12. INVENTARIO_HISTORIAL Table (Stock Change History)
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'InventarioHistorial')
BEGIN
    CREATE TABLE InventarioHistorial (
        id INT PRIMARY KEY IDENTITY(1,1),
        producto_id INT NOT NULL,
        cantidad_anterior INT NOT NULL,
        cantidad_nueva INT NOT NULL,
        tipo_movimiento NVARCHAR(50) NOT NULL CHECK (tipo_movimiento IN ('REABASTECIMIENTO', 'VENTA', 'AJUSTE', 'DEVOLUCION')),
        referencia NVARCHAR(200) NULL,
        usuario_id INT NULL,
        fecha DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_inventario_producto FOREIGN KEY (producto_id) 
            REFERENCES Productos(id),
        CONSTRAINT fk_inventario_usuario FOREIGN KEY (usuario_id) 
            REFERENCES Usuarios(id)
    );
    
    CREATE INDEX idx_inventario_producto ON InventarioHistorial(producto_id);
    CREATE INDEX idx_inventario_fecha ON InventarioHistorial(fecha);
END
GO

-- ============================================================
-- 13. VERIFICATION_CODES Table (Email Verification)
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'VerificationCodes')
BEGIN
    CREATE TABLE VerificationCodes (
        id INT PRIMARY KEY IDENTITY(1,1),
        usuario_id INT NOT NULL,
        code_hash NVARCHAR(MAX) NOT NULL,
        expira_en DATETIME NOT NULL,
        intentos_fallidos INT DEFAULT 0,
        usado BIT DEFAULT 0,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_verif_usuario FOREIGN KEY (usuario_id) 
            REFERENCES Usuarios(id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_verif_usuario ON VerificationCodes(usuario_id);
END
GO

-- ============================================================
-- 14. REFRESH_TOKENS Table
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'RefreshTokens')
BEGIN
    CREATE TABLE RefreshTokens (
        id INT PRIMARY KEY IDENTITY(1,1),
        usuario_id INT NOT NULL,
        token_hash NVARCHAR(MAX) NOT NULL,
        expira_en DATETIME NOT NULL,
        revocado BIT DEFAULT 0,
        fecha_creacion DATETIME DEFAULT GETUTCDATE(),
        CONSTRAINT fk_refresh_usuario FOREIGN KEY (usuario_id) 
            REFERENCES Usuarios(id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_refresh_usuario ON RefreshTokens(usuario_id);
    CREATE INDEX idx_refresh_expira ON RefreshTokens(expira_en);
END
GO

-- ============================================================
-- Create Views for Common Queries
-- ============================================================

-- View: Product with Category/Subcategory Details
IF OBJECT_ID('vw_productos_detalle', 'V') IS NOT NULL
    DROP VIEW vw_productos_detalle;
GO

CREATE VIEW vw_productos_detalle AS
SELECT 
    p.id,
    p.nombre,
    p.descripcion,
    p.precio,
    p.peso_gramos,
    p.cantidad_disponible,
    -- sku removed from product view
    c.nombre AS categoria_nombre,
    sc.nombre AS subcategoria_nombre,
    p.activo,
    p.fecha_creacion,
    p.fecha_actualizacion
FROM Productos p
INNER JOIN Categorias c ON p.categoria_id = c.id
INNER JOIN Subcategorias sc ON p.subcategoria_id = sc.id;
GO

-- View: Order Summary
IF OBJECT_ID('vw_pedidos_resumen', 'V') IS NOT NULL
    DROP VIEW vw_pedidos_resumen;
GO

CREATE VIEW vw_pedidos_resumen AS
SELECT 
    p.id,
    p.usuario_id,
    u.nombre_completo,
    u.email,
    p.estado,
    p.total,
    COUNT(pi.id) AS cantidad_items,
    p.fecha_creacion
FROM Pedidos p
INNER JOIN Usuarios u ON p.usuario_id = u.id
LEFT JOIN PedidoItems pi ON p.id = pi.pedido_id
GROUP BY p.id, p.usuario_id, u.nombre_completo, u.email, p.estado, p.total, p.fecha_creacion;
GO

PRINT 'Database schema created successfully!';
