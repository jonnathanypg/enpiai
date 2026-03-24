import { obtenerDiagnosticoOpenAI } from "../ai/openaiAPI.js";
import { pool, ejecutarConsulta } from "../backend/db.js";

export const submitSurvey = async (req, res) => {
  console.log("📝 Recibida nueva solicitud de encuesta");
  
  try {
    // Validar campos requeridos
    const camposRequeridos = [
      'nombre', 'apellido', 'telefono', 'correo',
      'edad', 'peso', 'estatura', 'presion_arterial', 'pulso', 'nivel_energia', 'sintomas'
    ];

    const camposFaltantes = camposRequeridos.filter(campo => !req.body[campo]);
    if (camposFaltantes.length > 0) {
      return res.status(400).json({
        success: false,
        error: 'Campos requeridos faltantes',
        campos: camposFaltantes
      });
    }

    console.log("🤖 Obteniendo diagnóstico con OpenAI...");
    
    // Procesar los datos antes de enviarlos
    const datosProcesados = {
      sintomas: req.body.sintomas,
      peso: parseFloat(req.body.peso),
      estatura: parseFloat(req.body.estatura),
      presion: req.body.presion_arterial,
      pulso: parseInt(req.body.pulso),
      edad: parseInt(req.body.edad),
      nivel_energia: parseInt(req.body.nivel_energia) || 5,
      observaciones: req.body.observaciones || ''
    };

    // Validar datos numéricos
    if (isNaN(datosProcesados.edad) || datosProcesados.edad < 0 || datosProcesados.edad > 120) {
      return res.status(400).json({
        success: false,
        error: 'Edad inválida'
      });
    }
    if (isNaN(datosProcesados.pulso) || datosProcesados.pulso < 30 || datosProcesados.pulso > 200) {
      return res.status(400).json({
        success: false,
        error: 'Pulso inválido'
      });
    }
    if (isNaN(datosProcesados.nivel_energia) || datosProcesados.nivel_energia < 1 || datosProcesados.nivel_energia > 10) {
      return res.status(400).json({
        success: false,
        error: 'Nivel de energía inválido. Debe estar entre 1 y 10'
      });
    }

    console.log("📊 Datos procesados para diagnóstico:", datosProcesados);

    // Obtener diagnóstico de OpenAI
    const diagnosticoResult = await obtenerDiagnosticoOpenAI(
      datosProcesados.sintomas,
      datosProcesados.peso,
      datosProcesados.estatura,
      datosProcesados.presion,
      datosProcesados.pulso,
      datosProcesados.edad,
      datosProcesados.nivel_energia,
      datosProcesados.observaciones
    );
    console.log("✅ Diagnóstico obtenido correctamente");

    // Crear nuevo usuario
    console.log("📝 Creando nuevo usuario...");
    const [usuarioResult] = await pool.query(
      `INSERT INTO usuarios (nombre, apellido, telefono, correo) 
       VALUES (?, ?, ?, ?)`,
      [req.body.nombre, req.body.apellido, req.body.telefono, req.body.correo]
    );
    const usuario_id = usuarioResult.insertId;
    console.log("✅ Nuevo usuario creado con ID:", usuario_id);

    // Insertar encuesta
    console.log("📝 Guardando encuesta...");
    const [encuestaResult] = await pool.query(
      `INSERT INTO encuestas (
        usuario_id, nombre_encuestado, telefono, correo, edad, peso, 
        estatura, presion_arterial, pulso, nivel_energia, sintomas, observaciones,
        nombre_encuestador, encuestador_id, fecha
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())`,
      [
        usuario_id,
        `${req.body.nombre} ${req.body.apellido}`,
        req.body.telefono,
        req.body.correo,
        datosProcesados.edad,
        datosProcesados.peso,
        datosProcesados.estatura,
        datosProcesados.presion,
        datosProcesados.pulso,
        datosProcesados.nivel_energia,
        JSON.stringify(datosProcesados.sintomas),
        datosProcesados.observaciones || null,
        req.body.nombre_encuestador || null,
        req.body.encuestador_id || null
      ]
    );
    const encuesta_id = encuestaResult.insertId;
    console.log("✅ Encuesta guardada con ID:", encuesta_id);

    // Guardar diagnóstico
    console.log("📝 Guardando diagnóstico...");
    await pool.query(
      `INSERT INTO diagnosticos (usuario_id, encuesta_id, diagnostico, recomendaciones) 
       VALUES (?, ?, ?, ?)`,
      [usuario_id, encuesta_id, diagnosticoResult.diagnostico, diagnosticoResult.recomendaciones]
    );
    console.log("✅ Diagnóstico guardado");

    // Preparar datos del paciente para la respuesta
    const datosPaciente = {
      nombre: req.body.nombre,
      apellido: req.body.apellido,
      telefono: req.body.telefono,
      correo: req.body.correo,
      edad: datosProcesados.edad,
      peso: datosProcesados.peso,
      estatura: datosProcesados.estatura,
      presion_arterial: datosProcesados.presion,
      pulso: datosProcesados.pulso,
      nivel_energia: datosProcesados.nivel_energia,
      sintomas: req.body.sintomas,
      observaciones: req.body.observaciones || null
    };

    // Generar un ID único para la sesión
    const sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);

    // Preparar respuesta
    const response = {
      success: true,
      message: 'Diagnóstico generado correctamente',
      sessionId: sessionId,
      datosPaciente: datosPaciente,
      diagnostico: diagnosticoResult.diagnostico,
      recomendaciones: diagnosticoResult.recomendaciones
    };

    console.log("📤 Enviando respuesta al cliente");
    res.json(response);

  } catch (error) {
    console.error('Error al procesar la encuesta:', error);
    res.status(500).json({
      success: false,
      error: 'Error al procesar la encuesta',
      details: error.message
    });
  }
};

export async function getDiagnostico(req, res) {
  try {
    const { id } = req.params;
    console.log('🔍 Obteniendo diagnóstico para sesión ID:', id);

    // En este caso, como no estamos usando la base de datos,
    // simplemente devolvemos un error 404
    return res.status(404).json({
      success: false,
      error: 'Diagnóstico no encontrado'
    });

  } catch (error) {
    console.error('❌ Error al obtener el diagnóstico:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener el diagnóstico'
    });
  }
}

export async function getEncuesta(req, res) {
  try {
    const { id } = req.params;
    console.log('🔍 Obteniendo datos de la sesión ID:', id);

    // En este caso, como no estamos usando la base de datos,
    // simplemente devolvemos un error 404
    return res.status(404).json({
      success: false,
      error: 'Datos no encontrados'
    });

  } catch (error) {
    console.error('❌ Error al obtener los datos:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener los datos'
    });
  }
}
