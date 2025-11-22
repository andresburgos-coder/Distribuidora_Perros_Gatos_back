import mssql from 'mssql';
import logger from './utils/logger';

const config = {
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  server: process.env.DB_SERVER || 'localhost',
  database: process.env.DB_NAME,
  port: parseInt(process.env.DB_PORT || '1433', 10),
  options: {
    encrypt: process.env.DB_ENCRYPT === 'true',
    // In containerized local/dev environments using self-signed certs it's
    // common to trust the server certificate. Default to true unless
    // explicitly set to 'false'.
    trustServerCertificate: process.env.DB_TRUST_SERVER_CERTIFICATE === 'false' ? false : true,
  },
  pool: {
    max: 10,
    min: 0,
    idleTimeoutMillis: 30000
  }
};

const pool = new mssql.ConnectionPool(config);

// Ensure connection is established before exporting
let isConnected = false;

pool.connect()
  .then(() => {
    isConnected = true;
    logger.info(`✅ Connected to MSSQL: ${config.server}:${config.port}/${config.database}`);
    logger.info(`   User: ${config.user}`);
  })
  .catch((err: any) => {
    logger.error('❌ Database Connection Failed!', {
      error: err.message,
      errorCode: err.code,
      server: config.server,
      database: config.database,
      port: config.port,
      user: config.user,
      stack: err.stack
    });
    logger.error('   Please verify:');
    logger.error('   1. SQL Server is running');
    logger.error(`   2. Database "${config.database}" exists`);
    logger.error(`   3. User "${config.user}" has access`);
    logger.error(`   4. Connection string: ${config.server}:${config.port}`);
    // Don't exit - let it retry on first use
  });

// Helper function to ensure connection
export async function ensureConnection(): Promise<void> {
  if (!isConnected || !pool.connected) {
    try {
      logger.info(`Attempting to connect to database: ${config.server}:${config.port}/${config.database}`);
      await pool.connect();
      isConnected = true;
      logger.info(`✅ Database connection established: ${config.database}`);
    } catch (error: any) {
      logger.error('❌ Failed to establish database connection:', {
        error: error.message,
        errorCode: error.code,
        errorNumber: error.number,
        server: config.server,
        database: config.database,
        port: config.port,
        user: config.user
      });
      throw error;
    }
  } else {
    logger.debug(`Database connection already established: ${config.database}`);
  }
}

export default pool;
