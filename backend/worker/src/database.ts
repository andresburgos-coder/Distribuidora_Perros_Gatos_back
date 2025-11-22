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
};

const pool = new mssql.ConnectionPool(config);

pool.connect().then(() => {
  logger.info('Connected to MSSQL');
}).catch((err: any) => {
  logger.error('Database Connection Failed! Bad Config: ', err);
});

export default pool;
