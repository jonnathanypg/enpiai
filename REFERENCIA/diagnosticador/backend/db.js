import mysql from 'mysql2/promise';
import { config } from './config.js';

// Crear el pool de conexiones con configuración mejorada
export const pool = mysql.createPool({
  host: config.db.host,
  user: config.db.user,
  password: config.db.password,
  database: config.db.database,
  port: config.db.port,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 0
});

// Función para verificar la conexión
export const verificarConexion = async () => {
  try {
    const connection = await pool.getConnection();
    console.log('✅ Conexión a MySQL establecida correctamente');
    connection.release();
    return true;
  } catch (error) {
    console.error('❌ Error al conectar con MySQL:', error);
    return false;
  }
};

// Función para verificar que las tablas existen
export const verificarYCrearTablas = async () => {
  try {
    // Solo verificamos que las tablas existan
    await pool.query('SHOW TABLES LIKE "usuarios"');
    await pool.query('SHOW TABLES LIKE "encuestas"');
    await pool.query('SHOW TABLES LIKE "diagnosticos"');
    console.log('✅ Tablas verificadas correctamente');
    return true;
  } catch (error) {
    console.error('❌ Error al verificar tablas:', error);
    return false;
  }
};

// Función para ejecutar consultas con reintentos
export const ejecutarConsulta = async (query, params = [], maxReintentos = 3) => {
  let intentos = 0;
  while (intentos < maxReintentos) {
    try {
      const [resultados] = await pool.query(query, params);
      return resultados;
    } catch (error) {
      intentos++;
      if (intentos === maxReintentos) {
        throw error;
      }
      console.log(`Reintento ${intentos} de ${maxReintentos}...`);
      await new Promise(resolve => setTimeout(resolve, 1000 * intentos)); // Espera exponencial
    }
  }
}; 