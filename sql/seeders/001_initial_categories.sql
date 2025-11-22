-- Seeder: Initial Categories and Subcategories
-- Purpose: Populate the database with initial data for Perros and Gatos

USE distribuidora_db;
GO

BEGIN TRANSACTION;

-- Insert Categories
INSERT INTO Categorias (nombre, descripcion, activo)
VALUES 
    ('Perros', 'Productos para perros', 1),
    ('Gatos', 'Productos para gatos', 1);

-- Get the inserted category IDs
DECLARE @perros_id INT = (SELECT id FROM Categorias WHERE nombre = 'Perros');
DECLARE @gatos_id INT = (SELECT id FROM Categorias WHERE nombre = 'Gatos');

-- Insert Perros Subcategories
INSERT INTO Subcategorias (categoria_id, nombre, descripcion, activo)
VALUES 
    (@perros_id, 'Alimento', 'Alimentos y comidas para perros', 1),
    (@perros_id, 'Accesorios', 'Collares, correas, y otros accesorios', 1),
    (@perros_id, 'Productos de aseo', 'Champús, acondicionadores, y productos de higiene', 1);

-- Insert Gatos Subcategories
INSERT INTO Subcategorias (categoria_id, nombre, descripcion, activo)
VALUES 
    (@gatos_id, 'Alimento', 'Alimentos y comidas para gatos', 1),
    (@gatos_id, 'Accesorios', 'Juguetes, camas, y otros accesorios', 1),
    (@gatos_id, 'Productos de aseo', 'Champús, desodorantes, y productos de higiene', 1);

COMMIT TRANSACTION;

PRINT 'Initial categories and subcategories seeded successfully!';
