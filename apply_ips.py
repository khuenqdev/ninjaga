#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=4: raise SystemExit('usage: apply_ips.py PATCH.ips INPUT.nes OUTPUT.nes')
p=Path(sys.argv[1]).read_bytes(); src=bytearray(Path(sys.argv[2]).read_bytes())
if p[:5]!=b'PATCH': raise SystemExit('bad IPS header')
i=5
while p[i:i+3]!=b'EOF':
    off=int.from_bytes(p[i:i+3],'big');i+=3
    n=int.from_bytes(p[i:i+2],'big');i+=2
    if n:
        data=p[i:i+n];i+=n
    else:
        rle=int.from_bytes(p[i:i+2],'big'); val=p[i+2]; i+=3
        data=bytes([val])*rle
    if off+len(data)>len(src): src.extend(b'\0'*(off+len(data)-len(src)))
    src[off:off+len(data)] = data
Path(sys.argv[3]).write_bytes(src)
print('wrote',sys.argv[3],len(src))
