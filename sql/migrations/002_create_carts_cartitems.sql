-- Migration: create Carts and CartItems tables
-- Compatible with SQL Server

IF OBJECT_ID('dbo.CartItems', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CartItems (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        cart_id BIGINT NOT NULL,
        producto_id BIGINT NOT NULL,
        cantidad INT NOT NULL CHECK (cantidad > 0),
        fecha_creacion DATETIME2 DEFAULT SYSUTCDATETIME(),
        fecha_actualizacion DATETIME2 NULL
    );
END

IF OBJECT_ID('dbo.Carts', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Carts (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        usuario_id BIGINT NULL,
        session_id NVARCHAR(128) NULL,
        created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
    );
    CREATE INDEX IX_Carts_session_id ON dbo.Carts(session_id);
    CREATE INDEX IX_Carts_usuario_id ON dbo.Carts(usuario_id);
END

-- Add foreign key constraints if Productos table exists
IF OBJECT_ID('dbo.Productos', 'U') IS NOT NULL AND OBJECT_ID('dbo.Carts', 'U') IS NOT NULL
BEGIN
    ALTER TABLE dbo.CartItems
    ADD CONSTRAINT FK_CartItems_Productos FOREIGN KEY (producto_id) REFERENCES dbo.Productos(id) ON DELETE NO ACTION;
END

IF OBJECT_ID('dbo.CartItems', 'U') IS NOT NULL AND OBJECT_ID('dbo.Carts', 'U') IS NOT NULL
BEGIN
    ALTER TABLE dbo.CartItems
    ADD CONSTRAINT FK_CartItems_Carts FOREIGN KEY (cart_id) REFERENCES dbo.Carts(id) ON DELETE CASCADE;
END

-- Notes: run this script against the database using sqlcmd or SSMS
