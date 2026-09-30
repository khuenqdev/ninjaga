#!/usr/bin/env python3
"""Fix the Vietnamese HUD glyphs in the already-built Ninja Gaiden ROM.

The gameplay status-bar transmission uses the same CHR page ($10 / file 0x30010)
for its small HUD font. The dialogue glyphs in the existing build are encoded with
transparent/background color 0, while the HUD font uses the font's alternate
2bpp palette convention. To avoid changing the dialogue glyphs, this script puts
HUD-only copies into unused tiles F0-F7 and rewrites only the HUD/menu byte strings.
"""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'Ninja_Gaiden_Vietnamese_Final.nes'
DST=ROOT/'Ninja_Gaiden_Vietnamese_Final_HUDFixed.nes'
BASE=0x30010

# Existing Vietnamese glyph IDs in the general dialogue font.
# HUD uses dedicated codes F0-F7 so dialogue rendering stays unchanged.
HUD_GLYPHS={
    0xF0: ('Đ', 0xB6),
    0xF1: ('Ể', 0xE9),
    0xF2: ('À', 0xA0),
    0xF3: ('ê', 0xAB),
    0xF4: ('Ả', 0xBF),
    0xF5: ('Ờ', 0xEA),
    0xF6: ('Ị', 0xEB),
    0xF7: ('Ế', 0xED),
}

# HUD/status-bar areas are raw PPU-tile transmissions.
HUD_START=0x742E
HUD_END=0x74A2
REMAP={src:dst for dst,(ch,src) in HUD_GLYPHS.items()}


def copy_hud_glyph(src_tile: bytes) -> bytes:
    """Convert the existing glyph mask to the HUD palette convention.

    Existing general-font glyphs use palette index 2 for the glyph. For the HUD
    font, unused/background pixels should be color 3 rather than color 1 (the
    latter is what produced the pink tile background in the previous build).
    """
    p0,p1=src_tile[:8],src_tile[8:]
    out0=[]
    out1=[]
    for y in range(8):
        b0=b1=0
        for x in range(8):
            bit=1<<(7-x)
            v=((p0[y]>> (7-x))&1) | (((p1[y]>>(7-x))&1)<<1)
            if v==2:
                # Foreground = palette 2 => p0=0,p1=1
                b1 |= bit
            else:
                # Background = palette 3 => p0=1,p1=1
                b0 |= bit
                b1 |= bit
        out0.append(b0); out1.append(b1)
    return bytes(out0+out1)


def main():
    rom=bytearray(SRC.read_bytes())
    old=bytes(rom)

    # Install HUD-only copies in the otherwise-blank F0-F7 tiles.
    for hud_code,(_,src_code) in HUD_GLYPHS.items():
        src=old[BASE+src_code*16:BASE+src_code*16+16]
        if len(src)!=16:
            raise ValueError(f'missing glyph {src_code:02X}')
        rom[BASE+hud_code*16:BASE+hud_code*16+16]=copy_hud_glyph(src)

    # Rewrite only the static HUD/menu transmissions.
    for i in range(HUD_START,HUD_END):
        b=rom[i]
        if b in REMAP:
            rom[i]=REMAP[b]

    DST.write_bytes(rom)

    # Save an explicit record of what changed for reproducibility.
    changes=[]
    for i,(a,b) in enumerate(zip(old,rom)):
        if a!=b:
            changes.append([i,a,b])
    (ROOT/'hud_fix_changes.json').write_text(json.dumps(changes,indent=2),encoding='utf-8')
    print('wrote',DST)
    print('byte changes:',len(changes))
    print('HUD-only remap:', {f'{k:02X}':f'{v:02X}' for k,v in REMAP.items()})

if __name__=='__main__': main()
