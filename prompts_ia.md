# Registro de apoyo de IA

## Revisión del 1 de noviembre de 2026

Herramienta: asistente Codex.

Solicitud del estudiante: revisar un clon de PetCare para detectar problemas al publicar en GitHub, analizar su relación con AWS y mejorar los templates conservando los colores, tomando como referencia el Proyecto 1 de EVA 3.

Contexto adicional aportado: el despliegue usa AWS Academy, acceso SSH con una clave PEM y arranque manual de Gunicorn con nohup en el puerto 8000. Se pidió respetar la indicación de acceder sin :8000.

Apoyo realizado: análisis de documentos, código y commits locales; revisión de solo lectura por SSH de Nginx, PostgreSQL, puertos, versiones y respuestas HTTP; nueva portada y estilos compartidos; listados conectados a la API; tratamiento de errores y acceso; variables de entorno para credenciales; permisos autenticados; archivo de exclusiones, dependencias e instrucciones de ejecución y despliegue.

Validación: comprobaciones locales con Django y base temporal. No se modificó AWS, no se publicó en GitHub, no se cambiaron modelos ni migraciones. La comprobación visual quedó pendiente por una limitación de la herramienta de navegador.

Este registro describe la asistencia actual. No reconstruye consultas anteriores ni afirma que se hayan implementado automatización de recordatorios, agenda por intervalos o permisos por tutor.

## Ampliación posterior del 1 de noviembre de 2026

Solicitud: implementar separación por tutor/rol, agenda por intervalos, recordatorios y registro público; aclarar cambio de IP de AWS Academy y apertura de SSH desde cualquier origen.

Apoyo: relación Tutor-usuario, grupos de recepción/veterinarios, límites de datos por cuenta, registro y confirmación firmada del correo, portal de autoservicio, horarios, duración y exclusiones PostgreSQL. Generación de correos en archivos para la prueba, opción SMTP y timer systemd. Detección de IP mediante IMDSv2 y servicio de arranque web. Se corrigió un error en los validadores de contraseña de la revisión previa.

Validación: 27 pruebas en PostgreSQL temporal, incluidas reservas concurrentes y conservación de datos al migrar. Consultas de cantidades y metadatos de IP en AWS, sin modificar servicios, credenciales, grupos de seguridad ni datos. No se enviaron correos reales. La sección previa describe el estado de la primera revisión; esta ampliación implementa las funciones allí pendientes.

## Separación de credenciales

A petición del estudiante se respaldó la instancia y se preparó /etc/petcare.env fuera del repositorio, conservando las credenciales vigentes. El settings.py del servidor se adaptó para leer el entorno. Se verificó la conexión como ubuntu, Django check y permisos privados. No se rotaron contraseñas, no se migró ni se desplegó la nueva aplicación. Se añadieron tres pruebas del cargador privado.

## Instalación autorizada en AWS

El estudiante solicitó instalar y migrar conservando datos. Se creó respaldo nuevo, se verificó el paquete, se aplicaron migraciones, se compararon huellas de columnas originales y se instalaron servicios web y timer de simulación. Se conservaron el tutor y el usuario existentes. Se comprobó HTTP, rechazo anónimo de la API y portada/registro en navegador. No se enviaron correos reales ni se crearon cuentas de prueba persistentes.
