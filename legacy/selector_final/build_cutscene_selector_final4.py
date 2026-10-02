#!/usr/bin/env python3
from pathlib import Path
import hashlib, zlib
BASE=Path('/mnt/data/ng_vn_final/Ninja_Gaiden_Vietnamese_Final.nes')
OUT=Path('/mnt/data/ng_vn_final/Ninja_Gaiden_Vietnamese_Cutscene_Selector4.nes')
IPS=Path('/mnt/data/ng_vn_final/Ninja_Gaiden_Vietnamese_Cutscene_Selector4.ips')
BASE_SHA1='53388f0909187f03d672a5acb3a95b23a6bebb74'
HOOK_OFF=0x10138; HOOK_NEW=bytes.fromhex('20 d9 a7'); HOOK_OLD=bytes.fromhex('20 a9 83')
SEED_OFF=0x100c8; SEED_OLD=bytes.fromhex('a9 0c 20 be 80')
ROUTINE_OFF=0x127e9; ROUTINE_CPU=0xA7D9; STATE_RAM=0x07FF
class A:
 def __init__(s,o):s.o=o;s.b=bytearray();s.l={};s.f=[]
 def lab(s,n):s.l[n]=s.o+len(s.b)
 def e(s,*x):s.b.extend(x)
 def imm(s,op,v):s.e(op,v)
 def zp(s,op,a):s.e(op,a)
 def ab(s,op,a):s.e(op,a&255,a>>8)
 def br(s,op,n):s.e(op,0);s.f.append((len(s.b)-1,n))
 def out(s):
  for p,n in s.f:
   r=s.l[n]-(s.o+p+1)
   if not -128<=r<=127: raise ValueError((n,r))
   s.b[p]=r&255
  return bytes(s.b)
def input_code():
 a=A(ROUTINE_CPU)
 a.ab(0x20,0x83A9); a.e(0xAA) # preserve new-button A in X
 a.e(0x8A); a.imm(0x29,0x20); a.br(0xF0,'no_select')
 a.ab(0xAD,STATE_RAM); a.imm(0x29,0xF0); a.imm(0xC9,0xB0); a.br(0xD0,'enable')
 a.imm(0xA9,0x00); a.ab(0x8D,STATE_RAM); a.br(0x4C,'done')
 a.lab('enable'); a.imm(0xA9,0xB0); a.ab(0x8D,STATE_RAM); a.br(0x4C,'done')
 a.lab('no_select')
 a.e(0x8A); a.imm(0x29,0x01); a.br(0xF0,'try_left')
 a.ab(0xAD,STATE_RAM); a.imm(0x29,0xF0); a.imm(0xC9,0xB0); a.br(0xD0,'done')
 a.ab(0xAD,STATE_RAM); a.imm(0x29,0x0F); a.imm(0xC9,0x0D); a.br(0xF0,'wrap_right')
 a.ab(0xEE,STATE_RAM); a.br(0x4C,'done')
 a.lab('wrap_right'); a.imm(0xA9,0xB0); a.ab(0x8D,STATE_RAM); a.br(0x4C,'done')
 a.lab('try_left')
 a.e(0x8A); a.imm(0x29,0x02); a.br(0xF0,'done')
 a.ab(0xAD,STATE_RAM); a.imm(0x29,0xF0); a.imm(0xC9,0xB0); a.br(0xD0,'done')
 a.ab(0xAD,STATE_RAM); a.imm(0x29,0x0F); a.br(0xF0,'wrap_left')
 a.ab(0xCE,STATE_RAM); a.br(0x4C,'done')
 a.lab('wrap_left'); a.imm(0xA9,0xBD); a.ab(0x8D,STATE_RAM)
 a.lab('done'); a.e(0x8A,0x29,0x10,0x60)
 return a.out()
def seed_code(origin):
 a=A(origin)
 a.ab(0xAD,STATE_RAM); a.imm(0x29,0xF0); a.imm(0xC9,0xB0); a.br(0xD0,'normal')
 a.ab(0xAD,STATE_RAM); a.imm(0x29,0x0F); a.ab(0x20,0x80BE); a.e(0x60)
 a.lab('normal'); a.imm(0xA9,0x0C); a.ab(0x20,0x80BE); a.e(0x60)
 return a.out()
def ips(ch):
 o=bytearray(b'PATCH')
 for off,p in sorted(ch):o+=off.to_bytes(3,'big')+len(p).to_bytes(2,'big')+p
 o+=b'EOF';return bytes(o)
d=bytearray(BASE.read_bytes());assert hashlib.sha1(d).hexdigest()==BASE_SHA1;assert d[HOOK_OFF:HOOK_OFF+3]==HOOK_OLD;assert d[SEED_OFF:SEED_OFF+5]==SEED_OLD
inp=input_code(); soff=ROUTINE_OFF+len(inp); scpu=ROUTINE_CPU+len(inp); seed=seed_code(scpu)
d[HOOK_OFF:HOOK_OFF+3]=HOOK_NEW;d[SEED_OFF:SEED_OFF+5]=bytes([0x20,scpu&255,scpu>>8,0xEA,0xEA]);d[ROUTINE_OFF:ROUTINE_OFF+len(inp)]=inp;d[soff:soff+len(seed)]=seed
OUT.write_bytes(d);IPS.write_bytes(ips([(HOOK_OFF,HOOK_NEW),(SEED_OFF,bytes([0x20,scpu&255,scpu>>8,0xEA,0xEA])),(ROUTINE_OFF,inp),(soff,seed)]))
print('input len',len(inp),'seed len',len(seed),'seed',hex(scpu));print('sha1',hashlib.sha1(d).hexdigest(),'crc',f'{zlib.crc32(d)&0xffffffff:08X}')
