# PetCare actualizado

Proyecto 1 de EVA 3 con Django, DRF y PostgreSQL. Incluye registro público, separación por tutor/rol, agenda por intervalos y recordatorios automáticos en modo de prueba. Conserva la paleta y los templates de la revisión anterior.

Esta es una copia revisada. La carpeta del Escritorio no se reemplazó. La nueva aplicación ya fue instalada en AWS, con migraciones aplicadas y conservación verificada del tutor y del usuario anteriores. /etc/petcare.env conserva las credenciales fuera del código; los servicios web y de recordatorios simulados están habilitados. La dirección actual es http://100.58.113.144/ . La guía de instalación se conserva como referencia en `deploy/GUIA_AWS.md`.

## Funciones

- Registro público de tutores con validación de contraseña y RUT, rechazo de duplicados y confirmación de correo mediante enlace firmado que vence en 24 horas. No crea usuarios administrativos ni reclama fichas anteriores por coincidencia de correo/RUT.
- `/mi-cuenta/`: perfil y consentimiento de recordatorios, alta/edición de mascotas, consulta de disponibilidad, reserva y cancelación de citas propias.
- Listados y relaciones filtrados en el servidor: un tutor no puede acceder a datos ajenos cambiando un ID.
- Horarios semanales por profesional, duración entre 15 y 240 minutos; el portal ofrece 30, 45 y 60 minutos. Disponibilidad en pasos de 15 minutos, citas adyacentes permitidas y horas canceladas reutilizables.
- Restricciones PostgreSQL contra superposición por profesional y por mascota, además de validación y bloqueos en la aplicación.
- Recordatorios programables cada cinco minutos mediante los servicios entregados. Modo de prueba predeterminado: correos guardados en archivos privados, sin envío real.
- Arranque preparado para detectar la nueva IP de EC2 automáticamente, sin editar templates o settings en cada inicio del Lab.

## Roles

| Rol | Acceso |
| --- | --- |
| Tutor | Su perfil, mascotas, citas, fichas y recordatorios. Edita perfil/mascotas, reserva y cancela citas. No escribe datos clínicos ni elimina historias. |
| Recepción | Gestión de pacientes y citas de la clínica; consulta profesionales/horarios. No accede a fichas ni recordatorios. |
| Veterinario | Pacientes, agenda, fichas y recordatorios de la clínica. No elimina registros ni administra cuentas. |
| Administrador | Superusuario: todos los módulos, usuarios, vínculos y horarios. |

Recepción y veterinarios requieren `is_staff=True` y pertenecer al grupo `Recepcion` o `Veterinarios`. Usar un solo grupo de trabajo por cuenta y no otorgarles permisos adicionales de administración de usuarios. `python manage.py configurar_roles` crea los grupos y sincroniza sus permisos del Admin; no asigna usuarios. Una cuenta staff sin grupo ni perfil no obtiene acceso general a la API.

Los tutores existentes se conservan con `usuario=NULL`. El administrador debe verificar su identidad y vincular la cuenta desde Admin. El registro público no puede apropiarse de esas fichas.

## Ejecución local

Requisitos: Python 3.14, PostgreSQL y dependencias de requirements.txt. Versiones contrastadas con los entornos originales. La instalación de pruebas utilizó PostgreSQL 18.

Desde esta carpeta, en PowerShell 7:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DJANGO_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(64))"
$env:DJANGO_DEBUG = 'True'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1'
$env:DB_NAME = 'petcare_db'
$env:DB_USER = 'petcare_admin'
$env:DB_PASSWORD = Read-Host 'Contraseña de PostgreSQL local' -MaskInput
$env:DB_HOST = 'localhost'
$env:DB_PORT = '5432'
python manage.py check
python manage.py migrate
python manage.py configurar_roles
python manage.py createsuperuser
python manage.py runserver
```

La base y el usuario deben existir previamente. La migración requiere la extensión `btree_gist`; si el usuario no tiene permiso para crearla, el administrador de PostgreSQL debe habilitarla. No utilizar `test_settings` para una instalación real.

La clave generada solo existe en esa sesión: guardar una clave privada estable para conservar sesiones entre reinicios. `.env.example` documenta variables, no se carga automáticamente. El cargador sí lee /etc/petcare.env cuando existe (o la ruta de PETCARE_ENV_FILE). Las variables existentes del proceso tienen prioridad. En una base existente ejecutar primero `python manage.py auditar_agenda`, antes de `migrate`; acepta el esquema anterior e interpreta citas sin duración como 30 minutos. No modifica registros ni resuelve conflictos automáticamente.

## Demostración de correo sin contratar servicios

1. Crear en Admin un profesional activo y un HorarioProfesional para el día de la prueba, por ejemplo 09:00–17:00. No se inventan horarios en la migración.
2. Registrar un tutor desde `/registro/`, usando datos de prueba y un RUT válido.
3. Abrir el archivo de correo generado en `private-mail/` desde el sistema de archivos del servidor, copiar su enlace y confirmar con el botón de la página. Esa carpeta no se publica por HTTP ni se sube a GitHub.
4. Iniciar sesión, registrar una mascota y reservar una hora desde Mi espacio.
5. Como veterinario/administrador, registrar una ficha y un recordatorio para hoy o mañana. El tutor debe haber confirmado su correo y aceptado recordatorios.
6. Ejecutar el comando siguiente o esperar el timer, si ya fue instalado:

```text
python manage.py enviar_recordatorios --dry-run
python manage.py enviar_recordatorios --simular
```

`--dry-run` solo enumera IDs elegibles. `--simular` genera archivos y registra `simulado_en`, pero conserva `PENDIENTE` y no establece `enviado_en`. Una segunda ejecución no vuelve a simular el mismo registro. Esto demuestra generación automática, no recepción real; si el profesor exige recibir el correo en una bandeja, configurar SMTP.

Para envío real: backend SMTP, remitente y credenciales privadas, `REMINDERS_ENABLED=True`, y quitar `--simular` del servicio. Solo se procesan pendientes, no enviados, con consentimiento y correo confirmado, vencidos o hasta un día por delante. `REMINDER_ADVANCE_DAYS` controla la anticipación.

Un envío aceptado por SMTP establece ENVIADO; no acredita recepción final. Un fallo conserva PENDIENTE y registra intentos y el tipo de error, sin credenciales. El bloqueo de fila evita envíos simultáneos normales. Si el proceso muere después de que SMTP acepta el mensaje y antes de confirmar la transacción, un reintento podría duplicarlo: no se garantiza entrega exactamente una vez. Crear un nuevo recordatorio para un nuevo control en lugar de reciclar uno enviado/simulado.

Los correos no contienen diagnósticos ni recetas. Se accede a ellos tras iniciar sesión. No hay procesamiento mientras el Lab está apagado; al volver se retoman los pendientes.

## IP de AWS y SSH

La IP de tu casa, usada para limitar SSH, es distinta de la IP pública de EC2. Abrir SSH a `0.0.0.0/0` permite intentos de conexión desde cualquier origen y no fija la IP de la página. No se modificaron grupos de seguridad.

La solución preparada obtiene la IPv4 de EC2 mediante IMDSv2 al arrancar y la guarda en `/run/petcare/public-ip`. Django agrega esa IP a los hosts permitidos. Nginx escucha en 80 y Gunicorn queda en `127.0.0.1:8000`. Tras instalar los servicios, abrir `http://NUEVA_IP/` al encender el Lab y esperar su arranque, sin editar el proyecto.

La dirección sigue cambiando. Para una dirección siempre idéntica se necesita Elastic IP o un dominio con DNS actualizado; no se reservaron recursos. Los enlaces de correo emitidos antes de un cambio de IP pueden apuntar al destino anterior: solicitar otra confirmación desde Mi espacio.

## Migraciones y datos existentes

Se añaden campos opcionales al tutor y duración de 30 minutos a citas antiguas. No se convierte su fecha/hora ni se cambian registros automáticamente. Se usa `America/Santiago`; AWS tenía `UTC`: revisar la interpretación de los horarios históricos antes del despliegue. Los DateTimeField se muestran según la zona configurada.

Comprobación de solo lectura en AWS el 1 de noviembre de 2026: un tutor, cero mascotas y cero citas activas/completadas. Sin conflictos de intervalos. IMDSv2 devolvió correctamente la IP actual. Repetir la auditoría inmediatamente antes de migrar.

## Seguridad y límites

- Las credenciales originales siguen en el historial del repositorio antiguo. Quedan pendientes rotación coordinada y revisión de GitHub; esta copia no contiene esos secretos ni `.git`.
- Excluir claves, bases, respaldos, `.env`, logs y `private-mail/` de GitHub. Los archivos de verificación contienen enlaces privados.
- El entorno observado usa HTTP. Completar HTTPS para credenciales/datos reales fuera del laboratorio.
- JWT sigue en localStorage. Al vencer se solicita iniciar sesión otra vez; no hay recuperación pública de contraseña. La recuperación de cuentas de la demostración se realiza por Admin.
- Los límites de registro/login son básicos y por proceso. Para mayor escala usar caché compartido y límites en el proxy.
- Portada y formulario de registro se comprobaron en navegador tras desplegar. Sigue pendiente el recorrido completo con registro, perfil y reserva.

## Pruebas

Pasaron 27 pruebas en PostgreSQL 18 temporal: permisos, acceso cruzado, relaciones, registro sin privilegios, validación de contraseñas, confirmación firmada, horarios, cancelación/reutilización, reservas concurrentes, listados, páginas, simulación, fallos de correo y conservación de registros al migrar. También pasaron `check`, comprobación de migraciones y sintaxis JavaScript. No se envió correo real. Posteriormente se migró AWS y se verificó la conservación de los datos existentes.

Pruebas rápidas con SQLite; se omiten las dos pruebas específicas de PostgreSQL:

```text
python manage.py test usuarios --settings=petcare_core.test_settings
```

Para reproducir PostgreSQL, usar únicamente un clúster desechable en 127.0.0.1:55439 con usuario `petcare_test` y base inicial `postgres`. Ejecutar con `--settings=petcare_core.test_postgres_settings`; crea/elimina `test_petcare_features`. Nunca usar esos módulos en producción.

## Referencias

- [IP de EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-instance-addressing.html)
- [IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [systemd timers](https://www.freedesktop.org/software/systemd/man/256/systemd.timer.html)
- [Correo de Django](https://docs.djangoproject.com/en/dev/topics/email/)
- [Permisos de DRF](https://www.django-rest-framework.org/api-guide/permissions/)

## Estado de entrega actualizado — 2 de noviembre de 2026
URL pública: https://petcare-chres-pbckdn.duckdns.org/ . HTTPS y timer DuckDNS activos, renovación de certificado ensayada correctamente. Roles/horarios de demostración y recorrido de registro/reserva comprobados. Tema con transición animada y acceso Django Admin visible solo al rol administrador. Los datos demo no se incluyen en este repositorio. No ejecutar instalación inicial sobre la instancia activa.

