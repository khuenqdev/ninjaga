#!/usr/bin/env python3
from pathlib import Path
import hashlib, zlib
ROM=Path(__file__).with_name("Ninja_Gaiden_Vietnamese_Cutscene_Selector_FINAL.nes")
BASE=Path(__file__).with_name("Ninja_Gaiden_Vietnamese_Final.nes")
IPS=Path(__file__).with_name("Ninja_Gaiden_Vietnamese_Cutscene_Selector_FINAL.ips")
EXPECTED_BASE="53388f0909187f03d672a5acb3a95b23a6bebb74"
EXPECTED_ROM="7a2a2c7a03b26401afc00d6292fd11faf9ac932a"
def apply(d,b):
 p=5; o=bytearray(d)
 while b[p:p+3]!=b"EOF":
  off=int.from_bytes(b[p:p+3],"big"); n=int.from_bytes(b[p+3:p+5],"big"); p+=5
  if n:
   o[off:off+n]=b[p:p+n]; p+=n
  else:
   r=int.from_bytes(b[p:p+2],"big"); v=b[p+2]; p+=3; o[off:off+r]=bytes([v])*r
 return bytes(o)
base=BASE.read_bytes(); rom=ROM.read_bytes(); assert hashlib.sha1(base).hexdigest()==EXPECTED_BASE
assert hashlib.sha1(rom).hexdigest()==EXPECTED_ROM
assert apply(base,IPS.read_bytes())==rom
print("OK")
print("ROM SHA1",EXPECTED_ROM)
print("ROM CRC32",f"{zlib.crc32(rom)&0xffffffff:08X}")
