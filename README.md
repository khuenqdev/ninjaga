# Ninja Gaiden NES — Vietnamese Translation + SELECT Cutscene Playlist

Consolidated project pack containing the Vietnamese translation, character/control mapping, CDL data, IPS patches, SELECT cutscene-playlist hack, reproducible build/verification scripts, and earlier reference builds.

## Current release artifacts

`roms/Ninja_Gaiden_Vietnamese_Final.nes` — known-good Vietnamese translation base ROM.

`roms/Ninja_Gaiden_Vietnamese_Cutscene_Playlist_SELECT_FIXED.nes` — latest experimental SELECT-playlist ROM candidate.

`patches/Ninja_Gaiden_Vietnamese_Final.ips` — translation IPS from the earlier translation project.

`patches/Ninja_Gaiden_Vietnamese_Cutscene_Playlist_SELECT_FIXED.ips` — applies the SELECT playlist to the Vietnamese Final ROM.

`data/Ninja_Gaiden_Vietnamese_Final.tbl` — current TBL mapping, including the Vietnamese glyph values and cutscene control codes.

`data/translation_source.txt` — translation source.

`data/vn_font_payload.chr` — Vietnamese glyph payload.

`data/Ninja_Gaiden_Vietnamese_Cutscene_Selector_FINAL_USER.cdl` — latest CDL supplied by the user.

`scripts/build_cutscene_playlist_select_fixed.py` — portable current playlist builder.
`scripts/apply_ips.py` — standalone IPS applier.
`scripts/verify_playlist_fixed.py` — integrity and IPS round-trip checker.

`tools/fceumm_libretro.so` — supplied FCEUmm core used in earlier automated testing; optional.

`legacy/` contains the previous selector, debug and playlist experiments and the reference translation project archive.

## Intended current behavior

At the static title screen, one SELECT press is intended to start the story cutscene playlist. There is no cutscene-number selection and no second START press in the intended interface.

The current playlist ROM remains an experimental candidate because the user's latest manual test exposed title-screen/start-flow behavior that was not reproduced consistently by the automated test environment. The exact ROM/IPS pairing in this pack is verified byte-for-byte, but emulator/manual compatibility still requires confirmation.

## Rebuild

From the project root:

```bash
python3 scripts/build_cutscene_playlist_select_fixed.py
python3 scripts/verify_playlist_fixed.py
```

## Apply only the playlist patch

```bash
python3 scripts/apply_ips.py \
  roms/Ninja_Gaiden_Vietnamese_Final.nes \
  patches/Ninja_Gaiden_Vietnamese_Cutscene_Playlist_SELECT_FIXED.ips \
  --output roms/Ninja_Gaiden_Vietnamese_Cutscene_Playlist_SELECT_FIXED_from_IPS.nes
```

## Known hashes

Vietnamese Final base: SHA-1 `53388f0909187f03d672a5acb3a95b23a6bebb74`, CRC32 `2B119A55`.

Current playlist candidate: SHA-1 `4b737cfa6e9dda81cf08dfc81b05a77a214f7a65`, CRC32 `1941CE7C`.

The playlist IPS has three records and round-trips exactly to the ROM above when applied to the Vietnamese Final base.

## Supplemental HUD patches

`patches/Ninja_Gaiden_Vietnamese_HUD_Fix.ips` and `patches/Ninja_Gaiden_Vietnamese_HUD_Title_Fix.ips` are included for completeness from earlier work. They are not part of the current recommended playlist build sequence and should not be stacked blindly onto `Ninja_Gaiden_Vietnamese_Final.nes` without checking their intended source ROM.
