#!/usr/bin/env python3
from pathlib import Path
import hashlib,zlib
BASE=Path('/mnt/data/ng_work/Ninja_Gaiden_Vietnamese_Final.nes')
OUT=Path('/mnt/data/ng_work/Ninja_Gaiden_Vietnamese_Cutscene_AutoPlay_V20.nes')
IPS=Path('/mnt/data/ng_work/Ninja_Gaiden_Vietnamese_Cutscene_AutoPlay_V20.ips')
BASE_SHA1='53388f0909187f03d672a5acb3a95b23a6bebb74'
HOOK_OFF=0x10138; HOOK_OLD=bytes.fromhex('20 a9 83')
SEED_OFF=0x100c8; SEED_OLD=bytes.fromhex('a9 0c 20 be 80')
END_OFF=0x103f0; END_OLD=bytes.fromhex('a9 01 8d 03 03')
# All helpers are in the same switchable PRG bank as $8128/$80B8/$83F0.
IN_OFF=0x127e9; IN_CPU=0xA7D9
SEED_OFF_C=0x12840; SEED_CPU=0xA830
END_OFF_C=0x12880; END_CPU=0xA870
STATE=0xEB

class A:
 def __init__(s,o):s.o=o;s.b=bytearray();s.l={};s.r=[];s.a=[]
 def lab(s,n):s.l[n]=s.o+len(s.b)
 def e(s,*x):s.b.extend(x)
 def i(s,v):s.e(0xA9,v)
 def z(s,op,a):s.e(op,a)
 def m(s,op,a):s.e(op,a&255,a>>8)
 def br(s,op,n):s.e(op,0);s.r.append((len(s.b)-1,n))
 def out(s):
  for p,n in s.r:
   d=s.l[n]-(s.o+p+1)
   if not -128<=d<=127:raise ValueError((n,d))
   s.b[p]=d&255
  return bytes(s.b)

def input_helper():
 a=A(IN_CPU)
 a.m(0x20,0x83A9);a.e(0x48);a.e(0x29,0x20);a.br(0xF0,'not_select')
 a.i(0xC0);a.z(0x85,STATE);a.e(0x68);a.i(0);a.e(0x60)
 a.lab('not_select');a.e(0x68);a.e(0x48)
 a.z(0xA5,STATE);a.e(0x29,0xF0);a.e(0xC9,0xC0);a.br(0xF0,'pending');a.e(0xC9,0xB0);a.br(0xF0,'active')
 a.e(0x68);a.e(0x29,0x10);a.e(0x60)
 a.lab('pending');a.z(0xA5,STATE);a.e(0x29,0x0F);a.e(0x09,0xB0);a.z(0x85,STATE);a.e(0x68);a.i(0x10);a.e(0x60)
 a.lab('active');a.e(0x68);a.i(0);a.e(0x60)
 return a.out()

def seed_helper():
 a=A(SEED_CPU)
 a.z(0xA5,STATE);a.e(0x29,0xF0);a.e(0xC9,0xB0);a.br(0xD0,'normal')
 a.z(0xA5,STATE);a.e(0x29,0x0F);a.m(0x20,0x80BE);a.e(0x60)
 a.lab('normal');a.i(0x0C);a.m(0x20,0x80BE);a.e(0x60)
 return a.out()

def end_helper():
 a=A(END_CPU)
 a.i(1);a.m(0x8D,0x0303)
 a.z(0xA5,STATE);a.e(0x29,0xF0);a.e(0xC9,0xB0);a.br(0xD0,'done')
 a.z(0xA5,STATE);a.e(0x29,0x0F);a.e(0xC9,0x0D);a.br(0xF0,'last')
 a.e(0x18,0x69,0x01,0x29,0x0F,0x09,0xC0);a.z(0x85,STATE);a.e(0x60)
 a.lab('last');a.i(0);a.z(0x85,STATE);a.e(0x60)
 a.lab('done');a.e(0x60)
 return a.out()

def make_ips(changes):
 o=bytearray(b'PATCH')
 for off,p in sorted(changes):o+=off.to_bytes(3,'big')+len(p).to_bytes(2,'big')+p
 return bytes(o+b'EOF')

d=bytearray(BASE.read_bytes());assert len(d)==262160 and hashlib.sha1(d).hexdigest()==BASE_SHA1
assert d[HOOK_OFF:HOOK_OFF+3]==HOOK_OLD and d[SEED_OFF:SEED_OFF+5]==SEED_OLD and d[END_OFF:END_OFF+5]==END_OLD
h=input_helper();s=seed_helper();e=end_helper()
assert IN_OFF+len(h)<SEED_OFF_C;assert SEED_OFF_C+len(s)<END_OFF_C;assert END_OFF_C+len(e)<0x12920
hook=bytes((0x20,IN_CPU&255,IN_CPU>>8)); seedpatch=bytes((0x20,SEED_CPU&255,SEED_CPU>>8,0xEA,0xEA)); endpatch=bytes((0x20,END_CPU&255,END_CPU>>8,0xEA,0xEA))
d[HOOK_OFF:HOOK_OFF+3]=hook;d[SEED_OFF:SEED_OFF+5]=seedpatch;d[END_OFF:END_OFF+5]=endpatch
d[IN_OFF:IN_OFF+len(h)]=h;d[SEED_OFF_C:SEED_OFF_C+len(s)]=s;d[END_OFF_C:END_OFF_C+len(e)]=e
OUT.write_bytes(d);IPS.write_bytes(make_ips([(HOOK_OFF,hook),(SEED_OFF,seedpatch),(END_OFF,endpatch),(IN_OFF,h),(SEED_OFF_C,s),(END_OFF_C,e)]))
print('lens',len(h),len(s),len(e));print('sha1',hashlib.sha1(d).hexdigest());print('crc32',f'{zlib.crc32(d)&0xffffffff:08X}')
print('hooks',hook.hex(' '),seedpatch.hex(' '),endpatch.hex(' '));print('input',h.hex(' '));print('seed',s.hex(' '));print('end',e.hex(' '))
