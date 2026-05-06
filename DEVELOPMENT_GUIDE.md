
# Manual de Desarrollo: Plataforma SaaS para Distribuidores de Herbalife

**Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.**

## 1. Introducción

### 1.1. Visión del Proyecto

La plataforma SaaS para distribuidores de Herbalife es un ecosistema de herramientas de software diseñado para potenciar el negocio de los distribuidores independientes. El objetivo es proporcionar una solución integral "todo en uno" que automatice y simplifique las tareas clave de la gestión de un negocio de Herbalife, permitiendo a los distribuidores centrarse en lo que mejor saben hacer: vender productos y reclutar nuevos miembros para su equipo.

La plataforma se basa en una filosofía de "cero fricción", ofreciendo una experiencia de usuario intuitiva, rápida y agradable tanto para los distribuidores como para sus clientes y prospectos.

### 1.2. Alcance del Documento

Este documento sirve como manual técnico y guía de desarrollo para el proyecto. Define la arquitectura, las tecnologías, las convenciones de codificación, los flujos de trabajo y las mejores prácticas que deben seguir todos los desarrolladores que trabajen en el proyecto.

## 2. Arquitectura del Sistema

La plataforma se construye sobre una arquitectura de microservicios, con un backend principal en Python (Flask) y un servicio dedicado en Node.js para la integración con WhatsApp. Esta separación permite un desarrollo y escalado más flexible y robusto.

### 2.1. Diagrama de Arquitectura de Alto Nivel

```
+---------------------+      +---------------------+      +---------------------+
|      Frontend       |----->|       Backend       |<---->|     Base de Datos     |
| (React/Vue/Angular) |      |    (Python/Flask)   |      |       (MySQL)       |
+---------------------+      +---------------------+      +---------------------+
                                     ^
                                     |
                                     v
+---------------------+      +---------------------+      +---------------------+
|     Integraciones   |----->|   Agentes de IA     |<---->|    Vector DB        |
| (Google, Mail, etc) |      | (Orquestador/RAG)   |      |      (Pinecone)     |
+---------------------+      +---------------------+      +---------------------+
                                     ^
                                     |
                                     v
+---------------------+
|      API WhatsApp   |
|     (Node.js)       |
+---------------------+
```

### 2.2. Componentes Principales

*   **Frontend:** Una aplicación de una sola página (SPA) construida con un framework moderno como React, Vue o Angular, que se comunica con el backend a través de una API REST.
*   **Backend (Python/Flask):** El núcleo de la aplicación. Gestiona la lógica de negocio, la autenticación, el acceso a la base de datos y la orquestación de los agentes de IA.
*   **API WhatsApp (Node.js):** Un servicio independiente que gestiona la conexión con la API de WhatsApp, permitiendo un sistema multi-tenant para que cada distribuidor pueda conectar su propio número.
*   **Base de Datos Relacional (MySQL):** Almacena todos los datos de la aplicación, incluyendo usuarios, clientes, prospectos, configuraciones, etc.
*   **Base de Datos Vectorial (Pinecone):** Se utiliza para la memoria a largo plazo de los agentes de IA (RAG), almacenando documentos, conversaciones y otra información relevante.
*   **Agentes de IA:** Un sistema multi-agente que gestiona las interacciones con clientes y distribuidores, utilizando un orquestador para gestionar el estado y las habilidades de cada agente.

## 3. Pila Tecnológica (Tech Stack)

*   **Backend:** Python 3.10+, Flask 3.0
*   **Frontend:** A definir (React, Angular o Vue.js)
*   **Base de Datos:** MySQL
*   **ORM:** SQLAlchemy
*   **Base de Datos Vectorial:** Pinecone
*   **Servicio de WhatsApp:** Node.js 18+
*   **Autenticación:** JWT (JSON Web Tokens) y Google OAuth
*   **Integraciones:**
    *   Google Calendar API
    *   Google Gmail API (o SMTP genérico)
    *   Python Telegram Bot
*   **Despliegue:** Docker, Gunicorn, Nginx

## 4. Estructura del Proyecto

La estructura del proyecto seguirá las convenciones estándar de las aplicaciones Flask, utilizando "Blueprints" para modularizar la aplicación.

```
/
├── api-whatsapp/          # Servicio de WhatsApp (Node.js)
├── backend/               # Aplicación principal de Flask
│   ├── app/               # Lógica de la aplicación
│   │   ├── __init__.py    # Fábrica de la aplicación
│   │   ├── routes/        # Blueprints de las rutas
│   │   ├── models/        # Modelos de la base de datos
│   │   ├── services/      # Lógica de negocio y servicios
│   │   └── static/        # Archivos estáticos
│   ├── migrations/        # Migraciones de la base de datos
│   ├── tests/             # Pruebas unitarias y de integración
│   ├── .env.example       # Archivo de ejemplo para variables de entorno
│   ├── config.py          # Clases de configuración
│   └── requirements.txt   # Dependencias de Python
├── docs/                  # Documentación del proyecto
└── README.md              # README principal
```

## 5. Modelado de Datos (Esquema de la Base de Datos)

Se diseñará un esquema de base de datos relacional y normalizado para garantizar la integridad y la escalabilidad de los datos. Las tablas principales incluirán:

*   **`distributors`**: Información sobre los distribuidores (usuarios de la plataforma).
*   **`customers`**: Información sobre los clientes de los distribuidores.
*   **`leads`**: Información sobre los prospectos.
*   **`products`**: Catálogo de productos de Herbalife.
*   **`wellness_evaluations`**: Resultados de las evaluaciones de bienestar.
*   **`conversations`**: Historial de conversaciones con los agentes de IA.
*   **`appointments`**: Citas y reuniones programadas.
*   **`agent_configs`**: Configuraciones personalizadas de los agentes para cada distribuidor.

## 6. Flujo de Desarrollo

El desarrollo seguirá un flujo de trabajo basado en `git-flow`, con las siguientes ramas principales:

*   **`main`**: Código de producción.
*   **`dev`**: Código de desarrollo (staging).
*   **`feature/<nombre-feature>`**: Ramas para el desarrollo de nuevas funcionalidades.

Todos los cambios deben ser revisados y aprobados a través de Pull Requests antes de ser fusionados en la rama `dev`.

## 7. Pruebas y Calidad del Código

Se implementará una estrategia de pruebas exhaustiva que incluirá:

*   **Pruebas Unitarias:** Para verificar el funcionamiento de componentes individuales.
*   **Pruebas de Integración:** Para asegurar que los diferentes módulos de la aplicación funcionen correctamente juntos.
*   **Pruebas End-to-End (E2E):** Para simular el flujo completo de un usuario en la aplicación.

Se utilizarán herramientas de `linting` y formateo de código para mantener un estilo de código consistente y de alta calidad.

## 8. Despliegue y Operaciones (DevOps)

La aplicación se desplegará utilizando contenedores de Docker para garantizar un entorno consistente y reproducible. Se utilizará Gunicorn como servidor de aplicaciones WSGI y Nginx como proxy inverso.

Se implementará un pipeline de CI/CD (Integración Continua / Despliegue Continuo) para automatizar el proceso de pruebas y despliegue.

## 9. Documentación Adicional

*   **`README.md`**: Proporciona una visión general del proyecto y instrucciones de instalación.
*   **`GEMINI.md`**: Define el contexto y las directrices para el desarrollo de los agentes de IA.
*   **`AGENTS.md`**: Describe la arquitectura y los roles de los diferentes agentes de IA en el sistema.
*   **API Documentation**: Se generará una documentación detallada de la API REST utilizando herramientas como Swagger o OpenAPI.
