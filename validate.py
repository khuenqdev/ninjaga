#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,zlib
PTR_BASE=0x152E0; TEXT_END=0x172E0

def slots(rom):
 a=[]
 for i in range(113):
  p=rom[PTR_BASE+2*i]|rom[PTR_BASE+2*i+1]<<8;a.append((0x14010+p-0x8000,i))
 a.sort();return {i:(o,a[n+1][0] if n+1<len(a) else TEXT_END) for n,(o,i) in enumerate(a)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('original');ap.add_argument('patched');args=ap.parse_args();a=Path(args.original).read_bytes();b=Path(args.patched).read_bytes()
 assert len(a)==len(b)==262160,'size mismatch';assert a[PTR_BASE:PTR_BASE+226]==b[PTR_BASE:PTR_BASE+226],'pointer table changed'
 ss=slots(b); missing=[]
 for i in range(113):
  o,e=ss[i]
  try:b[o:e].index(0xF8)
  except ValueError:missing.append(i)
 assert not missing,f'missing END {missing}'
 # Menu sanity
 assert b[0x749B:0x74A0] != a[0x749B:0x74A0]
 print('size:',len(b));print('CRC32:',f'{zlib.crc32(b)&0xffffffff:08X}');print('SHA1:',hashlib.sha1(b).hexdigest());print('pointer table: unchanged');print('113/113 cutscene slots: terminated');print('menu fields: changed');print('VALIDATION OK')
if __name__=='__main__':main()
