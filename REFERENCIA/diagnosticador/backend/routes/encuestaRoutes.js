import express from 'express';
import { 
  procesarEncuesta, 
  obtenerHistorialEncuestas, 
  obtenerEncuestaPorId,
  testGuardadoDB,
  diagnosticarDB 
} from '../controllers/encuestaController.js';

const router = express.Router();

// Ruta para procesar una nueva encuesta
router.post('/encuesta', procesarEncuesta);

// Ruta para obtener el historial de encuestas
router.get('/encuestas', obtenerHistorialEncuestas);

// Ruta para obtener una encuesta específica por ID
router.get('/encuesta/:id', obtenerEncuestaPorId);

// Ruta de prueba para verificar el guardado en la base de datos
router.get('/test-db', testGuardadoDB);

// Ruta para diagnosticar la base de datos
router.get('/diagnosticar-db', diagnosticarDB);

export default router; 