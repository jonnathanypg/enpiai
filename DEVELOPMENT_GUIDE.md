
# Manual de Desarrollo: Plataforma SaaS para Distribuidores de Herbalife

**Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.**

## 1. Introducción

### 1.1. Visión del Proyecto

La plataforma SaaS para distribuidores de Herbalife es un ecosistema de herramientas de software diseñado para potenciar el negocio de los distribuidores independientes. El objetivo es proporcionar una solución integral "todo en uno" que automatice y simplifique las tareas clave de la gestión de un negocio de Herbalife, permitiendo a los distribuidores centrarse en lo que mejor saben hacer: vender productos y reclutar nuevos miembros para su equipo.

La plataforma se basa en una filosofía de "cero fricción", ofreciendo una experiencia de usuario intuitiva, rápida y agradable tanto para los distribuidores como para sus clientes y prospectos.

### 1.2. Alcance del Documento

Este documento sirve como manual técnico y guía de desarrollo para el proyecto. Define la arquitectura, las tecnologías, las convenciones de codificación, los flujos de trabajo y las mejores prácticas que deben seguir todos los desarrolladores que trabajen en el proyecto.

## 2. Arquitectura del Sistema

La plataforma se construye sobre una arquitectura de microservicios, con un **Unified Gateway en FastAPI** que integra lógica de Flask y un servicio dedicado en Node.js para WhatsApp.

### 2.1. Diagrama de Arquitectura de Alto Nivel

```
+---------------------+      +---------------------+      +---------------------+
|      Frontend       |----->|   Unified Gateway   |<---->|     Base de Datos     |
| (Next.js 16/React 19)|      | (FastAPI + Flask)   |      |       (MySQL)       |
+---------------------+      +---------------------+      +---------------------+
                                     ^
                                     |
                                     v
+---------------------+      +---------------------+      +---------------------+
|     Integraciones   |----->|   Agentes de IA     |<---->|    Vector DB        |
| (Google, Mail, etc) |      | (LangGraph/Celery)  |      |      (Pinecone)     |
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

*   **Frontend:** Aplicación moderna construida con **Next.js 16** y **React 19**, utilizando App Router para optimización y Server Actions para interactividad.
*   **Unified Gateway (FastAPI):** El punto de entrada principal. Maneja webhooks asíncronos y expone APIs de alto rendimiento, mientras mantiene compatibilidad con la lógica de negocio heredada de Flask vía WSGI.
*   **API WhatsApp (Node.js):** Microservicio basado en Baileys para gestión multi-tenant de sesiones de WhatsApp.
*   **Base de Datos Relacional (MySQL):** Almacenamiento persistente con soporte para encriptación a nivel de aplicación (Sovereign SQL Layer).
*   **Base de Datos Vectorial (Pinecone):** Memoria semántica aislada por tenant (`namespace=dist_ID`).
*   **Agentes de IA:** Orquestación basada en **LangGraph** con ejecución asíncrona mediante **Celery** y **Redis**.

## 3. Pila Tecnológica (Tech Stack)

*   **Backend:** Python 3.12+, FastAPI, Flask 3.0
*   **Frontend:** Next.js 16, React 19, Tailwind CSS v4, Shadcn UI
*   **Base de Datos:** MySQL 8.0
*   **ORM:** SQLAlchemy
*   **Base de Datos Vectorial:** Pinecone
*   **Servicio de WhatsApp:** Node.js 20+ (Baileys)
*   **Autenticación:** JWT y Google OAuth
*   **Gestión de Tareas:** Celery + Redis (Puerto 6381)
*   **Despliegue:** PM2, Nginx, Docker

## 4. Estructura del Proyecto

```
/
├── api-whatsapp/          # Servicio de WhatsApp (Node.js)
├── backend/               # Aplicación principal (Unified Gateway)
│   ├── fastapi_app.py     # Entry Point FastAPI
│   ├── app.py             # App Factory Flask
│   ├── routes/            # Blueprints y Rutas
│   ├── models/            # Modelos con Encriptación PII
│   ├── services/          # Orquestación LangGraph y Lógica
│   ├── skills/            # Herramientas modulares de los agentes
│   ├── tasks.py           # Tareas de Celery
│   └── requirements.txt   # Dependencias
├── frontend/              # Aplicación Next.js 16
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
