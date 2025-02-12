from datetime import datetime, timedelta
import random

def generate_demo_xml():
    print('<?xml version="1.0" encoding="utf-8"?>')
    print('<odoo>\n<data noupdate="1">')

    # Añadir usuarios de prueba al principio
    print('''
        <!-- Usuario Profesional Asociado -->
        <record id="demo_user_professional" model="res.users">
            <field name="name">Juan Torres</field>
            <field name="login">prof_demo</field>
            <field name="password">prof_demo</field>
            <field name="groups_id" eval="[
                (4, ref('base.group_user')),
                (4, ref('clinical_studies_management.group_study_professional_associate'))
            ]"/>
        </record>

        <!-- Usuario Gestor Principal -->
        <record id="demo_user_manager" model="res.users">
            <field name="name">Demo Gestor</field>
            <field name="login">manager_demo</field>
            <field name="password">manager_demo</field>
            <field name="groups_id" eval="[
                (4, ref('base.group_user')),
                (4, ref('clinical_studies_management.group_study_professional_principal'))
            ]"/>
        </record>''')

    # Datos de ejemplo para las plantillas
    templates = [
        {
            'name': 'Estudio de Depresión y Ansiedad',
            'participant_count': 50,
            'professional_count': 10,
            'sessions_per_week': 2,
            'total_sessions': 16,
            'required_specialities': ['depression', 'anxiety', 'ptsd'],
            'required_experience_years': 5
        },
        {
            'name': 'Programa de Adicciones',
            'participant_count': 40,
            'professional_count': 8,
            'sessions_per_week': 3,
            'total_sessions': 24,
            'required_specialities': ['addiction', 'personality', 'family'],
            'required_experience_years': 7
        },
        {
            'name': 'Terapia de Trauma',
            'participant_count': 30,
            'professional_count': 6,
            'sessions_per_week': 1,
            'total_sessions': 12,
            'required_specialities': ['ptsd', 'grief', 'psychosomatic'],
            'required_experience_years': 3
        }
    ]

    # Generar templates
    for i, template in enumerate(templates, 1):
        print(f'''
        <record id="demo_template_{i}" model="study.template">
            <field name="name">{template['name']}</field>
            <field name="participant_count">{template['participant_count']}</field>
            <field name="professional_count">{template['professional_count']}</field>
            <field name="sessions_per_week">{template['sessions_per_week']}</field>
            <field name="required_experience_years">{template['required_experience_years']}</field>
            <field name="required_specialities_ids" eval="[(6,0, [{
                ', '.join([f"ref('clinical_studies_management.speciality_{spec}')" 
                          for spec in template['required_specialities']])}])]"/>
            <field name="state">draft</field>
        </record>''')

        # Generar configuración de sesiones para cada template
        print(f'''
        <record id="demo_template_session_type_{i}_1" model="study.template.session.type">
            <field name="template_id" ref="demo_template_{i}"/>
            <field name="session_type_id" ref="clinical_studies_management.session_type_initial"/>
            <field name="quantity">1</field>
            <field name="sequence">1</field>
        </record>
        <record id="demo_template_session_type_{i}_2" model="study.template.session.type">
            <field name="template_id" ref="demo_template_{i}"/>
            <field name="session_type_id" ref="clinical_studies_management.session_type_therapy"/>
            <field name="quantity">{template['total_sessions'] - 2}</field>
            <field name="sequence">2</field>
        </record>
        <record id="demo_template_session_type_{i}_3" model="study.template.session.type">
            <field name="template_id" ref="demo_template_{i}"/>
            <field name="session_type_id" ref="clinical_studies_management.session_type_followup"/>
            <field name="quantity">1</field>
            <field name="sequence">3</field>
        </record>''')

    # Datos para generar nombres aleatorios
    nombres = [
        'Ana', 'Juan', 'María', 'Carlos', 'Laura', 'Pedro', 'Sandra', 'Miguel', 
        'Elena', 'David', 'Patricia', 'José', 'Carmen', 'Francisco', 'Isabel',
        'Antonio', 'Marta', 'Javier', 'Lucía', 'Alberto', 'Cristina', 'Jorge',
        'Paula', 'Fernando', 'Silvia', 'Raúl', 'Beatriz', 'Diego', 'Rosa', 'Pablo'
    ]
    
    apellidos = [
        'García', 'López', 'Martínez', 'Rodríguez', 'Sánchez', 'Fernández',
        'Pérez', 'González', 'Ruiz', 'Díaz', 'Torres', 'Moreno', 'Ortiz',
        'Jiménez', 'Castro', 'Vázquez', 'Ramos', 'Herrera', 'Medina', 'Cruz',
        'Romero', 'Navarro', 'Delgado', 'Morales', 'Blanco', 'Serrano', 
        'Suárez', 'Molina', 'Lara', 'Flores'
    ]

    # Lista de todas las especialidades disponibles
    all_specialities = [
        'depression', 'anxiety', 'addiction', 'ptsd', 'eating', 'personality',
        'ocd', 'bipolar', 'schizophrenia', 'child', 'geriatric', 'family',
        'psychosomatic', 'grief', 'sexual'
    ]

    # Generar profesionales
    for i in range(30):
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        email = f"{nombre.lower()}.{apellido.lower()}@example.com"
        years = random.randint(2, 15)
        
        specialities = random.sample(all_specialities, random.randint(2, 5))
        spec_refs = ", ".join([f"ref('clinical_studies_management.speciality_{spec}')" 
                             for spec in specialities])
        
        available_days = random.sample(['1', '2', '3', '4', '5'], random.randint(3, 5))
        days_refs = ", ".join([
            f"ref('clinical_studies_management.available_day_{['monday', 'tuesday', 'wednesday', 'thursday', 'friday'][int(day)-1]}')" 
            for day in available_days
        ])
        
        # Añadir user_id al primer profesional
        user_field = ''
        if i == 0:
            user_field = '\n            <field name="user_id" ref="clinical_studies_management.demo_user_professional"/>'
        
        print(f'''
        <record id="demo_professional_{i+1}" model="study.professional">
            <field name="name">{nombre} {apellido}</field>
            <field name="email">{email}</field>
            <field name="phone">+34 {random.randint(600000000, 699999999)}</field>
            <field name="years_experience">{years}</field>
            <field name="speciality_ids" eval="[(6,0, [{spec_refs}])]"/>
            <field name="available_days" eval="[(6,0, [{days_refs}])]"/>
            <field name="preferred_schedule">{random.choice(['1', '2', '3'])}</field>
            <field name="state">available</field>{user_field}
        </record>''')

    # Generar participantes
    for i in range(150):
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        email = f"{nombre.lower()}.{apellido.lower()}_{i}@example.com"
        
        available_days = random.sample(['1', '2', '3', '4', '5'], random.randint(2, 4))
        days_refs = ", ".join([
            f"ref('clinical_studies_management.available_day_{['monday', 'tuesday', 'wednesday', 'thursday', 'friday'][int(day)-1]}')" 
            for day in available_days
        ])

        print(f'''
        <record id="demo_participant_{i+1}" model="study.participant">
            <field name="name">{nombre}</field>
            <field name="surname">{apellido}</field>
            <field name="email">{email}</field>
            <field name="phone">+34 {random.randint(600000000, 699999999)}</field>
            <field name="available_days" eval="[(6,0, [{days_refs}])]"/>
            <field name="preferred_schedule">{random.choice(['1', '2', '3'])}</field>
            <field name="state">draft</field>
        </record>''')

    print('\n</data></odoo>')

if __name__ == '__main__':
    generate_demo_xml()