#!/usr/bin/env python3
from pathlib import Path
import hashlib
import zlib

BASE = Path('/mnt/data/ng_work/Ninja_Gaiden_Vietnamese_Final.nes')
OUT = Path('/mnt/data/ng_work/Ninja_Gaiden_Vietnamese_Cutscene_Playlist_SELECT_V3.nes')
IPS = OUT.with_suffix('.ips')
BASE_SHA1 = '53388f0909187f03d672a5acb3a95b23a6bebb74'

# Switchable-bank code hooks in the title/cutscene bank.
INPUT_HOOK_OFF = 0x10138     # CPU $8128: JSR $83A9
INPUT_HOOK_OLD = bytes.fromhex('20 a9 83')
END_HOOK_OFF = 0x1013F       # CPU $812F: LDA $0303 / BEQ $80EC
END_HOOK_OLD = bytes.fromhex('ad 03 03 f0 b8')

# Fixed final PRG bank. CPU $C000-$FFFF is always visible with MMC1.
CAVE_OFF = 0x1FA30
CAVE_CPU = 0xFA20
STATE = 0x00EB
MARK = 0xC0

class Asm:
    def __init__(self, origin):
        self.origin = origin
        self.b = bytearray()
        self.labels = {}
        self.rel = []
        self.absfix = []
    def here(self): return self.origin + len(self.b)
    def lab(self, name): self.labels[name] = self.here()
    def e(self, *v): self.b.extend(v)
    def imm(self, op, v): self.e(op, v)
    def emit_abs(self, op, addr): self.e(op, addr & 0xFF, (addr >> 8) & 0xFF)
    def jsr(self, addr): self.emit_abs(0x20, addr)
    def jmp_abs(self, addr): self.emit_abs(0x4C, addr)
    def jmp(self, label):
        self.e(0x4C, 0, 0)
        self.absfix.append((len(self.b)-2, label))
    def br(self, op, label):
        self.e(op, 0)
        self.rel.append((len(self.b)-1, label))
    def out(self):
        out = bytearray(self.b)
        for pos, label in self.absfix:
            a = self.labels[label]
            out[pos] = a & 0xFF
            out[pos+1] = (a >> 8) & 0xFF
        for pos, label in self.rel:
            target = self.labels[label]
            next_pc = self.origin + pos + 1
            delta = target - next_pc
            if not -128 <= delta <= 127:
                raise ValueError(f'branch out of range: {label}: {delta}')
            out[pos] = delta & 0xFF
        return bytes(out)

def build_code():
    a = Asm(CAVE_CPU)

    # ------------------------------------------------------------
    # INPUT HOOK: CPU $FA20
    # ------------------------------------------------------------
    a.lab('input')
    a.jsr(0x83A9)               # A = newly pressed buttons
    a.e(0xAA)                   # TAX
    a.e(0x29, 0x20)             # SELECT?
    a.br(0xF0, 'input_normal')

    # Ignore repeated SELECT while a playlist is already active.
    a.emit_abs(0xAD, STATE)
    a.imm(0x29, 0xF0)
    a.imm(0xC9, MARK)
    a.br(0xF0, 'input_select_start')
    a.jmp('input_normal')

    a.lab('input_select_start')
    a.imm(0xA9, MARK)           # C0 = playlist active, scene 0
    a.emit_abs(0x8D, STATE)
    a.imm(0xA9, 0x00)
    a.jsr(0x80BE)               # initialize cutscene 0 using existing engine
    # JSR $FA20 has left one caller return address on stack. We are
    # deliberately tail-jumping into the cutscene frame loop.
    a.e(0x68, 0x68)
    a.jmp_abs(0x80EC)

    a.lab('input_normal')
    a.e(0x8A)                   # TXA
    a.e(0x60)                   # RTS; caller then masks START as usual

    # ------------------------------------------------------------
    # CUTSCENE DISPATCHER: CPU $FA3D-ish
    # Entered with JMP from $812F, so it NEVER returns. That makes
    # per-frame rerouting safe on the 6502 stack.
    # ------------------------------------------------------------
    a.lab('dispatcher')
    a.emit_abs(0xAD, 0x0303)    # LDA $0303
    a.br(0xF0, 'still_running')

    # If no playlist is active, reproduce the original path at $8134.
    a.emit_abs(0xAD, STATE)
    a.imm(0x29, 0xF0)
    a.imm(0xC9, MARK)
    a.br(0xD0, 'normal_finished')

    # Playlist active: advance index if not already D.
    a.emit_abs(0xAD, STATE)
    a.imm(0x29, 0x0F)
    a.imm(0xC9, 0x0D)
    a.br(0xB0, 'advance')

    # D completed: clear state and resume original post-cutscene flow.
    a.imm(0xA9, 0x00)
    a.emit_abs(0x8D, STATE)
    a.jmp('normal_finished')

    a.lab('advance')
    a.e(0x18)                   # CLC
    a.e(0x69, 0x01)             # ADC #1
    a.imm(0x09, MARK)           # restore C0 marker
    a.emit_abs(0x8D, STATE)
    a.imm(0x29, 0x0F)           # A = next scene index
    a.jsr(0x80BE)               # initialize next scene
    a.jmp_abs(0x80EC)

    a.lab('still_running')
    a.jmp_abs(0x80EC)           # original BEQ target

    a.lab('normal_finished')
    a.jmp_abs(0x8134)           # original fall-through target

    return a.out(), a

def make_ips(changes):
    out = bytearray(b'PATCH')
    for off, data in sorted(changes):
        out += off.to_bytes(3, 'big')
        out += len(data).to_bytes(2, 'big')
        out += data
    out += b'EOF'
    return bytes(out)

def main():
    d = bytearray(BASE.read_bytes())
    assert len(d) == 262160
    assert hashlib.sha1(d).hexdigest() == BASE_SHA1
    assert d[INPUT_HOOK_OFF:INPUT_HOOK_OFF+3] == INPUT_HOOK_OLD
    assert d[END_HOOK_OFF:END_HOOK_OFF+5] == END_HOOK_OLD

    code, asm = build_code()
    assert len(code) <= 0x120, len(code)

    input_patch = bytes((0x20, asm.labels['input'] & 0xFF, (asm.labels['input'] >> 8) & 0xFF))
    end_patch = bytes((0x4C, asm.labels['dispatcher'] & 0xFF, (asm.labels['dispatcher'] >> 8) & 0xFF, 0xEA, 0xEA))

    # Write code into fixed-bank FF fill.
    assert all(x == 0xFF for x in d[CAVE_OFF:CAVE_OFF+len(code)])
    d[INPUT_HOOK_OFF:INPUT_HOOK_OFF+3] = input_patch
    d[END_HOOK_OFF:END_HOOK_OFF+5] = end_patch
    d[CAVE_OFF:CAVE_OFF+len(code)] = code

    OUT.write_bytes(d)
    IPS.write_bytes(make_ips([(INPUT_HOOK_OFF, input_patch), (END_HOOK_OFF, end_patch), (CAVE_OFF, code)]))

    print('ROM', OUT)
    print('IPS', IPS)
    print('size', len(d))
    print('SHA1', hashlib.sha1(d).hexdigest())
    print('CRC32', f'{zlib.crc32(d)&0xffffffff:08X}')
    print('code', len(code), f'bytes at CPU ${CAVE_CPU:04X}-${CAVE_CPU+len(code)-1:04X}')
    print('input hook', input_patch.hex(' '), '->', f'${asm.labels["input"]:04X}')
    print('end hook', end_patch.hex(' '), '->', f'${asm.labels["dispatcher"]:04X}')
    print('state RAM', f'${STATE:04X}')

if __name__ == '__main__': main()
