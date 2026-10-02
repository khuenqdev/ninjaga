#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib, zlib
from apply_ips import apply_ips
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'roms'/'Ninja_Gaiden_Vietnamese_Final.nes'
OUT=ROOT/'roms'/'Ninja_Gaiden_Vietnamese_Cutscene_Playlist_SELECT_FIXED.nes'
IPS=ROOT/'patches'/'Ninja_Gaiden_Vietnamese_Cutscene_Playlist_SELECT_FIXED.ips'
EXPECTED_BASE='53388f0909187f03d672a5acb3a95b23a6bebb74'
EXPECTED_OUT='4b737cfa6e9dda81cf08dfc81b05a77a214f7a65'
def sha(p): return hashlib.sha1(p.read_bytes()).hexdigest()
def crc(p): return f'{zlib.crc32(p.read_bytes())&0xffffffff:08X}'
assert len(BASE.read_bytes())==262160 and sha(BASE)==EXPECTED_BASE
assert len(OUT.read_bytes())==262160 and sha(OUT)==EXPECTED_OUT
assert apply_ips(BASE.read_bytes(),IPS.read_bytes())==OUT.read_bytes()
print('PASS')
print('base SHA1:',sha(BASE),'CRC32:',crc(BASE))
print('playlist SHA1:',sha(OUT),'CRC32:',crc(OUT))
print('IPS round-trip: exact')
