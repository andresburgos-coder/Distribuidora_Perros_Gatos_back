# Quick Start Guide

## 🚀 Fast Track to Running the Project

### Prerequisites
- Docker Desktop (recommended) or Python 3.11+ & Node.js 18+

## Option 1: Docker (5 minutes - Recommended)

```bash
# 1. Navigate to project directory
cd Distribuidora_Perros_Gatos_back

# 2. Build and start all services
docker-compose up -d

# 3. Check if services are running
docker-compose ps

# 4. Access the application
# API Documentation: http://localhost:8000/docs
# API Root: http://localhost:8000/
# RabbitMQ Admin: http://localhost:15672 (guest/guest)
```

### Verify Services Are Running
```bash
# Check FastAPI health
curl http://localhost:8000/health

# Check RabbitMQ status
docker logs distribuidora_rabbitmq | grep "Server startup"

# Check SQL Server status
docker logs distribuidora_sqlserver | grep "SQL Server is now ready"

# Check Worker status
docker logs distribuidora_worker | grep "Connected"
```

---

## Option 2: Local Development Setup

### Backend (FastAPI)

```bash
# 1. Navigate to backend/api
cd backend/api

# 2. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings (can use defaults for local dev)

# 5. Run the server
uvicorn main:app --reload --port 8000

# API will be available at http://localhost:8000/docs
```

### Worker (Node.js)

```bash
# In a new terminal, navigate to backend/worker
cd backend/worker

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Build TypeScript
npm run build

# 4. Start worker
npm start

# Or for development with auto-reload
npm run dev
```

### Database (SQL Server)

```bash
# Option A: Using Docker for just the database
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourPassword123!" \
  -p 1433:1433 \
  mcr.microsoft.com/mssql/server:2022-latest

# Option B: Using SQL Server directly installed on your machine
# Make sure the service is running and accessible at localhost:1433
```

### Message Broker (RabbitMQ)

```bash
# Option A: Using Docker
docker run -d \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3.12-management-alpine

# Option B: Using RabbitMQ directly installed
# Make sure the service is running at localhost:5672
```

---

## Testing the API

### Using Swagger UI (Recommended)
```
Open browser: http://localhost:8000/docs
```

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/

# List categories (requires authentication in production)
curl http://localhost:8000/api/admin/categorias
```

### Using Postman

1. Import OpenAPI schema from `http://localhost:8000/openapi.json`
2. Create environment variable `base_url = http://localhost:8000`
3. Test endpoints

---

## Common Tasks

### Initialize Database Schema

```bash
# Using Docker (if services are running)
docker exec distribuidora_sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P YourPassword123! \
  -i /sql/schema.sql

# Or manually in SSMS:
# 1. Connect to localhost:1433 with sa/YourPassword123!
# 2. Run sql/schema.sql
# 3. Run sql/migrations/001_add_indexes.sql
# 4. Run sql/seeders/001_initial_categories.sql
```

### Check Logs

```bash
# FastAPI logs
docker logs -f distribuidora_api

# Worker logs
docker logs -f distribuidora_worker

# RabbitMQ logs
docker logs -f distribuidora_rabbitmq

# SQL Server logs
docker logs -f distribuidora_sqlserver
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (careful - deletes database!)
docker-compose down -v
```

---

## Environment Variables

### Critical Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DB_SERVER` | localhost | SQL Server host |
| `DB_PORT` | 1433 | SQL Server port |
| `DB_USER` | sa | Database user |
| `DB_PASSWORD` | YourPassword123! | Database password |
| `RABBITMQ_HOST` | localhost | RabbitMQ host |
| `RABBITMQ_PORT` | 5672 | RabbitMQ port |
| `SECRET_KEY` | your-secret-key-change-in-production | JWT secret |

### For Production
- Change `SECRET_KEY` to a strong random value
- Set `DEBUG=False`
- Use managed services (Azure SQL, AWS RDS)
- Configure real SMTP credentials for email

---

## API Endpoints Reference

### Authentication
```
POST   /api/auth/register         - Register new user
POST   /api/auth/verify-email     - Verify email code
POST   /api/auth/login            - Login with credentials
POST   /api/auth/refresh          - Refresh access token
POST   /api/auth/logout           - Logout
```

### Categories
```
GET    /api/admin/categorias      - List all categories
POST   /api/admin/categorias      - Create category
GET    /api/admin/categorias/{id} - Get category
PUT    /api/admin/categorias/{id} - Update category
DELETE /api/admin/categorias/{id} - Delete category
```

### Products
```
GET    /api/admin/productos       - List products
POST   /api/admin/productos       - Create product
GET    /api/admin/productos/{id}  - Get product
PUT    /api/admin/productos/{id}  - Update product
DELETE /api/admin/productos/{id}  - Delete product
POST   /api/admin/productos/{id}/images - Upload image
```

### Orders
```
GET    /api/admin/pedidos         - List orders
GET    /api/admin/pedidos/{id}    - Get order
PUT    /api/admin/pedidos/{id}/estado - Update status
```

### Shopping
```
GET    /api/home/productos        - Browse products
GET    /api/cart                  - Get cart
POST   /api/cart/add              - Add to cart
PUT    /api/cart/items/{id}       - Update item
DELETE /api/cart/items/{id}       - Remove item
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Kill the process
# Windows: taskkill /PID <PID> /F
# Linux/Mac: kill -9 <PID>
```

### Database Connection Failed
```bash
# Check SQL Server is running
docker ps | grep sqlserver

# Check connection string in .env
# Default: Server=localhost,1433;Database=DistribuidoraDB;User Id=sa;Password=YourPassword123!;

# Test connection with SQL Server Management Studio (SSMS)
```

### RabbitMQ Connection Failed
```bash
# Check RabbitMQ is running
docker ps | grep rabbitmq

# Check credentials in .env
# Default user: guest / password: guest

# Access RabbitMQ Management UI: http://localhost:15672
```

### Module Not Found Errors
```bash
# Backend
pip install -r requirements.txt

# Worker
npm install
npm run build
```

---

## Next Steps After Setup

1. **Read the Documentation**
   - `README_BACKEND.md` - Full documentation
   - `HU/INSTRUCTIONS_HU_*.md` - Feature specifications

2. **Test the API**
   - Visit http://localhost:8000/docs
   - Try authentication endpoints first
   - Test category and product endpoints

3. **Implement Services**
   - Implement business logic in `backend/api/app/services/`
   - Implement consumer logic in `backend/worker/src/services/`

4. **Add Tests**
   - Unit tests in `backend/api/tests/`
   - Integration tests for endpoints

5. **Deploy**
   - Configure production `.env` values
   - Build Docker images
   - Deploy to cloud platform

---

## Support

For detailed information:
- **API Docs**: http://localhost:8000/docs
- **Project Structure**: See `README_BACKEND.md`
- **Feature Details**: See `HU/` directory
- **Architecture**: See `ARCHITECTURE.md`

---

**Happy Coding! 🎉**
