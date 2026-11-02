import sys,os,json,getpass,re,subprocess
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
import ipaddress
os.umask(0o077)
config=Path('/etc/petcare-duckdns.json')
if '--configure' in sys.argv:
    token=getpass.getpass('Token de DuckDNS (no se mostrará): ').strip()
    if not re.fullmatch(r'[a-fA-F0-9-]{32,40}',token):
        raise SystemExit('Formato de token no válido; no se guardó.')
    config.write_text(json.dumps({'domain':'petcare-chres-pbckdn','token':token}))
    config.chmod(0o600)
    subprocess.run([sys.executable,__file__],check=True)
    subprocess.run(['systemctl','enable','--now','petcare-duckdns.timer'],check=True)
    print('DuckDNS configurado. Actualización automática cada 5 minutos y después de arrancar.')
    raise SystemExit(0)
try:
    data=json.loads(config.read_text())
    token=urlopen(Request('http://169.254.169.254/latest/api/token',method='PUT',headers={'X-aws-ec2-metadata-token-ttl-seconds':'60'}),timeout=10).read().decode()
    ip=str(ipaddress.IPv4Address(urlopen(Request('http://169.254.169.254/latest/meta-data/public-ipv4',headers={'X-aws-ec2-metadata-token':token}),timeout=10).read().decode()))
    url='https://www.duckdns.org/update?'+urlencode({'domains':data['domain'],'token':data['token'],'ip':ip})
    result=urlopen(url,timeout=20).read().decode().strip()
    if result!='OK':raise RuntimeError('DuckDNS no confirmó la actualización')
    print('DuckDNS actualizado correctamente: '+ip)
except Exception:
    raise SystemExit('No se pudo actualizar DuckDNS; revise red y configuración privada. No se muestran credenciales.')
