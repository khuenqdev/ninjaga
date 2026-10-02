# Ninja Gaiden Vietnamese Cutscene Selector — Final Experimental Build

## Purpose
This version implements a cutscene selector without entering the original debug stage/sound-test screen.
Normal game startup remains unchanged unless the selector is explicitly armed.

## Controls
1. Reach the static title screen.
2. Press **SELECT** once to arm the selector. SELECT is consumed by the hook, so the original debug screen does not open.
3. Press **LEFT/RIGHT** to select cutscene index 0..13. The selection wraps.
4. Press **START** to play the selected cutscene.
5. Press SELECT again at the title to disarm the selector and restore the normal startup cutscene (index 0C).

The selector state is stored in RAM `$07FF` as `$B0..$BD`; this byte was chosen because the ROM has no direct PRG references to `$07FF` and a full title/gameplay RAM trace showed it unused by the tested path.

## Correct execution path
The original title loop calls `$83A9` for controller edge detection. The hook at CPU `$8128` calls a fixed-bank helper and returns only the original START bit to the title code. Thus SELECT/LEFT/RIGHT are consumed by the hack and cannot trigger the original debug selector.

The second cutscene seed at CPU `$80B8` originally loaded constant `$0C`. It now calls a helper that either:
- loads the selected index from `$07FF & $0F` when selector mode is armed; or
- loads the original `$0C` when it is not armed.

The helper then calls the existing cutscene initializer at `$80BE`.

## Validation with supplied FCEUmm core
The supplied `fceumm_libretro.so` (FCEUmm SVN 236ccdf) was used for automated runtime tests.

- Selector off: second START produced pointer `$A78F`, which is the original cutscene-table entry 0C.
- Selected index 0: pointer `$8EFC`.
- Selected index 1: pointer `$91D7` and the translated story cutscene was visibly rendered.
- Selected index 2: pointer `$93B1`.
- Selected index 3: pointer `$9606`.
- Selected index 4: pointer `$99E7`.
- Selected index 5: pointer `$9A21`.
- Selected index 6: pointer `$9C40`.
- Selected index 7: pointer `$9CE8`.
- Selected index 8: pointer `$9D52`.
- Selected index 9: pointer `$9F5B`.
- Selected index 10: pointer `$A14F`.
- Selected index 11: pointer `$A254`.
- Selected index 12: pointer `$A78F`.
- Selected index 13: pointer `$A7BB`.

All 14 selector values reached the expected cutscene pointer without a CPU crash in the automated FCEUmm run.

## Key ROM changes
- File `$10138`: `20 A9 83` -> `20 D9 A7`.
- File `$100C8`: `A9 0C 20 BE 80` -> `20 44 A8 EA EA`.
- File `$127E9` onward: selector input helper and cutscene-seed helper, placed in the existing unused cutscene-bank area.

## Build identifiers
ROM size: 262160 bytes
SHA-1: `7a2a2c7a03b26401afc00d6292fd11faf9ac932a`
CRC32: `A7401B07`

Clean base SHA-1: `53388f0909187f03d672a5acb3a95b23a6bebb74`
IPS round-trip: exact byte-for-byte match.

## Emulator note
Runtime verification was performed with the supplied FCEUmm core. Mesen and FCEUX should be used for final manual verification because emulator frontends/debuggers can differ in input timing and diagnostics.
