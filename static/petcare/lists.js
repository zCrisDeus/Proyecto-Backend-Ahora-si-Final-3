(async () => {
const configs={
tutores:{url:'/api/pacientes/tutores/',cols:[['nombre','Nombre'],['apellidos','Apellidos'],['rut','RUT'],['telefono','Teléfono'],['email','Correo']]},
mascotas:{url:'/api/pacientes/mascotas/',cols:[['nombre','Nombre'],['especie','Especie'],['raza','Raza'],['peso_kg','Peso (kg)'],['tutor_nombre','Tutor']]},
profesionales:{url:'/api/agendamiento/profesionales/',cols:[['nombre','Nombre'],['apellidos','Apellidos'],['especialidad','Especialidad'],['activo','Activo']]},
citas:{url:'/api/agendamiento/citas/',cols:[['fecha','Fecha'],['hora','Hora'],['mascota_nombre','Mascota'],['profesional_nombre','Profesional'],['motivo','Motivo'],['estado','Estado']]},
fichas:{url:'/api/clinica/fichas/',cols:[['mascota_nombre','Mascota'],['profesional_nombre','Profesional'],['diagnostico','Diagnóstico'],['tratamiento','Tratamiento'],['receta_medica','Receta'],['examenes','Exámenes']]},
recordatorios:{url:'/api/clinica/recordatorios/',cols:[['fecha_programada','Fecha'],['mascota_nombre','Mascota'],['tipo','Tipo'],['mensaje','Mensaje'],['estado','Estado']]}
};
const cfg=configs[document.querySelector('[data-module]').dataset.module];
const body=document.getElementById('list-body'),head=document.getElementById('list-head'),search=document.getElementById('list-search'),count=document.getElementById('record-count');
const header=document.createElement('tr');for(const [,label] of cfg.cols){const th=document.createElement('th');th.scope='col';th.textContent=label;header.append(th);}head.append(header);
function message(text,login=false){body.replaceChildren();const row=document.createElement('tr'),td=document.createElement('td');td.colSpan=cfg.cols.length;td.className='list-message';td.setAttribute('role','status');td.textContent=text;if(login){td.append(document.createElement('br'));const a=document.createElement('a');a.href='/login/';a.textContent='Iniciar sesión';td.append(a);}row.append(td);body.append(row);count.textContent='Sin registros cargados';}
try{
let token;try{token=localStorage.getItem('access_token');}catch(_){}
if(!token){message('Inicia sesión para consultar los registros de la clínica.',true);return;}
const response=await fetch(cfg.url,{headers:{Authorization:'Bearer '+token}});
if(response.status===401){message('Tu sesión venció. Vuelve a ingresar para continuar.',true);return;}
if(response.status===403){message('Tu cuenta no tiene permiso para consultar estos registros.');return;}
if(!response.ok)throw new Error('request');
const data=await response.json(),rows=Array.isArray(data)?data:data.results;
if(!Array.isArray(rows))throw new Error('format');
const display=value=>value===null||value===undefined||value===''?'—':typeof value==='boolean'?(value?'Sí':'No'):String(value);
function draw(){const query=search.value.trim().toLocaleLowerCase('es');const visible=rows.filter(r=>cfg.cols.some(([key])=>display(r[key]).toLocaleLowerCase('es').includes(query)));body.replaceChildren();for(const r of visible){const tr=document.createElement('tr');for(const [key] of cfg.cols){const td=document.createElement('td');td.textContent=display(r[key]);tr.append(td);}body.append(tr);}if(!visible.length)message(rows.length?'No hay coincidencias para esta búsqueda.':'Aún no hay registros. Puedes crearlos desde Administración.');count.textContent=visible.length+' de '+rows.length+' registros'+(!Array.isArray(data)&&data.next?' · primera página':'');}
search.disabled=false;search.addEventListener('input',draw);draw();
}catch(_){message('No pudimos cargar los registros. Revisa la conexión e intenta recargar la página.');}
})();
