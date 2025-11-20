
---

## 📄 2. `AI_WORKFLOW.md`

```markdown
# 🤖 AI_WORKFLOW.md

Documento vivo que define cómo el **Equipo 3 – Gatos y Perros** integra inteligencia artificial en su flujo de trabajo para el desarrollo del MVP de sistema de pedidos.

> **Propósito**: Usar IA como **asistente técnico**, no como reemplazo del pensamiento crítico del equipo.

---

## 🧩 Metodología

- Trabajamos con **Kanban** en GitHub Projects.
- Reuniones diarias a las 8:00 am l
- Tareas pequeñas (<1 día) para facilitar integración continua.
- Todo el código pasa por **pull request con al menos una revisión**.

---

## 💬 Interacciones clave

| Canal          | Uso |
|----------------|-----|
| **chat gogle**    | Comunicación diaria, resolución rápida de dudas |
| **GitHub**     | Discusión técnica, pull requests, issues |
| **Reuniones**  | Toma de decisiones arquitectónicas, priorización |

---

## 📚 Documentos clave

| Documento             | Propósito |
|-----------------------|---------|
| `README.md`           | Cómo levantar el sistema localmente |
| `ARCHITECTURE.md`     | Diagrama y explicación del sistema (API → RabbitMQ → Worker) |
| `AI_WORKFLOW.md`      | Este documento: normas para uso de IA |
| `docker-compose.yml`  | Infraestructura local del MVP |
| `/docs/prompts/`      | Archivos con prompts útiles y reutilizables |

---

## 🤖 Dinámicas de interacción con IA

### ✅ Uso permitido
- Generar **esqueletos de código**: componentes React, Dockerfiles, workers en Python.
- Explicar conceptos técnicos: patrón Saga, colas de mensajes, accesibilidad WCAG.
- Redactar o mejorar **documentación técnica** (README, guías).
- Simular conversaciones de equipo para alinear ideas.

### 🚫 Uso prohibido
- Entregar código generado 100% por IA sin comprensión del equipo.
- Usar IA para resolver exámenes, tareas individuales o entregas académicas sin autoría clara.

### 🔁 Validación obligatoria
1. Todo output de IA se **revisa en pareja** antes de commitear.
2. El código generado debe:
   - Pasar pruebas locales.
   - Seguir las convenciones del equipo.
   - Ser entendido por al menos dos miembros.
3. Si la IA sugiere una solución arquitectónica, se **discute en reunión** antes de implementar.

### 📁 Gestión de prompts
- Los prompts útiles se guardan en `/docs/prompts/` con nombre descriptivo:  
  - `explain_rabbitmq_flow.md`  
  - `react_product_card_accessible.md`  
  - `docker_compose_frontend_backend.md`

### 🌍 Ética y responsabilidad
- La IA es una **herramienta de productividad**, no un actor autónomo.
- El equipo asume **responsabilidad total** sobre el código y decisiones técnicas.
- Priorizamos **transparencia**: si algo se generó con IA, se menciona en el PR o commit (ej: `feat: card de producto (asistido por IA)`).

---

> 🐾 *"La IA no piensa, pero nos ayuda a pensar mejor."*  
> — Equipo 3, Gatos y Perros