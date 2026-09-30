#!/usr/bin/env python3
from pathlib import Path
import struct
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: make_ips.py ORIGINAL ROM_PATCHED')
src=Path(sys.argv[1]).read_bytes(); dst=Path(sys.argv[2]).read_bytes()
if len(src)!=len(dst): raise SystemExit('IPS builder expects same-size ROMs')
out=bytearray(b'PATCH'); i=0
while i < len(src):
    if src[i]==dst[i]: i+=1; continue
    s=i
    while i<len(src) and src[i]!=dst[i] and i-s<0xFFFF: i+=1
    data=dst[s:i]
    # Split records further if needed.
    j=0
    while j<len(data):
        chunk=data[j:j+0xFFFF]
        off=s+j
        out += off.to_bytes(3,'big') + len(chunk).to_bytes(2,'big') + chunk
        j += len(chunk)
out += b'EOF'
Path('/mnt/data/ng_vn_final/Ninja_Gaiden_Vietnamese_Final.ips').write_bytes(out)
print('records created:', out.count(b'PATCH'))
print('size:', len(out))
