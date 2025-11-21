# Distribuidora Perros y Gatos - Worker

This is the message consumer worker for the Distribuidora Perros y Gatos e-commerce application. It consumes messages from a RabbitMQ queue and performs asynchronous tasks, such as sending emails.

## Prerequisites

- Node.js (v16 or higher)
- npm
- RabbitMQ server

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/distribuidora-perros-gatos.git
   ```
2. Navigate to the worker directory:
   ```bash
   cd distribuidora-perros-gatos/backend/worker
   ```
3. Install the dependencies:
   ```bash
   npm install
   ```

## Configuration

1. Create a `.env` file in the `backend/worker` directory by copying the `.env.example` file:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file and update the following variables:
   - `RABBITMQ_URL`: The URL of your RabbitMQ server.
   - `SMTP_HOST`: The host of your SMTP server.
   - `SMTP_PORT`: The port of your SMTP server.
   - `SMTP_USER`: The username for your SMTP server.
   - `SMTP_PASS`: The password for your SMTP server.

## Running the worker

To start the worker, run the following command:

```bash
npm run dev
```

This will start the worker in development mode using `ts-node`.

To build the worker for production, run the following command:

```bash
npm run build
```

To start the worker in production mode, run the following command:

```bash
npm run start
```

## Testing

To run the tests, run the following command:

```bash
npm test
```
