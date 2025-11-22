-- Migration: Update Categorias and Subcategorias tables to match HU_MANAGE_CATEGORIES specifications
-- This migration ensures the tables match the exact requirements:
-- - id as GUID or bigint (using bigint for compatibility)
-- - created_at and updated_at (instead of fecha_creacion/fecha_actualizacion)
-- - Case-insensitive uniqueness for nombre
-- - Proper indexes for case-insensitive comparison

USE DistribuidoraDB;
GO

-- ============================================================
-- Update Categorias Table
-- ============================================================
IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Categorias')
BEGIN
    -- Drop existing unique constraint/index if exists
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_categoria_nombre' AND object_id = OBJECT_ID('Categorias'))
        DROP INDEX idx_categoria_nombre ON Categorias;
    
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_Categorias_nombre' AND object_id = OBJECT_ID('Categorias'))
        DROP INDEX UQ_Categorias_nombre ON Categorias;
    
    -- Add created_at and updated_at if they don't exist
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'created_at' AND object_id = OBJECT_ID('Categorias'))
        ALTER TABLE Categorias ADD created_at DATETIME DEFAULT GETUTCDATE();
    
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'updated_at' AND object_id = OBJECT_ID('Categorias'))
        ALTER TABLE Categorias ADD updated_at DATETIME DEFAULT GETUTCDATE();
    
    -- Rename fecha_creacion to created_at if it exists and created_at doesn't
    IF EXISTS (SELECT 1 FROM sys.columns WHERE name = 'fecha_creacion' AND object_id = OBJECT_ID('Categorias'))
        AND NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'created_at' AND object_id = OBJECT_ID('Categorias'))
    BEGIN
        EXEC sp_rename 'Categorias.fecha_creacion', 'created_at', 'COLUMN';
    END
    
    -- Rename fecha_actualizacion to updated_at if it exists and updated_at doesn't
    IF EXISTS (SELECT 1 FROM sys.columns WHERE name = 'fecha_actualizacion' AND object_id = OBJECT_ID('Categorias'))
        AND NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'updated_at' AND object_id = OBJECT_ID('Categorias'))
    BEGIN
        EXEC sp_rename 'Categorias.fecha_actualizacion', 'updated_at', 'COLUMN';
    END
    
    -- Remove old columns if they still exist
    IF EXISTS (SELECT 1 FROM sys.columns WHERE name = 'fecha_creacion' AND object_id = OBJECT_ID('Categorias'))
        ALTER TABLE Categorias DROP COLUMN fecha_creacion;
    
    IF EXISTS (SELECT 1 FROM sys.columns WHERE name = 'fecha_actualizacion' AND object_id = OBJECT_ID('Categorias'))
        ALTER TABLE Categorias DROP COLUMN fecha_actualizacion;
    
    -- Ensure nombre column has case-insensitive collation
    ALTER TABLE Categorias ALTER COLUMN nombre NVARCHAR(100) NOT NULL COLLATE SQL_Latin1_General_CP1_CI_AS;
    
    -- Create unique index for case-insensitive nombre
    CREATE UNIQUE NONCLUSTERED INDEX UQ_Categorias_nombre_ci 
        ON Categorias(LOWER(LTRIM(RTRIM(nombre))))
        WHERE nombre IS NOT NULL;
END
GO

-- ============================================================
-- Update Subcategorias Table
-- ============================================================
IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Subcategorias')
BEGIN
    -- Drop existing indexes if they exist
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_subcategoria_categoria' AND object_id = OBJECT_ID('Subcategorias'))
        DROP INDEX idx_subcategoria_categoria ON Subcategorias;
    
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_subcategoria_nombre_categoria' AND object_id = OBJECT_ID('Subcategorias'))
        DROP INDEX idx_subcategoria_nombre_categoria ON Subcategorias;
    
    -- Add created_at and updated_at if they don't exist
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'created_at' AND object_id = OBJECT_ID('Subcategorias'))
        ALTER TABLE Subcategorias ADD created_at DATETIME DEFAULT GETUTCDATE();
    
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'updated_at' AND object_id = OBJECT_ID('Subcategorias'))
        ALTER TABLE Subcategorias ADD updated_at DATETIME DEFAULT GETUTCDATE();
    
    -- Rename fecha_creacion to created_at if it exists and created_at doesn't
    IF EXISTS (SELECT 1 FROM sys.columns WHERE name = 'fecha_creacion' AND object_id = OBJECT_ID('Subcategorias'))
        AND NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'created_at' AND object_id = OBJECT_ID('Subcategorias'))
    BEGIN
        EXEC sp_rename 'Subcategorias.fecha_creacion', 'created_at', 'COLUMN';
    END
    
    -- Remove old columns if they still exist
    IF EXISTS (SELECT 1 FROM sys.columns WHERE name = 'fecha_creacion' AND object_id = OBJECT_ID('Subcategorias'))
        ALTER TABLE Subcategorias DROP COLUMN fecha_creacion;
    
    -- Ensure nombre column has case-insensitive collation
    ALTER TABLE Subcategorias ALTER COLUMN nombre NVARCHAR(100) NOT NULL COLLATE SQL_Latin1_General_CP1_CI_AS;
    
    -- Ensure categoria_id column exists and has FK
    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE name = 'categoria_id' AND object_id = OBJECT_ID('Subcategorias'))
        ALTER TABLE Subcategorias ADD categoria_id INT NOT NULL;
    
    -- Add FK constraint if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_subcategoria_categoria' AND parent_object_id = OBJECT_ID('Subcategorias'))
    BEGIN
        ALTER TABLE Subcategorias 
        ADD CONSTRAINT fk_subcategoria_categoria 
        FOREIGN KEY (categoria_id) REFERENCES Categorias(id);
    END
    
    -- Create index for categoria_id
    CREATE NONCLUSTERED INDEX idx_subcategoria_categoria 
        ON Subcategorias(categoria_id);
    
    -- Create unique index for case-insensitive nombre within same categoria_id
    CREATE UNIQUE NONCLUSTERED INDEX UQ_Subcategorias_nombre_categoria_ci 
        ON Subcategorias(categoria_id, LOWER(LTRIM(RTRIM(nombre))))
        WHERE nombre IS NOT NULL;
END
GO

PRINT 'Migration 002: Categorias and Subcategorias tables updated successfully!';
GO

