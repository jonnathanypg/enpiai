import OpenAI from 'openai';
import { config } from '../backend/config.js';

console.log("🔑 Inicializando OpenAI API...");

// Verificar que la API key esté definida
if (!config.openai.apiKey) {
  console.error("❌ Error: API key de OpenAI no definida en la configuración");
  throw new Error("API key de OpenAI no definida");
}

const openai = new OpenAI({
  apiKey: config.openai.apiKey
});

const ASSISTANT_ID = config.openai.assistantId;

// Verificar que el ID del asistente esté definido
if (!ASSISTANT_ID) {
  console.warn("⚠️ Advertencia: ASSISTANT_ID no definido, se usará el modelo gpt-5-nano directamente");
}

// Función principal para obtener diagnóstico
export async function obtenerDiagnosticoOpenAI(sintomas, peso, estatura, presion, pulso, edad, nivel_energia = 5, observaciones = "") {
  console.log("🤖 Iniciando obtención de diagnóstico...");
  
  // Validar que los datos sean correctos antes de procesarlos
  console.log("📊 Validando datos recibidos:");
  console.log(`  → Edad: ${edad} (${typeof edad})`);
  console.log(`  → Pulso: ${pulso} (${typeof pulso})`);
  console.log(`  → Nivel de energía: ${nivel_energia} (${typeof nivel_energia})`);

  if (isNaN(edad) || edad < 0 || edad > 120) {
    throw new Error("Edad inválida");
  }
  if (isNaN(pulso) || pulso < 30 || pulso > 200) {
    throw new Error("Pulso inválido");
  }
  if (isNaN(nivel_energia) || nivel_energia < 1 || nivel_energia > 10) {
    console.error("❌ Nivel de energía inválido:", nivel_energia);
    throw new Error("Nivel de energía inválido. Debe estar entre 1 y 10");
  }

  console.log("✅ Validaciones pasadas correctamente");
  console.log("📊 Datos recibidos para diagnóstico:");
  console.log(`  → Edad: ${edad} años`);
  console.log(`  → Peso: ${peso} kg`);
  console.log(`  → Estatura: ${estatura} m`);
  console.log(`  → Presión: ${presion}`);
  console.log(`  → Pulso: ${pulso} lpm`);
  console.log(`  → Nivel de energía: ${nivel_energia}/10`);
  console.log(`  → Síntomas: ${sintomas.join(", ")}`);
  
  // Calcular IMC
  const imc = peso / (estatura * estatura);
  console.log(`  → IMC calculado: ${imc.toFixed(2)}`);

  const promptDiagnostico = `
  Como experto en bienestar y nutrición, analiza los siguientes datos del encuestado y proporciona un diagnóstico detallado en formato de párrafo continuo:

  **Datos del Encuestado:**
  - Edad: ${edad} años
  - Peso: ${peso} kg
  - Estatura: ${estatura} m
  - IMC: ${imc.toFixed(2)}
  - Presión arterial: ${presion}
  - Pulso: ${pulso} lpm
  - Nivel de energía: ${nivel_energia}/10
  
  **Síntomas Reportados:**
  ${sintomas.map(s => `- ${s}`).join('\n')}
  
  **Observaciones Adicionales:**
  ${observaciones || "Ninguna"}

  Por favor, proporciona un diagnóstico detallado en formato de párrafo continuo que incluya:
  1. Análisis de los síntomas reportados
  2. Posibles condiciones relacionadas
  3. Factores de riesgo identificados

  IMPORTANTE: 
  - Escribe todo en un solo párrafo continuo
  - No uses viñetas ni listas
  - No uses títulos ni subtítulos
  - Asegúrate de que el diagnóstico se complete completamente
  - Concluye con una recomendación clara sobre la necesidad de consultar con su coach de bienestar
  - Mantén un tono profesional pero accesible
  - No cortes el texto a mitad de una idea
  - Usa los datos exactos proporcionados, no inventes ni modifiques valores
  - Asegúrate de usar la edad correcta (${edad} años) y el pulso correcto (${pulso} lpm)
  - El nivel de energía es ${nivel_energia}/10, no lo confundas con la edad
  - No uses el valor de la edad como nivel de energía ni viceversa
  - Verifica que estés usando los valores correctos:
    * Edad: ${edad} años
    * Pulso: ${pulso} lpm
    * Nivel de energía: ${nivel_energia}/10
  `;

  try {
    console.log("📤 Enviando solicitud de diagnóstico a OpenAI...");
    const startTime = Date.now();
    
    const responseDiagnostico = await Promise.race([
      openai.chat.completions.create({
        model: "gpt-5-nano",
        messages: [
          { 
            role: "system", 
            content: "Eres un experto en bienestar y nutrición especializado en diagnósticos preliminares. Proporciona diagnósticos en formato de párrafo continuo, sin estructuras ni listas. Asegúrate de que cada diagnóstico se complete completamente y concluya con una recomendación clara sobre la necesidad de consultar con su coach de bienestar o distribuidor independiente de Herbalife. Usa los datos exactos proporcionados, no inventes ni modifiques valores." 
          },
          { 
            role: "user", 
            content: promptDiagnostico 
          }
        ],
        max_tokens: 50,
        temperature: 0.7
      }),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error("Timeout al obtener diagnóstico")), 30000)
      )
    ]);

    const diagnostico = responseDiagnostico.choices[0].message.content;
    console.log("✅ Respuesta recibida de OpenAI en", Date.now() - startTime, "ms");

    // Obtener recomendaciones
    const promptRecomendaciones = `
    Basado en el siguiente diagnóstico, proporciona recomendaciones específicas, personalizadas y accionables:

    Diagnóstico: ${diagnostico}

    Por favor, considera los siguientes puntos para proporcionar las recomendaciones:
    1. Debe estar basado estrictamente en el diagnóstico y la información proporcionada.
    2. Aborda la importancia de empezar cambios positivos desde el nivel de estilo de vida, nutrición y alimentación.
    3. Aborda los hábitos alimenticios recomendados, actividades físicas sugeridas y productos de Herbalife recomendados.
    4. No debes inventar nada, solo debes usar la información proporcionada, como un experto en nutrición y alimentación saludable.
    5. Debes recomendar productos Herbalife específicos para la necesidad del encuestado, solo los que tienes en los documentos adjuntos.
    6. La recomendación debe generar FOMO e incentivar la compra de productos Herbalife, no debes ser ambiguo, debes ser claro y directo.

    Presenta todo en un párrafo resumido, compacto, personalizado, claro y entendible.
    `;

    console.log("📤 Enviando solicitud de recomendaciones a OpenAI...");
    const responseRecomendaciones = await Promise.race([
      openai.chat.completions.create({
        model: "gpt-5-nano",
        messages: [
          { 
            role: "system", 
            content: "Eres un experto en bienestar y Herbalife. Proporciona recomendaciones en formato de párrafo continuo, sin estructuras ni listas. Asegúrate de que cada recomendación se complete completamente y concluya con una nota positiva y motivadora. Incluye recomendaciones específicas de productos Herbalife cuando sea relevante." 
          },
          { 
            role: "user", 
            content: promptRecomendaciones 
          }
        ],
        max_tokens: 50,
        temperature: 0.7
      }),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout en la llamada a OpenAI')), 30000)
      )
    ]);

    const responseTime = Date.now() - startTime;
    console.log(`✅ Respuestas recibidas de OpenAI en ${responseTime}ms`);

    return {
      diagnostico: diagnostico,
      recomendaciones: responseRecomendaciones.choices[0].message.content
    };

  } catch (error) {
    console.error("❌ Error al obtener diagnóstico de OpenAI:", error);
    if (error.message === 'Timeout en la llamada a OpenAI') {
      throw new Error("La solicitud a OpenAI tardó demasiado tiempo. Por favor, intente nuevamente.");
    }
    throw new Error("Error al obtener el diagnóstico. Por favor, intente nuevamente más tarde.");
  }
}
