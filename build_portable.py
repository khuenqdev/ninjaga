#!/usr/bin/env python3
"""Reproducibly build the Vietnamese Ninja Gaiden ROM from the original ROM.

Usage:
    python3 build_portable.py \
        --rom "Ninja Gaiden (USA).nes" \
        --script translation_source.txt \
        --output Ninja_Gaiden_Vietnamese_Final.nes
"""
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, re, unicodedata, zlib

PTR_BASE=0x152E0
TEXT_END=0x172E0
FONT_BASE=0x30010
VI_CODES=list(range(0xA0,0xE8))  # 72 chars
EXTRA_CODES=list(range(0xE8,0xF8))
EXTRA_MENU=['H','Ể','Ờ','Ị','Ả','Ế']
# HUD-only glyph slots in otherwise-unused tiles F0-F7 of the status-bar CHR page.
HUD_GLYPHS={'Đ':0xF0,'Ể':0xF1,'À':0xF2,'ê':0xF3,'Ả':0xF4,'Ờ':0xF5,'Ị':0xF6,'Ế':0xF7}
HUD_REMAP={0xB6:0xF0,0xE9:0xF1,0xA0:0xF2,0xAB:0xF3,0xBF:0xF4,0xEA:0xF5,0xEB:0xF6,0xED:0xF7}
BASE_HUD={'A':0x0A,'C':0x0B,'E':0x0C,'G':0x0D,'I':0x0E,'J':0x0F,'M':0x10,'N':0x11,'O':0x12,'P':0x13,'R':0x14,'S':0x15,'T':0x16,'Y':0x17}
MACROS={'<NL>':bytes([0xFF]),'<NL+INDENT>':bytes([0xFA]),'<PAGE>':bytes([0xFB]),'<DELAY>':bytes([0xFC]),'<END>':bytes([0xF8])}
for i in range(256):
    MACROS[f'<ANIM:{i:02X}>']=bytes([0xFD,i]); MACROS[f'<SPR:{i:02X}>']=bytes([0xFE,i]); MACROS[f'<INDENT:{i:02X}>']=bytes([0xF9,i])

def parse_script(p: Path):
    s=p.read_text(encoding='utf-8'); d={int(m.group(1)):m.group(2) for m in re.finditer(r'^\[(\d{3})\]\s*(.*?)\s*(?=^\[\d{3}\]|\Z)',s,re.S|re.M)}
    if len(d)!=113: raise ValueError(f'expected 113 entries, got {len(d)}')
    return d

def pointers(rom):
    a=[]
    for i in range(113):
        cpu=rom[PTR_BASE+2*i] | rom[PTR_BASE+2*i+1]<<8
        off=0x14010 + cpu - 0x8000
        a.append((off,i,cpu))
    a.sort(); slots={}
    for n,(off,i,cpu) in enumerate(a):
        end=a[n+1][0] if n+1<len(a) else TEXT_END
        if end<=off: raise ValueError(f'bad slot {i}')
        slots[i]=(off,end,cpu)
    return slots

def encode_text(t,mapv):
    out=bytearray(); i=0
    while i<len(t):
        if t[i]=='<':
            j=t.find('>',i); tok=t[i:j+1]
            if tok not in MACROS: raise ValueError('unknown token '+tok)
            out += MACROS[tok]; i=j+1; continue
        ch=t[i]
        if ch in mapv: out.append(mapv[ch])
        elif ord(ch)<128: out.append(ord(ch))
        else: raise ValueError(f'unmapped character {ch!r} U+{ord(ch):04X}')
        i+=1
    return bytes(out)

def tile_matrix(tile):
    p0,p1=tile[:8],tile[8:16]; m=[]
    for y in range(8):
        row=[]
        for x in range(8): row.append(((p0[y]>>(7-x))&1)|(((p1[y]>>(7-x))&1)<<1))
        m.append(row)
    return m

def encode_mask(mask):
    p0=[];p1=[]
    for y in range(8):
        b0=b1=0
        for x,on in enumerate(mask[y]):
            bit=1<<(7-x)
            if not on: b0|=bit
            else: b1|=bit
        p0.append(b0);p1.append(b1)
    return bytes(p0+p1)

def shift_up(m): return [m[y+1][:] if y<7 else [0]*8 for y in range(8)]

def accent_mask(ch,rom):
    if ch=='H': return None
    if ch in ('Đ','đ'): base,marks=('D' if ch=='Đ' else 'd',{'bar'})
    else:
        n=unicodedata.normalize('NFD',ch); base=n[0]; marks=set(n[1:])
    src=tile_matrix(rom[FONT_BASE+ord(base)*16:FONT_BASE+ord(base)*16+16])
    m=[[1 if v==2 else 0 for v in r] for r in src]
    if base.islower(): m=shift_up(m)
    def put(x,y):
        if 0<=x<8 and 0<=y<8: m[y][x]=1
    for mark in marks:
        if mark=='\u0300': put(2,0);put(3,1)
        elif mark=='\u0301': put(5,0);put(4,1)
        elif mark=='\u0303':
            for x,y in [(2,0),(3,1),(4,0),(5,1)]: put(x,y)
        elif mark=='\u0309': put(4,0);put(5,0);put(5,1)
        elif mark=='\u0302':
            for x,y in [(2,1),(3,0),(4,1)]: put(x,y)
        elif mark=='\u0306':
            for x,y in [(2,1),(3,0),(4,0),(5,1)]: put(x,y)
        elif mark=='\u031B':
            for x,y in [(5,1),(6,0),(7,1)]: put(x,y)
        elif mark=='\u0323': put(3,7);put(4,7)
        elif mark=='bar':
            for x in range(1,7): put(x,4)
    return encode_mask(m)

def hudify(tile):
    """Convert a general-font glyph into the HUD font's palette convention."""
    p0,p1=tile[:8],tile[8:16]
    o0=[]; o1=[]
    for y in range(8):
        b0=b1=0
        for x in range(8):
            bit=1<<(7-x)
            v=((p0[y]>>(7-x))&1) | (((p1[y]>>(7-x))&1)<<1)
            if v==2:
                # foreground = palette 2
                b1 |= bit
            else:
                # background = palette 3; avoids the pink color-1 background
                b0 |= bit; b1 |= bit
        o0.append(b0); o1.append(b1)
    return bytes(o0+o1)

def hud_encode(text,vi,extra):
    out=[]
    for ch in text:
        if ch==' ': out.append(0xFF)
        elif ch=='-': out.append(0x18)
        elif ch=='$': out.append(0x1B)
        elif ch in vi: out.append(vi[ch])
        elif ch in extra: out.append(extra[ch])
        elif ch in BASE_HUD: out.append(BASE_HUD[ch])
        else: raise ValueError('HUD unmapped '+repr(ch))
    return bytes(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rom',required=True);ap.add_argument('--script',default='translation_source.txt');ap.add_argument('--output',required=True);ap.add_argument('--tbl',default='Ninja_Gaiden_Vietnamese_Final.tbl');args=ap.parse_args()
    rom=bytearray(Path(args.rom).read_bytes()); original=bytes(rom); entries=parse_script(Path(args.script));
    vi_chars=sorted({c for t in entries.values() for c in t if ord(c)>=128})
    if len(vi_chars)!=72: raise ValueError(f'need 72 Vietnamese glyphs, got {len(vi_chars)}')
    vi={c:code for c,code in zip(vi_chars,VI_CODES)}; extra={c:code for c,code in zip(EXTRA_MENU,EXTRA_CODES)}
    slots=pointers(original)
    for idx in range(113):
        data=encode_text(entries[idx],vi); off,end,_=slots[idx]
        if len(data)>end-off: raise ValueError(f'entry {idx:03d} exceeds slot {len(data)}>{end-off}')
        rom[off:off+len(data)]=data
        if off+len(data)<end: rom[off+len(data)]=0xF8
    # Custom font tiles are stored where the text byte values A0-E7 and the six menu-only
    # values E8-ED are available in the game font page.
    for ch,code in vi.items(): rom[FONT_BASE+code*16:FONT_BASE+code*16+16]=accent_mask(ch,original)
    for ch,code in extra.items(): rom[FONT_BASE+code*16:FONT_BASE+code*16+16]=(original[FONT_BASE+ord('H')*16:FONT_BASE+ord('H')*16+16] if ch=='H' else accent_mask(ch,original))
    # Install separate HUD copies. The HUD uses the same CHR page but a different
    # palette convention, so the dialogue glyphs above must not be changed.
    for ch,code in HUD_GLYPHS.items():
        source_code = vi.get(ch) or extra.get(ch)
        if source_code is None: raise ValueError(f'HUD glyph source missing {ch!r}')
        glyph = rom[FONT_BASE+source_code*16:FONT_BASE+source_code*16+16]
        rom[FONT_BASE+code*16:FONT_BASE+code*16+16] = hudify(glyph)
    # Fixed HUD/menu fields documented in the attached reference project.
    for off,text in {0x7431:'ĐIỂM-',0x743E:'MÀN-$ ',0x7447:'GIỜ-  ',0x7454:'NINJA-',0x7472:'ĐỊCH- ',0x7491:'CẢNH- '}.items():
        b=hud_encode(text,vi,extra); b=b+bytes([0xFF])*(6-len(b)); rom[off:off+6]=b
    go=hud_encode('HẾT',vi,extra); rom[0x7484:0x7484+9]=go+bytes([0xFF])*(9-len(go))
    rom[0x749B:0x74A0]=hud_encode('TIẾNG',vi,extra)
    # Switch HUD-only Vietnamese glyph codes in all fixed status-bar/game-over strings.
    for i in range(0x742E,0x74A2):
        if rom[i] in HUD_REMAP:
            rom[i]=HUD_REMAP[rom[i]]
    Path(args.output).write_bytes(rom)
    tbl=['; Standard ASCII 0x20-0x7E retained; Vietnamese uses A0-E7; menu-only glyphs use E8-ED.','']
    for c in range(0x20,0x7F): tbl.append(f'{c:02X}={chr(c)}')
    tbl += [''] + [f'{code:02X}={c}' for c,code in vi.items()] + [''] + [f'{code:02X}={c}' for c,code in extra.items()] + [''] + [f'{code:02X}={c} ; HUD-only' for c,code in HUD_GLYPHS.items()] + ['F8=<END>','F9=<INDENT:n>','FA=<NL+INDENT>','FB=<PAGE>','FC=<DELAY>','FD=<ANIM:n>','FE=<SPR:n>','FF=<NL>']
    Path(args.tbl).write_text('\n'.join(tbl)+'\n',encoding='utf-8')
    print('CRC32',f'{zlib.crc32(rom)&0xffffffff:08X}');print('SHA1',hashlib.sha1(rom).hexdigest());print('size',len(rom));print('OK')
if __name__=='__main__': main()
