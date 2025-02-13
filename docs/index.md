---
title: Clinical Studies Management
layout: page
show_sidebar: false
hero_height: is-fullwidth
---

# Clinical Studies Management

## 1. Nombre del módulo
`clinical_studies_management`

## 2. Descripción corta
Sistema automatizado para la gestión integral de estudios clínicos en salud mental. Permite configurar plantillas de estudios, gestionar asignaciones inteligentes de profesionales y participantes mediante algoritmos de puntuación, y generar automáticamente calendarios optimizados para las sesiones, asegurando eficiencia y personalización en la planificación de los estudios.

## 3. Descripción detallada de funcionalidades

### A. Gestión de Plantillas de Estudios
El sistema permitirá crear una plantilla con toda la configuración necesaria para poder automatizar la asignación de los terapeutas más adecuados para cada estudio en base a su puntuación en factores de interés como su especialidad, antigüedad, carga de trabajo u otros.

- **Configuración básica**
    - Nombre y descripción del estudio
    - Número mínimo de participantes 
    - Número mínimo de terapeutas
    - Sesiones por semana
    - Duración total estimada (calculada automáticamente)

- **Configuración de Sesiones**
    - Tipos de sesiones configurables
    - Cantidad de sesiones por tipo
    - Duración personalizada por tipo

- **Requisitos de Personal**
    - Especialidades requeridas (ej: depresión, ansiedad, adicciones)
    - Años de experiencia esperados
    - Disponibilidad horaria necesaria

### B. Asignación Automatizada de Profesionales a Plantillas
- **Motor de Asignación de Profesionales**: Esta automatización permitirá obtener una puntuación de la afinidad de un terapeuta con respecto a un proyecto. Además, asignará a los terapeutas más adecuados en función de su perfil y de las características del estudio.
    - Calcula puntuación de afinidad (0-100) basada en:
        - Experiencia (40%): Ratio entre años de experiencia y requeridos
        - Especialidades (40%): Porcentaje de coincidencia con las requeridas
        - Carga de trabajo (20%): Penalización por número de participantes activos
    - Asigna automáticamente a los N mejores profesionales que superen 60 puntos
    - Permite confirmar o declinar asignaciones manualmente

- **Motor de Asignación de Participantes**: Permite automatizar la asignación de un profesional con un participante, considerando la afinidad entre las preferencias de calendario de ambos y la carga de trabajo actual del profesional.
    - Calcula compatibilidad (0-100) basada en:
        - Compatibilidad de días (40%): Días coincidentes entre agendas
        - Franja horaria (30%): Coincidencia de preferencias horarias
        - Carga profesional (30%): Número actual de participantes
    - Asigna al profesional más compatible que supere 50 puntos

### C. Generación Automática de Calendario
- **Planificador Inteligente**: Permite generar las sesiones asociadas a un estudio para cada participante, además de añadirlas al calendario.
    - Distribución automática de sesiones respetando:
        - Número de sesiones por semana configurado
        - Tipos de sesión requeridos
        - Días disponibles comunes
        - Franjas horarias compatibles
        - Duración de cada tipo de sesión
    - Integración con calendario Odoo
    - Sistema de estados para gestión de sesiones:
        - Programada
        - Confirmada
        - Completada
        - Cancelada

## 4. Mapa del módulo
El módulo permitirá gestionar plantillas, profesionales y participantes. La asignación de profesionales a una determinada plantilla se realizará de manera automática considerando datos del estudio y del profesional. El apartado de profesionales será de consulta, para comprobar el estado de cada uno de ellos y manejar cargas de trabajo. Por último, el apartado participantes permitirá crearlos con diferentes datos que también serán utilizados para la correcta asignación de profesionales y programación de sesiones.

![Mapa Modulo](/assets/images/mapaModulo.png)

## 5. Dependencias
- `base`
- `mail`: Notificaciones
- `calendar`: Gestión de calendario
- `hr`: Información de profesionales

## 6. Wireframes
El módulo requerirá el desarrollo de las siguientes pantallas para permitir la visualización y edición de plantillas. Además, se emplearán módulos de Odoo ya existentes para las vistas de calendario y de información particular de profesionales y participantes.

### - Templates Dashboard (Home)
![Templates Dashboard](/assets/images/templatesDashboard.png)

### - New Study Template
![New Study Template](assets/images/new-study-template.png)

### - Participants Dashboard
![Participants Dashboard](assets/images/participants-dashboard.png)

### - New Participant
![New Participant](assets/images/new-participant.png)

### - Assigned Professionals
![Assigned Professionals](assets/images/assigned-professionals.png)

## 7. Control de accesos

### Grupos de Usuario

#### Study_professional_principal
- **Permisos**:
    - Permisos: CRUD en `study_template`, `study_professional_role`, `study_professional_assignment`, `study_participant`, `study_session`
    - Vista global del calendario
    - Gestión completa de asignaciones

#### Study_professional_associate
- **Permisos**:
    - Permisos: R en `study_template`, RU en sus `study_professional_role`, `study_professional_assignment`, `study_participant` y `study_session`
    - Ver su calendario
    - Gestionar sus participantes asignados

## 8. Diagramas de flujo

- **Flujo de Asignación de Profesionales a Plantilla de Estudio**: Este flujo se activa manualmente una vez se ha configurado la plantilla de un nuevo estudio. Se basa en los requisitos especificados para calcular una puntuación para cada profesional. La fórmula es la siguiente, dando puntuaciones entre 0-100.

    ![Asignación profesional-plantilla](assets/images/profesionalPlantilla.jpg)

- **Flujo de Asignación de Participante**: se activa manualmente para uno o más participantes y calcula la puntuación de afinidad profesional-participante para asignar al mejor calificado, en una escala del 0 al 100.
    ![Asignación participante-profesional](assets/images/participanteProfesional.jpg)

- **Flujo de Generación de Calendario**: se activa manualmente una vez el estudio cuenta con las sesiones configuradas, los profesionales y participantes mínimos y su asignación. Genera automáticamente la distribución de todas las sesiones del estudio y los añade al calendario como eventos.

    ![Generación calendario](assets/images/calendario.jpg)

## 9. Esquema relacional
![Esquema relacional](assets/images/ER.png)

## 10. Comunicación con otros módulos
- **Módulo mail**
    - Enviar notificaciones y recordatorios
        - Asignación de terapeuta a plantilla de estudio
        - Asignación de nuevo participante a terapeuta
        - Programación de nuevas sesiones
        - Notificaciones de cambios en el calendario
- **Módulo calendar**:
    - Gestionar sesiones clínicas
        - Sincronizar calendarios de terapeutas y pacientes
- **Módulo HR**
    - Obtener información de los terapeutas
        - Información básica
        - Especialidades y experiencia
        - Horario laboral y disponibilidad
- **Módulo base**
    - Gestión de participantes
        - Información de contacto
        - Preferencias horarias

## 11. Instalación y Configuración

- **Requisitos previos**
    - Odoo 16.0 o superior
    - Módulos base requeridos:
        - mail
        - calendar
        - hr

- **Proceso de instalación**
    - 1. Clonar repositorio en la carpeta addons de Odoo:
        ```git clone https://github.com/zamora16/clinical_studies_management.git```
    - 2. Actualizar la lista de aplicaciones en Odoo:
        - Activar modo desarrollador
        - Ir a Aplicaciones > Actualizar lista de aplicaciones
    - 3. Buscar e instalar "Clinical Studies Management"


- **Configuración inicial**
    - 1. Crear usuarios y asignar a los grupos correspondientes:
        - Gestor Principal: acceso total
        - Profesional Asociado: acceso limitado a sus registros
    - 2. Datos maestros:
        - Especialidades: El módulo incluye 15 especialidades predefinidas
        - Tipos de sesión: 3 tipos base (evaluación inicial, terapia, seguimiento)
        - Días disponibles: Configuración de días laborables
    - 3. Datos de demo incluidos:
        - 3 plantillas de estudio
        - 30 profesionales con especialidades variadas
        - 150 participantes de prueba
        - Usuarios demo:
            - Gestor: login: manager_demo / password: manager_demo
            - Profesional: login: prof_demo / password: prof_demo

- **Flujo de trabajo recomendado**
   - 1. Crear nueva plantilla de estudio:
        - Configurar requisitos básicos
        - Definir tipos y cantidad de sesiones
        - Especificar requisitos de personal
    - 2. Asignar profesionales:
        - Usar botón "Asignar Profesionales" para asignación automática
        - Se debe confirmar la asignación manualmente
    - 3. Registrar participantes:
        - Crear participantes con sus preferencias horarias
        - Usar acción masiva "Asignar plantilla" para seleccionar la template deseada
        - Usar acción masiva "Asignar profesional" para matching automático
    - 4. Generar calendario:
        - Usar botón "Generar Sesiones" en la plantilla
        - Verificar calendario generado
        - Activar plantilla para confirmar todas las sesiones