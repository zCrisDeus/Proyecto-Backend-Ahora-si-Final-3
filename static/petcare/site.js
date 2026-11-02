(() => {
const toggle=document.getElementById('theme-toggle'), icon=document.getElementById('theme-icon');
function sync(){const dark=document.documentElement.dataset.bsTheme==='dark';if(icon)icon.className=dark?'bi bi-sun':'bi bi-moon';if(toggle){toggle.setAttribute('aria-pressed',String(dark));toggle.setAttribute('aria-label',dark?'Activar tema claro':'Activar tema oscuro');}}
let changingTheme=false;
sync();toggle?.addEventListener('click',async()=>{
if(changingTheme)return;
const root=document.documentElement,theme=root.dataset.bsTheme==='dark'?'light':'dark';
const apply=()=>{root.dataset.bsTheme=theme;try{localStorage.setItem('petcare-theme',theme);}catch(_){}sync();};
if(matchMedia('(prefers-reduced-motion: reduce)').matches){apply();return;}
if(!document.startViewTransition){apply();return;}
changingTheme=true;
const rect=toggle.getBoundingClientRect(),x=rect.left+rect.width/2,y=rect.top+rect.height/2;
root.style.setProperty('--theme-x',x+'px');root.style.setProperty('--theme-y',y+'px');
root.style.setProperty('--theme-radius',Math.hypot(Math.max(x,innerWidth-x),Math.max(y,innerHeight-y))+'px');
try{await document.startViewTransition(apply).finished;}finally{changingTheme=false;}
});
document.querySelectorAll('.nav-link').forEach(link=>{if(new URL(link.href).pathname===location.pathname){link.classList.add('active');link.setAttribute('aria-current','page');}});
try {if(localStorage.getItem('access_token')){document.getElementById('account-link').hidden=true;document.getElementById('logout-button').hidden=false;}}catch(_){}
document.getElementById('logout-button')?.addEventListener('click',()=>{try{localStorage.removeItem('access_token');localStorage.removeItem('refresh_token');}catch(_){}location.href='/login/';});
})();

(async()=>{try{const token=localStorage.getItem('access_token');if(!token)return;const r=await fetch('/api/usuarios/me/',{headers:{Authorization:'Bearer '+token}});if(!r.ok)return;const me=await r.json();document.documentElement.dataset.userRole=me.rol;if(me.rol==='tutor'){document.querySelectorAll('.admin-note').forEach(n=>n.hidden=true);document.querySelectorAll('.page-heading a[href^="/admin/"]').forEach(a=>{if(location.pathname==='/mascotas/')a.href='/mi-cuenta/#mascotas';else if(location.pathname==='/citas/')a.href='/mi-cuenta/#citas';else a.hidden=true;});}if(me.rol==='recepcion'){document.querySelectorAll('.nav-link').forEach(a=>{if(['/fichas/','/recordatorios/'].includes(new URL(a.href).pathname))a.hidden=true;});}}catch(_){}})();
