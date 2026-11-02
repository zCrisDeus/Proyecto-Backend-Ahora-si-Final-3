"""Refresh the public IP at service startup using IMDSv2. No AWS keys needed."""
import argparse
import ipaddress
import os
from pathlib import Path
import time
from urllib.request import build_opener, ProxyHandler, Request

BASE='http://169.254.169.254/latest/'

def discover(opener):
    request=Request(BASE+'api/token',method='PUT',headers={'X-aws-ec2-metadata-token-ttl-seconds':'60'})
    with opener.open(request,timeout=3) as response:
        token=response.read(4096).decode('ascii')
    request=Request(BASE+'meta-data/public-ipv4',headers={'X-aws-ec2-metadata-token':token})
    with opener.open(request,timeout=3) as response:
        address=str(ipaddress.IPv4Address(response.read(64).decode('ascii').strip()))
    if not ipaddress.ip_address(address).is_global:
        raise ValueError('EC2 no informó una IPv4 pública válida.')
    return address

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    opener=build_opener(ProxyHandler({}))
    for attempt in range(3):
        try:
            address=discover(opener)
            target=Path(args.output);temporary=target.with_suffix('.tmp')
            temporary.write_text(address+'\n',encoding='ascii');os.replace(temporary,target)
            print('IPv4 pública actualizada para PetCare.')
            return
        except Exception:
            if attempt==2:raise SystemExit('No se obtuvo la IPv4 pública. Revisa que IMDS y la IP pública estén habilitados en EC2.')
            time.sleep(2)

if __name__=='__main__':main()
