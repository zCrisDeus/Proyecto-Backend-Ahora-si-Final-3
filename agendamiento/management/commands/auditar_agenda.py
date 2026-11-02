from collections import defaultdict
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help='Revisa intervalos antes de migrar; no modifica citas y no imprime datos personales.'
    def handle(self,*args,**kwargs):
        with connection.cursor() as cursor:
            columns={c.name for c in connection.introspection.get_table_description(cursor,'agendamiento_citamedica')}
            duration='duracion_minutos' if 'duracion_minutos' in columns else '30'
            cursor.execute(f"SELECT id, profesional_id, mascota_id, fecha, hora, {duration} FROM agendamiento_citamedica WHERE estado <> 'CANCELADA'")
            rows=cursor.fetchall()
        grouped=defaultdict(list);conflicts=set()
        for pk,professional,pet,day,hour,minutes in rows:
            start=datetime.combine(day,hour);end=start+timedelta(minutes=minutes)
            for resource in [('profesional',professional),('mascota',pet)]:
                key=(*resource,day)
                for old_pk,old_start,old_end in grouped[key]:
                    if start<old_end and end>old_start:conflicts.add(tuple(sorted((old_pk,pk))))
                grouped[key].append((pk,start,end))
        for a,b in sorted(conflicts):self.stdout.write(f'Conflicto entre citas ID {a} y {b}.')
        if conflicts:raise CommandError('Resuelve los conflictos con la clínica antes de aplicar la migración de intervalos; no se alteró ningún registro.')
        self.stdout.write('Sin conflictos de intervalos detectados. Las citas anteriores sin duración se interpretan como 30 minutos.')
