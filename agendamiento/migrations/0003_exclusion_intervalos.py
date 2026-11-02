from django.db import migrations

def forwards(apps,schema_editor):
    if schema_editor.connection.vendor!='postgresql':return
    # Fail without modifying appointments if historical intervals collide.
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')
    for resource,name in [('profesional_id','cita_profesional_sin_solapamiento'),('mascota_id','cita_mascota_sin_solapamiento')]:
        schema_editor.execute(f"""ALTER TABLE agendamiento_citamedica ADD CONSTRAINT {name}
            EXCLUDE USING gist ({resource} WITH =,
            tsrange(fecha + hora, fecha + hora + duracion_minutos * interval '1 minute', '[)') WITH &&)
            WHERE (estado <> 'CANCELADA')""")

def backwards(apps,schema_editor):
    if schema_editor.connection.vendor!='postgresql':return
    for name in ['cita_profesional_sin_solapamiento','cita_mascota_sin_solapamiento']:
        schema_editor.execute(f'ALTER TABLE agendamiento_citamedica DROP CONSTRAINT IF EXISTS {name}')

class Migration(migrations.Migration):
    dependencies=[('agendamiento','0002_horarioprofesional_alter_citamedica_options_and_more')]
    operations=[migrations.RunPython(forwards,backwards)]
