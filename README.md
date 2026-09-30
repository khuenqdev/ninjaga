# Ninja Gaiden NES — Vietnamese translation

This package contains the reproducible Vietnamese build and the final HUD-glyph fix.

## HUD pink-background fix

The previous build placed Vietnamese dialogue glyphs correctly in the status-bar CHR page, but encoded the generated glyph background as palette index 1. The gameplay HUD uses the font's alternate 2bpp convention, so those pixels appeared as the emulator's pink background.

The fix keeps the dialogue glyphs unchanged and creates eight HUD-only glyph tiles in previously blank tiles `F0-F7` of the status-bar font page. The static HUD/game-over/sound-test transmissions are then remapped to those codes.

HUD-only mapping:

- `F0` = Đ
- `F1` = Ể
- `F2` = À
- `F3` = ê
- `F4` = Ả
- `F5` = Ờ
- `F6` = Ị
- `F7` = Ế

The HUD glyph background is encoded as palette index 3 rather than palette index 1, eliminating the pink tile background while leaving the normal dialogue font untouched.

## Rebuild

```bash
python3 build_portable.py \
  --rom "Ninja Gaiden (USA).nes" \
  --script translation_source.txt \
  --output Ninja_Gaiden_Vietnamese_Final.nes \
  --tbl Ninja_Gaiden_Vietnamese_Final.tbl
```

The build is deterministic for the supplied source ROM and translation source.

## Apply patches

Full patch (original ROM -> final Vietnamese ROM):

```bash
python3 apply_ips.py Ninja_Gaiden_Vietnamese_Final.ips \
  "Ninja Gaiden (USA).nes" final.nes
```

HUD-only patch (previous Vietnamese build -> corrected Vietnamese build):

```bash
python3 apply_ips.py Ninja_Gaiden_Vietnamese_HUD_Fix.ips \
  Ninja_Gaiden_Vietnamese_Final_Previous.nes corrected.nes
```

## Validation

The final ROM remains 262,160 bytes. The cutscene pointer table at `0x152E0-0x153C1` is unchanged, and the 113 cutscene entries remain terminated.

The final build was reproduced from `build_portable.py` and compared byte-for-byte with the distributed final ROM.

## Emulator note

The ROM structure, CHR payload, HUD transmission bytes, patch application, and reproducibility were validated programmatically. Mesen was not available in the build environment, so live emulator execution was not performed here.
