import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import encuestaRoutes from "./routes/encuestaRoutes.js";
import { verificarConexion, verificarYCrearTablas } from "./db.js";
import { config } from "./config.js";

// Configurar __dirname en ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rutas de la API (deben ir antes de las rutas estáticas)
app.use("/api", encuestaRoutes);

// Servir archivos estáticos desde la carpeta "frontend"
app.use(express.static(path.join(__dirname, "../frontend")));

// Ruta para la página principal
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "../frontend/index.html"));
});

// Manejo de errores 404
app.use((req, res) => {
  // Si la ruta comienza con /api, devolver error 404 en formato JSON
  if (req.path.startsWith("/api")) {
    res.status(404).json({
      success: false,
      error: "Ruta no encontrada"
    });
  } else {
    // Para otras rutas, servir index.html
    res.sendFile(path.join(__dirname, "../frontend/index.html"));
  }
});

// Iniciar servidor
const PORT = config.port || 3000;

const iniciarServidor = async () => {
  try {
    // Verificar conexión a la base de datos
    const conexionExitosa = await verificarConexion();
    if (!conexionExitosa) {
      throw new Error("No se pudo establecer conexión con la base de datos");
    }

    // Verificar y crear tablas si es necesario
    await verificarYCrearTablas();

    app.listen(PORT, () => {
      console.log(`🚀 Servidor corriendo en http://localhost:${PORT}`);
      console.log(`📊 Endpoint de diagnóstico: http://localhost:${PORT}/api/diagnosticar-db`);
    });
  } catch (error) {
    console.error("❌ Error al iniciar el servidor:", error);
    process.exit(1);
  }
};

iniciarServidor();
