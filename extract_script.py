#!/usr/bin/env python3
from pathlib import Path
import argparse
PTR_BASE=0x152E0; TEXT_END=0x172E0
MACRO={0xF8: '<END>',0xFA:'<NL+INDENT>',0xFB:'<PAGE>',0xFC:'<DELAY>',0xFF:'<NL>'}
def ptrs(rom):
 a=[]
 for i in range(113):
  p=rom[PTR_BASE+2*i]|rom[PTR_BASE+2*i+1]<<8; a.append((0x14010+p-0x8000,i))
 a.sort(); return {i:(o,a[n+1][0] if n+1<len(a) else TEXT_END) for n,(o,i) in enumerate(a)}
def decode(seg,table):
 o=[];i=0
 while i<len(seg):
  b=seg[i]
  if b==0xF8: o.append('<END>');break
  if b in MACRO:o.append(MACRO[b]);i+=1;continue
  if b in (0xF9,0xFD,0xFE):
   if i+1>=len(seg):o.append(f'<{b:02X}>');break
   tag={0xF9:'INDENT',0xFD:'ANIM',0xFE:'SPR'}[b];o.append(f'<{tag}:{seg[i+1]:02X}>');i+=2;continue
  if b in table:o.append(table[b])
  elif 0x20<=b<=0x7E:o.append(chr(b))
  else:o.append(f'<{b:02X}>')
  i+=1
 return ''.join(o)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('rom');ap.add_argument('-o','--output',default='dump.txt');args=ap.parse_args();r=Path(args.rom).read_bytes();
 table={}
 tbl=Path(__file__).with_name('Ninja_Gaiden_Vietnamese_Final.tbl')
 for line in tbl.read_text(encoding='utf8').splitlines():
  if '=' in line and line[:2].isalnum():
   try:k=int(line[:2],16)
   except:continue
   table[k]=line[3:]
 slots=ptrs(r); out=[]
 for i in range(113):
  s,e=slots[i]; out.append(f'[{i:03d}] {decode(r[s:e],table)}')
 Path(args.output).write_text('\n\n'.join(out)+'\n',encoding='utf8')
 print('wrote',args.output)
if __name__=='__main__':main()
