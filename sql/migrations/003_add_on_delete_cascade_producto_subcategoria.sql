-- Migration: 003_add_on_delete_cascade_producto_subcategoria.sql
-- Agrega ON DELETE CASCADE a la FK entre Productos.subcategoria_id -> Subcategorias.id
-- Incluye sección de 'up' (aplicar) y 'down' (rollback)
-- USO: ejecutar el script en la base de datos 'DistribuidoraDB' con un usuario que tenga permisos ALTER TABLE.

/* ======================
   UP - Aplicar cambio
   ====================== */
PRINT '--- UP: Aplicando ON DELETE CASCADE en fk_producto_subcategoria';
BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @existingFkName sysname;

    -- Buscar nombre de FK que referencia Subcategorias desde Productos
    SELECT TOP 1 @existingFkName = fk.name
    FROM sys.foreign_keys fk
    JOIN sys.tables t ON fk.parent_object_id = t.object_id
    WHERE t.name = 'Productos' AND fk.referenced_object_id = OBJECT_ID('Subcategorias');

    IF @existingFkName IS NOT NULL
    BEGIN
        PRINT 'Found existing FK: ' + @existingFkName + ' - dropping it first';
        EXEC('ALTER TABLE Productos DROP CONSTRAINT [' + @existingFkName + ']');
    END
    ELSE
    BEGIN
        PRINT 'No existing FK found by lookup; proceeding to (re)create constraint with cascade as fk_producto_subcategoria';
    END

    -- Crear nueva FK con ON DELETE CASCADE
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_producto_subcategoria')
    BEGIN
        ALTER TABLE Productos
        ADD CONSTRAINT fk_producto_subcategoria
        FOREIGN KEY (subcategoria_id) REFERENCES Subcategorias(id) ON DELETE CASCADE;
        PRINT 'Constraint fk_producto_subcategoria created with ON DELETE CASCADE';
    END
    ELSE
    BEGIN
        -- Si existe con el mismo nombre, reemplazar
        EXEC('ALTER TABLE Productos DROP CONSTRAINT fk_producto_subcategoria');
        ALTER TABLE Productos
        ADD CONSTRAINT fk_producto_subcategoria
        FOREIGN KEY (subcategoria_id) REFERENCES Subcategorias(id) ON DELETE CASCADE;
        PRINT 'Constraint fk_producto_subcategoria replaced (ON DELETE CASCADE)';
    END

    COMMIT TRANSACTION;
    PRINT '--- UP: Commit OK';
END TRY
BEGIN CATCH
    PRINT '--- UP: Error encountered - rolling back';
    IF XACT_STATE() <> 0
    BEGIN
        ROLLBACK TRANSACTION;
    END
    DECLARE @errMsg nvarchar(4000) = ERROR_MESSAGE();
    DECLARE @errNo int = ERROR_NUMBER();
    PRINT 'Error number: ' + CAST(@errNo AS nvarchar(50));
    PRINT @errMsg;
    THROW;
END CATCH

/* ======================
   DOWN - Rollback cambio
   ====================== */
PRINT '--- DOWN: Rollback - Removiendo ON DELETE CASCADE de fk_producto_subcategoria (se recreará sin cascade)';
BEGIN TRY
    BEGIN TRANSACTION;

    -- Si la constraint con cascade existe, eliminarla
    IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_producto_subcategoria')
    BEGIN
        ALTER TABLE Productos DROP CONSTRAINT fk_producto_subcategoria;
        PRINT 'Dropped fk_producto_subcategoria (cascade)';
    END

    -- Re-crear la FK sin cascade (si no existe)
    IF NOT EXISTS (
        SELECT 1 FROM sys.foreign_keys fk
        JOIN sys.tables t ON fk.parent_object_id = t.object_id
        WHERE t.name = 'Productos' AND fk.referenced_object_id = OBJECT_ID('Subcategorias')
    )
    BEGIN
        ALTER TABLE Productos
        ADD CONSTRAINT fk_producto_subcategoria
        FOREIGN KEY (subcategoria_id) REFERENCES Subcategorias(id);
        PRINT 'Recreated fk_producto_subcategoria WITHOUT ON DELETE CASCADE';
    END
    ELSE
    BEGIN
        PRINT 'There is another FK referencing Subcategorias from Productos; please review manually.';
    END

    COMMIT TRANSACTION;
    PRINT '--- DOWN: Commit OK';
END TRY
BEGIN CATCH
    PRINT '--- DOWN: Error encountered - rolling back';
    IF XACT_STATE() <> 0
    BEGIN
        ROLLBACK TRANSACTION;
    END
    DECLARE @errMsg2 nvarchar(4000) = ERROR_MESSAGE();
    DECLARE @errNo2 int = ERROR_NUMBER();
    PRINT 'Error number: ' + CAST(@errNo2 AS nvarchar(50));
    PRINT @errMsg2;
    THROW;
END CATCH
