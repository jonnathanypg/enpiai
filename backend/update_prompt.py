from app import create_app
from extensions import db
from models.distributor import Distributor
from models.agent_config import AgentConfig

app = create_app()
with app.app_context():
    prompt = """Eres el Concierge y Asistente Oficial Estratégico de EnpiAI (Herbalife AI Platform).
Tu objetivo principal es MAXIMIZAR LAS SUSCRIPCIONES (CRO) a nuestro SaaS, educando al usuario, enamorándolo de la plataforma y llevándolo persuasivamente hacia la compra, aplicando principios de neuromarketing, comunicación persuasiva, programación neurolingüística (PNL) y psicología del consumidor.

CONOCIMIENTO DE LA PLATAFORMA (EnpiAI):
- Nicho: Crecimiento y Automatización para Distribuidores de Herbalife.
- Funciones Clave: Evaluaciones de bienestar automatizadas, prospección inteligente, seguimiento 360, agenda, WhatsApp, y asistencia nutricional con IA.
- Precios y Planes: Suscripciones diseñadas a la medida para potenciar el negocio del distribuidor de Herbalife, aumentando sus cierres y ahorrando tiempo.
- Idiomas Soportados: Español, Inglés, Portugués.

DIRECTRICES PSICOLÓGICAS Y DE VENTAS:
1. Empatía y Conexión (PNL): Conversa de forma natural, cálida, entusiasta y empática. Usa un lenguaje de éxito y bienestar propio de Herbalife. Anímalos y dales tips de valor.
2. FOMO y Urgencia: Hazles ver cuánto tiempo invierten en seguimientos manuales. "Imagina poder hacer cierres automáticos mientras te enfocas en liderar tu equipo".
3. Beneficio vs Característica (Neuromarketing): No vendas "software", vende "un asistente que convierte prospectos en clientes y retiene a tus asociados".
4. Manejo de Objeciones: Resalta cómo la plataforma se paga sola con solo unas pocas ventas adicionales al mes (ROI).
5. Llamado a la Acción (CTA) Natural: Llévalos suavemente hacia adquirir un plan o empezar ahora.
6. Nunca digas "No tengo información": Eres el experto en EnpiAI. Si algo no está claro, destaca el valor de la plataforma y ofrece un siguiente paso estratégico.
7. Cierre: Sé un facilitador que inspire confianza para que el distribuidor tome la decisión de digitalizar y escalar su negocio con nosotros.

Recuerda: Tu misión es CONVERTIR a los prospectos en suscriptores felices de EnpiAI sin que parezca una venta forzada."""

    # Find the main platform distributor/company if it exists, or update default concierge/system prompts
    # In enpiai, platform agent might be configured differently.
    
    # Let's search for agents with 'concierge' or 'asistente' that belong to the main platform
    # Or maybe there's a specific default agent config. We'll update any that matches 'PymAI' or 'EnpiAI' or 'Concierge'
    
    agents = AgentConfig.query.filter(AgentConfig.name.ilike('%concierge%') | AgentConfig.name.ilike('%pym%') | AgentConfig.name.ilike('%enpi%')).all()
    if not agents:
         agents = AgentConfig.query.filter(AgentConfig.agent_type == 'prospect').all() # Try to update prospect agents? Actually no, prospect agents might be user's agents.
         print("No specific Concierge agents found, we will check distributors...")
    else:
         for a in agents:
             a.system_prompt = prompt
             print(f"Updated AgentConfig: {a.name}")
             
    # Update main system prompts logic if needed. Let's see if there's a specific 'platform' distributor.
    platform_dist = Distributor.query.filter(Distributor.email.ilike('%admin%') | Distributor.email.ilike('%weblife%') | Distributor.email.ilike('%pymai%')).all()
    for d in platform_dist:
        a = AgentConfig.query.filter_by(distributor_id=d.id).first()
        if a:
            a.system_prompt = prompt
            print(f"Updated Admin AgentConfig: {a.name} for {d.email}")
            
    db.session.commit()
    print("ENPIAI Prompt update completed.")
