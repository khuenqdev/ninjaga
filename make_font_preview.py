from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import importlib.util, re
p=Path('/mnt/data/ng_vn_final/build_vietnamese.py')
spec=importlib.util.spec_from_file_location('b',p); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
entries=b.parse_entries()
source_vi=sorted({c for t in entries.values() for c in t if ord(c)>=0x80})
b.CHAR_TO_CODE.update({c:code for c,code in zip(source_vi,b.VI_CODES)})
rom=Path('/mnt/data/Ninja Gaiden (USA).nes').read_bytes()
chars=list(b.CHAR_TO_CODE.keys())+list(b.EXTRA_TO_CODE.keys())
tiles=[]
for ch in chars:
    code=b.CHAR_TO_CODE.get(ch,b.EXTRA_TO_CODE.get(ch))
    tile=b.make_vietnamese_glyph(rom,ch) if ch in b.CHAR_TO_CODE or ch!='H' else b.base_matrix_tile(rom,ch)
    tiles.append((ch,tile,code))
scale=5; cellw=8*scale+42; cellh=8*scale+24; cols=12; rows=(len(tiles)+cols-1)//cols
img=Image.new('RGB',(cols*cellw,rows*cellh),(230,230,230)); d=ImageDraw.Draw(img)
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
except: font=None
for n,(ch,t,code) in enumerate(tiles):
    cx=n%cols; cy=n//cols; x=cx*cellw+5; y=cy*cellh+5
    p0=t[:8]; p1=t[8:]
    for yy in range(8):
        for xx in range(8):
            v=((p0[yy]>>(7-xx))&1)|(((p1[yy]>>(7-xx))&1)<<1)
            if v==2: d.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=(20,20,20))
    d.text((x,y+42),f'{ch} {code:02X}',fill=(0,0,0),font=font)
out=Path('/mnt/data/ng_vn_final/vietnamese_font_preview.png'); img.save(out); print(out, img.size, len(tiles))
