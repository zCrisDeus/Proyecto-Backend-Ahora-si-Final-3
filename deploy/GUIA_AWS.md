# Instalación propuesta en AWS Academy

Preparada para la ruta observada `/home/ubuntu/Proyecto-back-end-3-eva` y usuario `ubuntu`. Instalada el 1 de noviembre de 2026, con respaldo previo y variables privadas. Esta guía queda como referencia; no repetir la instalación sobre el servicio activo.

## Preparación

1. Confirmar IP actual y conexión SSH. Conservar validación de clave del servidor; no desactivar StrictHostKeyChecking para resolver un cambio de IP.
2. Respaldar privadamente código, configuración Nginx y base mediante pg_dump. Verificar que el respaldo existe y es legible. No subirlo a GitHub.
3. Resolver las claves expuestas en el historial. El archivo `/etc/petcare.env` ya fue preparado y comprobado, propiedad de root, grupo ubuntu, modo 640, con DJANGO_SECRET_KEY, DB_PASSWORD, DB_NAME, DB_USER, DB_HOST=localhost, DB_PORT=5432, DJANGO_DEBUG=False y DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1. Las claves deben ser las reales del entorno, no ejemplos.
4. Para la demostración: MAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend, REMINDERS_ENABLED=False, REMINDER_ADVANCE_DAYS=1. Dejar PUBLIC_BASE_URL sin definir para que use la IP detectada. No configurar un módulo de pruebas como DJANGO_SETTINGS_MODULE.
5. Preparar la revisión en otra carpeta y comprobar dependencias Linux. No copiar el venv de Windows. Con las variables privadas cargadas por un administrador en el proceso de verificación, ejecutar `python manage.py check` y `python manage.py auditar_agenda`. Si hay conflictos, detener el despliegue.
6. Revisar la zona horaria: esta versión usa America/Santiago; la anterior usaba UTC. No convierte los campos de fecha/hora de las citas.

## Cambio controlado

Detener escrituras durante el cambio. Identificar y detener el Gunicorn anterior sin afectar otros procesos. No ejecutar un segundo servidor en el puerto ocupado. Instalar el código validado en la ruta acordada y conservar privados los archivos de entorno y respaldo.

Con las variables del servidor cargadas:

```text
python manage.py migrate
python manage.py configurar_roles
python manage.py collectstatic --noinput
```

La migración requiere btree_gist. Si falla por permisos o conflictos, no eliminar las restricciones para forzarla. Un administrador debe verificar y vincular manualmente el tutor antiguo a su usuario. Asignar cuentas del equipo mediante is_staff y el grupo apropiado; no elevar cuentas públicas automáticamente.

## Servicios e IP automática

Instalar petcare.service, petcare-recordatorios.service y petcare-recordatorios.timer en `/etc/systemd/system/`. Systemd lee `/etc/petcare.env` antes de ejecutar como ubuntu. El cargador también permite ejecutar comandos de gestión como ubuntu leyendo ese archivo privado. No reemplazarlo por el ejemplo ni cambiar sus valores sin coordinarlo con PostgreSQL.

Reemplazar el bloque PetCare existente de Nginx por nginx-petcare.conf; no habilitar dos default_server para el mismo puerto. Se mantiene proxy al puerto 8000 local y se elimina la dependencia de una IP fija en server_name.

Con la migración correcta y el proceso anterior detenido:

```text
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now petcare.service
sudo systemctl reload nginx
sudo systemctl enable --now petcare-recordatorios.timer
```

Comprobar portada, registro, login, Mi espacio, Admin y archivos estáticos desde `http://IP_ACTUAL/`. Verificar rechazo anónimo de la API y separación entre cuentas. Consultar `systemctl status petcare` y `systemctl list-timers petcare-recordatorios.timer`.

IMDSv2 se comprobó en la instancia y devuelve la IP actual, sin claves AWS ni cambios de IAM. Los servicios ya están instalados y habilitados. Sigue pendiente probar un ciclo real de apagar/encender. Si IMDS o la IP pública no están disponibles, el servicio informa un error; no sustituir los hosts permitidos por `*`. La solución asume la misma instancia y disco, no una instancia nueva creada desde cero.

## Recordatorios y prueba

El timer ejecuta `enviar_recordatorios --simular` cada cinco minutos. Persistent=true permite recuperar una ejecución al volver a arrancar. Los archivos quedan en private-mail, privados y fuera de Nginx. Para envío real configurar SMTP, activar REMINDERS_ENABLED y quitar --simular del servicio.

SSH puede seguir limitado a la IP de tu casa. La página usa 80; Gunicorn y PostgreSQL solo necesitan puertos locales. No se modificaron reglas del grupo de seguridad.

## Restauración

Si falla la verificación, detener timer y nuevo servicio, restaurar el respaldo correspondiente de código/configuración/base, iniciar el proceso anterior y verificar antes de permitir escrituras. Volver solo al código anterior no revierte migraciones. No hay script automático de restauración: las rutas del respaldo deben comprobarse al ejecutarlo.
