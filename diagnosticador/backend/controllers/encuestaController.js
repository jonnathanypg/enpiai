import { obtenerDiagnosticoOpenAI } from '../../ai/openaiAPI.js';
import { pool, ejecutarConsulta } from '../db.js';

export const procesarEncuesta = async (req, res) => {
  try {
    console.log('📝 Iniciando procesamiento de encuesta...');
    const {
      nombre,
      apellido,
      telefono,
      correo,
      edad,
      peso,
      estatura,
      presion_arterial,
      pulso,
      nivel_energia,
      sintomas,
      observaciones,
      nombre_encuestador,
      encuestador_id
    } = req.body;

    // Obtener diagnóstico y recomendaciones
    console.log('🔄 Obteniendo diagnóstico de OpenAI...');
    const { diagnostico, recomendaciones } = await obtenerDiagnosticoOpenAI(
      sintomas,
      peso,
      estatura,
      presion_arterial,
      pulso,
      edad,
      nivel_energia,
      observaciones
    );
    console.log('✅ Diagnóstico obtenido');

    // Crear nuevo usuario sin verificaciones
    console.log('📝 Creando nuevo usuario...');
    let usuario_id;
    try {
      const usuarioResult = await ejecutarConsulta(
        `INSERT INTO usuarios (nombre, apellido, telefono, correo) 
         VALUES (?, ?, ?, ?)`,
        [nombre, apellido, telefono, correo]
      );
      usuario_id = usuarioResult.insertId;
      console.log('✅ Nuevo usuario creado con ID:', usuario_id);
    } catch (error) {
      console.error('❌ Error al crear usuario:', error);
      throw new Error(`Error al crear el usuario: ${error.message}`);
    }

    // Insertar datos en la tabla encuestas
    console.log('📝 Guardando encuesta...');
    const encuestaResult = await ejecutarConsulta(
      `INSERT INTO encuestas (
        usuario_id, nombre_encuestado, telefono, correo, edad, peso, 
        estatura, presion_arterial, pulso, nivel_energia, sintomas, observaciones,
        nombre_encuestador, encuestador_id, fecha
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())`,
      [
        usuario_id,
        `${nombre} ${apellido}`,
        telefono,
        correo,
        edad,
        peso,
        estatura,
        presion_arterial,
        pulso,
        nivel_energia,
        JSON.stringify(sintomas),
        observaciones,
        nombre_encuestador,
        encuestador_id
      ]
    );

    const encuesta_id = encuestaResult.insertId;
    console.log('✅ Encuesta guardada con ID:', encuesta_id);

    // Insertar diagnóstico y recomendaciones
    console.log('📝 Guardando diagnóstico y recomendaciones...');
    await ejecutarConsulta(
      `INSERT INTO diagnosticos (usuario_id, encuesta_id, diagnostico, recomendaciones) 
       VALUES (?, ?, ?, ?)`,
      [usuario_id, encuesta_id, diagnostico, recomendaciones]
    );
    console.log('✅ Diagnóstico y recomendaciones guardados');

    // Enviar respuesta exitosa
    res.json({
      success: true,
      datosPaciente: {
        nombre,
        apellido,
        telefono,
        correo,
        edad,
        peso,
        estatura,
        presion_arterial,
        pulso,
        nivel_energia,
        sintomas: JSON.stringify(sintomas),
        observaciones,
        nombre_encuestador,
        encuestador_id
      },
      diagnostico,
      recomendaciones,
      mensaje: 'Encuesta procesada y guardada exitosamente'
    });

  } catch (error) {
    console.error('❌ Error al procesar la encuesta:', error);
    console.error('Stack trace:', error.stack);
    
    // Determinar el tipo de error
    let statusCode = 500;
    let errorMessage = 'Error al procesar la encuesta';
    let errorDetails = error.message;

    if (error.code === 'ER_BAD_NULL_ERROR') {
      statusCode = 400;
      errorMessage = 'Datos incompletos';
      errorDetails = 'Faltan campos requeridos';
    }

    res.status(statusCode).json({
      success: false,
      error: errorMessage,
      details: errorDetails
    });
  }
};

// Función para obtener el historial de encuestas
export const obtenerHistorialEncuestas = async (req, res) => {
  try {
    const [encuestas] = await pool.query(`
      SELECT 
        e.*,
        u.nombre,
        u.apellido,
        d.diagnostico,
        d.recomendaciones
      FROM encuestas e
      JOIN usuarios u ON e.usuario_id = u.usuario_id
      JOIN diagnosticos d ON e.id = d.encuesta_id
      ORDER BY e.fecha DESC
    `);

    res.json({
      success: true,
      encuestas
    });
  } catch (error) {
    console.error('Error al obtener el historial:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener el historial de encuestas',
      details: error.message
    });
  }
};

// Función para obtener una encuesta específica por ID
export const obtenerEncuestaPorId = async (req, res) => {
  try {
    const [encuestas] = await pool.query(`
      SELECT 
        e.*,
        u.nombre,
        u.apellido,
        d.diagnostico,
        d.recomendaciones
      FROM encuestas e
      JOIN usuarios u ON e.usuario_id = u.usuario_id
      JOIN diagnosticos d ON e.id = d.encuesta_id
      WHERE e.id = ?
    `, [req.params.id]);

    if (encuestas.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'Encuesta no encontrada'
      });
    }

    res.json({
      success: true,
      encuesta: encuestas[0]
    });
  } catch (error) {
    console.error('Error al obtener la encuesta:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener la encuesta',
      details: error.message
    });
  }
};

// Función para probar la conexión y el guardado en la base de datos
export const testGuardadoDB = async (req, res) => {
  try {
    console.log('🔄 Iniciando prueba de guardado en la base de datos...');

    // Generar un timestamp para datos únicos
    const timestamp = Date.now();

    // Datos de prueba
    const datosPrueba = {
      nombre: 'Usuario',
      apellido: 'Prueba',
      telefono: `1234567890${timestamp}`,
      correo: `prueba${timestamp}@test.com`,
      edad: 30,
      peso: 70,
      estatura: 1.75,
      presion_arterial: '120/80',
      nivel_energia: 7,
      sintomas: ['Fatiga', 'Dolor de cabeza'],
      observaciones: 'Esta es una prueba',
      nombre_encuestador: 'Admin',
      encuestador_id: 'ADMIN001'
    };

    // Insertar en tabla usuarios
    console.log('📝 Insertando datos en tabla usuarios...');
    const [usuarioResult] = await pool.query(
      `INSERT INTO usuarios (nombre, apellido, telefono, correo) 
       VALUES (?, ?, ?, ?)`,
      [datosPrueba.nombre, datosPrueba.apellido, 
       datosPrueba.telefono, datosPrueba.correo]
    );

    const usuario_id = usuarioResult.insertId;
    console.log('✅ Usuario creado con ID:', usuario_id);

    // Insertar en tabla encuestas
    console.log('📝 Insertando datos en tabla encuestas...');
    const [encuestaResult] = await pool.query(
      `INSERT INTO encuestas (
        usuario_id, nombre_encuestado, telefono, correo, edad, peso, 
        estatura, presion_arterial, pulso, nivel_energia, sintomas, observaciones,
        nombre_encuestador, encuestador_id, fecha
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())`,
      [
        usuario_id,
        `${datosPrueba.nombre} ${datosPrueba.apellido}`,
        datosPrueba.telefono,
        datosPrueba.correo,
        datosPrueba.edad,
        datosPrueba.peso,
        datosPrueba.estatura,
        datosPrueba.presion_arterial,
        datosPrueba.pulso,
        datosPrueba.nivel_energia,
        JSON.stringify(datosPrueba.sintomas),
        datosPrueba.observaciones,
        datosPrueba.nombre_encuestador,
        datosPrueba.encuestador_id
      ]
    );

    const encuesta_id = encuestaResult.insertId;
    console.log('✅ Encuesta creada con ID:', encuesta_id);

    // Insertar en tabla diagnosticos
    console.log('📝 Insertando datos en tabla diagnosticos...');
    const diagnosticoPrueba = "Este es un diagnóstico de prueba";
    const recomendacionesPrueba = "Estas son recomendaciones de prueba";

    await pool.query(
      `INSERT INTO diagnosticos (usuario_id, encuesta_id, diagnostico, recomendaciones) 
       VALUES (?, ?, ?, ?)`,
      [usuario_id, encuesta_id, diagnosticoPrueba, recomendacionesPrueba]
    );
    console.log('✅ Diagnóstico creado');

    // Verificar que todo se guardó correctamente
    console.log('🔍 Verificando datos guardados...');
    const [resultados] = await pool.query(`
      SELECT 
        u.*,
        e.*,
        d.diagnostico,
        d.recomendaciones
      FROM usuarios u
      JOIN encuestas e ON u.usuario_id = e.usuario_id
      JOIN diagnosticos d ON e.id = d.encuesta_id
      WHERE u.usuario_id = ?
    `, [usuario_id]);

    console.log('✅ Prueba completada exitosamente');
    res.json({
      success: true,
      mensaje: 'Prueba de guardado completada exitosamente',
      datos: resultados[0]
    });

  } catch (error) {
    console.error('❌ Error en la prueba de guardado:', error);
    res.status(500).json({
      success: false,
      error: 'Error al realizar la prueba de guardado',
      details: error.message
    });
  }
};

// Función para diagnosticar la conexión y estructura de la base de datos
export const diagnosticarDB = async (req, res) => {
  try {
    console.log('🔍 Iniciando diagnóstico de la base de datos...');

    // 1. Verificar conexión
    console.log('1️⃣ Verificando conexión a la base de datos...');
    const [conexionResult] = await pool.query('SELECT 1');
    console.log('✅ Conexión exitosa');

    // 2. Verificar estructura de tablas
    console.log('2️⃣ Verificando estructura de tablas...');
    const [tablas] = await pool.query(`
      SELECT TABLE_NAME 
      FROM information_schema.TABLES 
      WHERE TABLE_SCHEMA = ?
    `, [process.env.DB_NAME]);

    console.log('Tablas encontradas:', tablas.map(t => t.TABLE_NAME));

    // 3. Verificar estructura de cada tabla
    const estructuraTablas = {};
    for (const tabla of tablas) {
      const [columnas] = await pool.query(`
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
      `, [process.env.DB_NAME, tabla.TABLE_NAME]);

      estructuraTablas[tabla.TABLE_NAME] = columnas;
    }

    // 4. Verificar registros existentes
    const registros = {};
    for (const tabla of tablas) {
      const [count] = await pool.query(`SELECT COUNT(*) as total FROM ${tabla.TABLE_NAME}`);
      registros[tabla.TABLE_NAME] = count[0].total;
      
      // Obtener los primeros 5 registros de cada tabla
      const [datos] = await pool.query(`SELECT * FROM ${tabla.TABLE_NAME} LIMIT 5`);
      registros[`${tabla.TABLE_NAME}_datos`] = datos;
    }

    // 5. Verificar permisos
    console.log('5️⃣ Verificando permisos...');
    const [permisos] = await pool.query(`
      SELECT GRANTEE, PRIVILEGE_TYPE
      FROM information_schema.USER_PRIVILEGES
      WHERE GRANTEE LIKE ?
    `, [`%${process.env.DB_USER}%`]);

    console.log('✅ Diagnóstico completado');

    res.json({
      success: true,
      diagnostico: {
        conexion: '✅ Conexión exitosa',
        tablas: {
          encontradas: tablas.map(t => t.TABLE_NAME),
          estructura: estructuraTablas,
          registros: registros
        },
        permisos: permisos,
        configuracion: {
          host: process.env.DB_HOST,
          database: process.env.DB_NAME,
          user: process.env.DB_USER
        }
      }
    });

  } catch (error) {
    console.error('❌ Error en el diagnóstico:', error);
    res.status(500).json({
      success: false,
      error: 'Error al realizar el diagnóstico',
      details: error.message,
      stack: error.stack
    });
  }
}; 