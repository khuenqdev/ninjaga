#!/usr/bin/env python3
from pathlib import Path
import hashlib, zlib
BASE=Path('/mnt/data/ng_vn_final/Ninja_Gaiden_Vietnamese_Final.nes')
OUT=Path('/mnt/data/ng_vn_final/Ninja_Gaiden_Vietnamese_Cutscene_Selector_FINAL.nes')
IPS=Path('/mnt/data/ng_vn_final/Ninja_Gaiden_Vietnamese_Cutscene_Selector_FINAL.ips')
BASE_SHA1='53388f0909187f03d672a5acb3a95b23a6bebb74'
HOOK_OFF=0x10138; HOOK_OLD=bytes.fromhex('20 a9 83'); HOOK_NEW=bytes.fromhex('20 d9 a7')
SEED_OFF=0x100c8; SEED_OLD=bytes.fromhex('a9 0c 20 be 80')
CAVE_OFF=0x127e9; CAVE_CPU=0xA7D9; STATE=0x07FF
class Asm:
 def __init__(s,o): s.o=o;s.b=bytearray();s.labels={};s.rfix=[];s.afix=[]
 def lab(s,n): s.labels[n]=s.o+len(s.b)
 def e(s,*x): s.b.extend(x)
 def imm(s,op,v): s.e(op,v)
 def zp(s,op,a): s.e(op,a)
 def ab(s,op,a): s.e(op,a&255,a>>8)
 def jmp(s,label): s.e(0x4C,0,0);s.afix.append((len(s.b)-2,label))
 def br(s,op,label): s.e(op,0);s.rfix.append((len(s.b)-1,label))
 def out(s):
  for p,n in s.afix:
   a=s.labels[n];s.b[p]=a&255;s.b[p+1]=a>>8
  for p,n in s.rfix:
   r=s.labels[n]-(s.o+p+1)
   if not -128<=r<=127: raise ValueError((n,r))
   s.b[p]=r&255
  return bytes(s.b)
def make_input():
 a=Asm(CAVE_CPU)
 a.ab(0x20,0x83A9);a.e(0xAA)               # JSR 83A9; X=new? preserve A
 a.e(0x8A);a.imm(0x29,0x20);a.br(0xF0,'no_select')
 # SELECT toggles selector state. B0-BD = armed/index 0-D, 00 = disabled.
 a.ab(0xAD,STATE);a.imm(0x29,0xF0);a.imm(0xC9,0xB0);a.br(0xD0,'enable')
 a.imm(0xA9,0);a.ab(0x8D,STATE);a.jmp('done')
 a.lab('enable');a.imm(0xA9,0xB0);a.ab(0x8D,STATE);a.jmp('done')
 a.lab('no_select')
 # RIGHT bit 0x01
 a.e(0x8A);a.imm(0x29,0x01);a.br(0xF0,'try_left')
 a.ab(0xAD,STATE);a.imm(0x29,0xF0);a.imm(0xC9,0xB0);a.br(0xD0,'done')
 a.ab(0xAD,STATE);a.imm(0x29,0x0F);a.imm(0xC9,0x0D);a.br(0xF0,'wrap_right')
 a.ab(0xEE,STATE);a.jmp('done')
 a.lab('wrap_right');a.imm(0xA9,0xB0);a.ab(0x8D,STATE);a.jmp('done')
 a.lab('try_left')
 a.e(0x8A);a.imm(0x29,0x02);a.br(0xF0,'done')
 a.ab(0xAD,STATE);a.imm(0x29,0xF0);a.imm(0xC9,0xB0);a.br(0xD0,'done')
 a.ab(0xAD,STATE);a.imm(0x29,0x0F);a.br(0xF0,'wrap_left')
 a.ab(0xCE,STATE);a.jmp('done')
 a.lab('wrap_left');a.imm(0xA9,0xBD);a.ab(0x8D,STATE)
 a.lab('done');a.e(0x8A,0x29,0x10,0x60) # return START only, consuming SELECT/L/R
 return a.out()
def make_seed(origin):
 a=Asm(origin)
 a.ab(0xAD,STATE);a.imm(0x29,0xF0);a.imm(0xC9,0xB0);a.br(0xD0,'normal')
 a.ab(0xAD,STATE);a.imm(0x29,0x0F);a.ab(0x20,0x80BE);a.e(0x60)
 a.lab('normal');a.imm(0xA9,0x0C);a.ab(0x20,0x80BE);a.e(0x60)
 return a.out()
def ips(changes):
 o=bytearray(b'PATCH')
 for off,p in sorted(changes):o+=off.to_bytes(3,'big')+len(p).to_bytes(2,'big')+p
 o+=b'EOF';return bytes(o)
d=bytearray(BASE.read_bytes());assert len(d)==262160;assert hashlib.sha1(d).hexdigest()==BASE_SHA1
assert d[HOOK_OFF:HOOK_OFF+3]==HOOK_OLD and d[SEED_OFF:SEED_OFF+5]==SEED_OLD
inp=make_input();seed_off=CAVE_OFF+len(inp);seed_cpu=CAVE_CPU+len(inp);seed=make_seed(seed_cpu)
d[HOOK_OFF:HOOK_OFF+3]=HOOK_NEW;d[SEED_OFF:SEED_OFF+5]=bytes((0x20,seed_cpu&255,seed_cpu>>8,0xEA,0xEA));d[CAVE_OFF:CAVE_OFF+len(inp)]=inp;d[seed_off:seed_off+len(seed)]=seed
OUT.write_bytes(d);IPS.write_bytes(ips([(HOOK_OFF,HOOK_NEW),(SEED_OFF,bytes((0x20,seed_cpu&255,seed_cpu>>8,0xEA,0xEA))),(CAVE_OFF,inp),(seed_off,seed)]))
print('input len',len(inp),'seed len',len(seed),'seed cpu',hex(seed_cpu));print('sha1',hashlib.sha1(d).hexdigest(),'crc',f'{zlib.crc32(d)&0xffffffff:08X}')
print('hook',d[HOOK_OFF:HOOK_OFF+3].hex(' '),'seedpatch',d[SEED_OFF:SEED_OFF+5].hex(' '))
