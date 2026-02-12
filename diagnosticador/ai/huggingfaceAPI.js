// Si decides usar ESM, renombra el archivo a .mjs o configura "type": "module" en package.json
import { HfInference } from "@huggingface/inference";
import { huggingFaceApiKey } from "../backend/config.js";

const client = new HfInference(huggingFaceApiKey);

export const obtenerDiagnostico = async (sintomas, peso, estatura, presion_arterial, edad) => {
  try {
    const prompt = `Paciente de ${edad} años, con los siguientes síntomas: ${sintomas.join(", ")}.
Peso: ${peso} kg, Estatura: ${estatura} m, Presión arterial: ${presion_arterial}.
Basado en estos datos, realice un diagnóstico y recomendaciones.`;

    const chatCompletion = await client.chatCompletion({
      model: "deepseek-ai/DeepSeek-R1",
      messages: [
        {
          role: "user",
          content: prompt
        }
      ],
      provider: "together",
      max_tokens: 500
    });

    return chatCompletion.choices[0].message.content || "No se encontró diagnóstico.";
  } catch (error) {
    console.error("Error con Hugging Face:", error);
    return "Error al procesar el diagnóstico.";
  }
};
