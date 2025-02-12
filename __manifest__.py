# -*- coding: utf-8 -*-
{
    'name': 'Clinical Studies Management',
    'version': '1.0',
    'summary': 'Sistema de gestión de estudios clínicos',
    'description': """
        Sistema automatizado para la gestión integral de estudios clínicos en salud mental.
        Características principales:
        - Gestión de plantillas de estudios
        - Asignación inteligente de profesionales y participantes
        - Generación automática de calendarios de sesiones
    """,
    'category': 'Healthcare',
    'author': 'Ángel Zamora Martínez',
    'website': 'https://zamora16.github.io/clinical_studies_management',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'calendar', 'hr'],
    'data': [
        # Security
        'security/clinical_security.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        
        # Datos (estáticos)
        'data/study_speciality_data.xml',
        'data/available_days_data.xml',
        'data/study_session_data.xml',

        # Acciones
        'actions/actions.xml',
        
        # Vistas
        'views/study_session_type_views.xml',
        'views/study_template_views.xml',
        'views/study_speciality_views.xml', 
        'views/study_professional_views.xml',
        'views/study_participant_views.xml',
        'views/study_session_views.xml',
        'views/study_professional_assignment_views.xml',
        'views/assign_template_wizard_views.xml',
        'views/menu_views.xml',

        # Datos demo
        'data/demo/security_demo_data.xml',
        'data/demo/initial_data.xml',
    ],
    'demo': [],
    'application': True,
    'installable': True,
}