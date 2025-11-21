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

---

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

## 🔁 Flujo de Validación (Producer + Consumer)

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
