import express from 'express';
import { submitSurvey, getDiagnostico, getEncuesta } from '../controllers/encuestaController.js';

const router = express.Router();

// Ruta para enviar una nueva encuesta
router.post('/encuesta', submitSurvey);

// Ruta para obtener el diagnóstico de una encuesta
router.get('/diagnostico/:id', getDiagnostico);

// Ruta para obtener los datos de una encuesta
router.get('/encuesta/:id', getEncuesta);

export default router;
