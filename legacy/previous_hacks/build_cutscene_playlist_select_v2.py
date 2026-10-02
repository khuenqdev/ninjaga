#!/usr/bin/env python3
from pathlib import Path
import hashlib, zlib

BASE = Path('/mnt/data/ng_work/Ninja_Gaiden_Vietnamese_Final.nes')
OUT = Path('/mnt/data/ng_work/Ninja_Gaiden_Vietnamese_Cutscene_Playlist_SELECT_V2.nes')
IPS = OUT.with_suffix('.ips')
BASE_SHA1 = '53388f0909187f03d672a5acb3a95b23a6bebb74'

# Original title/cutscene code in PRG bank 4.
HOOK_OFF = 0x10138       # CPU $8128: JSR $83A9
HOOK_OLD = bytes.fromhex('20 a9 83')
HOOK_NEW = bytes.fromhex('20 d9 a7')

# End-of-cutscene decision point:
# CPU $812F / file $1013F was:
#   AD 03 03   LDA $0303
#   F0 B8      BEQ $80EC
# We replace those 5 bytes with JSR to our dispatcher + 2 NOPs.
END_OFF = 0x1013F
END_OLD = bytes.fromhex('ad 03 03 f0 b8')

# Documented unused PRG area immediately after cutscene scripts.
CAVE_OFF = 0x127E9
CAVE_CPU = 0xA7D9
STATE = 0x00EB       # documented unused RAM byte ($EB-$EF)
MARK = 0xC0          # high nibble indicates playlist active; low nibble = scene 0..D

class Asm:
    def __init__(self, origin):
        self.origin = origin
        self.b = bytearray()
        self.labels = {}
        self.rel = []
        self.absfix = []
    def here(self): return self.origin + len(self.b)
    def lab(self, n): self.labels[n] = self.here()
    def e(self, *v): self.b.extend(v)
    def imm(self, op, v): self.e(op, v)
    def emit_abs(self, op, a): self.e(op, a & 0xFF, (a >> 8) & 0xFF)
    def jsr(self, a): self.emit_abs(0x20, a)
    def jmp(self, label): self.e(0x4C, 0, 0); self.absfix.append((len(self.b)-2, label))
    def jmp_abs(self, addr): self.e(0x4C, addr & 0xFF, (addr >> 8) & 0xFF)
    def br(self, op, label): self.e(op, 0); self.rel.append((len(self.b)-1, label))
    def out(self):
        out = bytearray(self.b)
        for pos, label in self.absfix:
            a = self.labels[label]
            out[pos] = a & 0xFF; out[pos+1] = (a >> 8) & 0xFF
        for pos, label in self.rel:
            target = self.labels[label]
            base = self.origin + pos + 1
            d = target - base
            if not -128 <= d <= 127:
                raise ValueError(f'branch out of range: {label} {d}')
            out[pos] = d & 0xFF
        return bytes(out)

def build_code():
    a = Asm(CAVE_CPU)

    # ------------------------------------------------------------
    # $A7D9: title input hook
    # Called from $8128 in place of the original JSR $83A9.
    # Normal input returns the exact newly-pressed mask in A.
    # SELECT, when not already in playlist mode, starts scene 0 and
    # tail-jumps into the existing cutscene frame loop at $80EC.
    # ------------------------------------------------------------
    a.lab('input')
    a.jsr(0x83A9)          # A = newly pressed buttons
    a.e(0xAA)              # TAX: preserve it
    a.e(0x29, 0x20)       # AND #$20 (SELECT)
    a.br(0xF0, 'input_normal')

    a.emit_abs(0xAD, STATE)     # LDA $EB
    a.imm(0x29, 0xF0)      # AND #$F0
    a.imm(0xC9, MARK)      # CMP #$C0
    a.br(0xF0, 'select_restart')  # only the first SELECT while idle starts it
    a.jmp('input_normal')

    a.lab('select_restart')
    a.imm(0xA9, MARK)      # scene 0, playlist active
    a.emit_abs(0x8D, STATE)     # STA $EB
    a.imm(0xA9, 0x00)      # A = scene 0
    a.jsr(0x80BE)          # initialize existing cutscene engine
    # We are tail-calling the cutscene loop, so remove the caller's
    # return address left by JSR $A7D9 before JMP $80EC.
    a.e(0x68, 0x68)
    a.jmp('cutscene_loop')

    a.lab('input_normal')
    a.e(0x8A)              # TXA
    a.e(0x60)              # RTS

    # ------------------------------------------------------------
    # dispatcher used at $812F.
    # This location is checked every cutscene frame. $0303 == 1 means
    # the current cutscene has completed. If playlist mode is active,
    # advance to the next script and re-enter $80EC without returning
    # to the title/start logic.
    # ------------------------------------------------------------
    a.lab('dispatcher')
    a.emit_abs(0xAD, 0x0303)    # LDA $0303
    a.br(0xF0, 'still_running')

    a.emit_abs(0xAD, STATE)     # LDA $EB
    a.imm(0x29, 0xF0)
    a.imm(0xC9, MARK)
    a.br(0xD0, 'normal_finished')

    # Active playlist; increment scene index unless this was D.
    a.emit_abs(0xAD, STATE)
    a.imm(0x29, 0x0F)
    a.imm(0xC9, 0x0D)
    a.br(0xB0, 'advance')

    # Last entry D has completed. Clear playlist mode and follow the
    # game's original post-cutscene path.
    a.imm(0xA9, 0x00)
    a.emit_abs(0x8D, STATE)
    a.jmp('normal_start_path')

    a.lab('advance')
    a.e(0x18)              # CLC
    a.e(0x69, 0x01)       # ADC #1
    a.imm(0x09, MARK)      # ORA #$C0
    a.emit_abs(0x8D, STATE)     # save next scene
    a.imm(0x29, 0x0F)      # A = next scene index
    a.jsr(0x80BE)          # initialize it
    a.jmp('cutscene_loop')

    # Same behavior as original BEQ $80EC when scene is still running.
    a.lab('still_running')
    a.jmp('cutscene_loop')

    # Same behavior as the original D0 $813E path when a cutscene has
    # finished and no playlist is active.
    a.lab('normal_finished')
    a.jmp('normal_start_path')

    a.lab('normal_start_path')
    a.jmp_abs(0x8134)          # original instruction stream resumes here

    a.lab('cutscene_loop')
    a.jmp_abs(0x80EC)

    code = a.out()
    return code, a

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
    assert d[HOOK_OFF:HOOK_OFF+3] == HOOK_OLD
    assert d[END_OFF:END_OFF+5] == END_OLD

    code, asm = build_code()
    end_patch = bytes((0x20, (asm.labels['dispatcher'] & 0xFF), (asm.labels['dispatcher'] >> 8) & 0xFF, 0xEA, 0xEA))
    hook_patch = bytes((0x20, asm.labels['input'] & 0xFF, (asm.labels['input'] >> 8) & 0xFF))

    # Ensure the code fits before the next mapped area.
    assert CAVE_OFF + len(code) <= 0x12880, (hex(CAVE_OFF+len(code)))

    d[HOOK_OFF:HOOK_OFF+3] = hook_patch
    d[END_OFF:END_OFF+5] = end_patch
    d[CAVE_OFF:CAVE_OFF+len(code)] = code

    OUT.write_bytes(d)
    IPS.write_bytes(make_ips([(HOOK_OFF, hook_patch), (END_OFF, end_patch), (CAVE_OFF, code)]))

    print('base sha1', BASE_SHA1)
    print('out sha1 ', hashlib.sha1(d).hexdigest())
    print('crc32    ', f'{zlib.crc32(d)&0xffffffff:08X}')
    print('input hook', hex(asm.labels['input']), hook_patch.hex(' '))
    print('dispatcher', hex(asm.labels['dispatcher']), end_patch.hex(' '))
    print('code len  ', len(code))
    print('files     ', OUT, IPS)

if __name__ == '__main__': main()
