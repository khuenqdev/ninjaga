#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

def apply_ips(rom: bytes, patch: bytes) -> bytes:
    if not patch.startswith(b'PATCH') or not patch.endswith(b'EOF'):
        raise ValueError('Not a valid IPS patch')
    data=bytearray(rom); p=5
    while p < len(patch)-3:
        off=int.from_bytes(patch[p:p+3],'big'); p+=3
        size=int.from_bytes(patch[p:p+2],'big'); p+=2
        if size:
            payload=patch[p:p+size]; p+=size
            end=off+size
            if end>len(data): data.extend(b'\x00'*(end-len(data)))
            data[off:end]=payload
        else:
            count=int.from_bytes(patch[p:p+2],'big'); value=patch[p+2]; p+=3
            end=off+count
            if end>len(data): data.extend(b'\x00'*(end-len(data)))
            data[off:end]=bytes([value])*count
    return bytes(data)

def main():
    ap=argparse.ArgumentParser(description='Apply an IPS patch to a ROM.')
    ap.add_argument('rom',type=Path)
    ap.add_argument('ips',type=Path)
    ap.add_argument('-o','--output',type=Path,required=True)
    a=ap.parse_args()
    out=apply_ips(a.rom.read_bytes(),a.ips.read_bytes())
    a.output.write_bytes(out)
    print(f'Wrote {a.output} ({len(out)} bytes)')
if __name__=='__main__': main()
