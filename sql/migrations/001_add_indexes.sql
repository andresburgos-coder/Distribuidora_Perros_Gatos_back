-- Migration: Add Indexes for Performance
-- Purpose: Improve query performance on common filter operations

USE DistribuidoraDB;
GO

-- Usuarios table indexes
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_usuario_activo')
CREATE INDEX idx_usuario_activo ON Usuarios(is_active);
GO

-- Productos table indexes
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_producto_activo')
CREATE INDEX idx_producto_activo ON Productos(activo);
GO

-- Cart indexes for fast lookups
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cart_usuario_activo')
CREATE INDEX idx_cart_usuario_activo ON Carts(usuario_id) WHERE usuario_id IS NOT NULL;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_cart_session_activo')
CREATE INDEX idx_cart_session_activo ON Carts(session_id) WHERE session_id IS NOT NULL;
GO

-- Pedidos indexes for filtering
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_pedido_usuario_estado')
CREATE INDEX idx_pedido_usuario_estado ON Pedidos(usuario_id, estado);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_pedido_estado_fecha')
CREATE INDEX idx_pedido_estado_fecha ON Pedidos(estado, fecha_creacion DESC);
GO

-- CarruselImagenes indexes
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_carrusel_activo')
CREATE INDEX idx_carrusel_activo ON CarruselImagenes(activo);
GO

-- InventarioHistorial indexes for historical queries
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_inventario_producto_fecha')
CREATE INDEX idx_inventario_producto_fecha ON InventarioHistorial(producto_id, fecha DESC);
GO

PRINT 'Performance indexes added successfully!';
