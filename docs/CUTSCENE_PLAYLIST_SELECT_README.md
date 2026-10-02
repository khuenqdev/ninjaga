# Ninja Gaiden Vietnamese — SELECT Cutscene Playlist

## Behavior

At the static title screen:

**SELECT once** → immediately starts the cutscene playlist.

No cutscene number selection, LEFT/RIGHT input, or second START press is required.

The playlist uses the game's existing cutscene engine and runs the 14 cutscene-script entries in pointer order:

`0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> A -> B -> C -> D`

After the final entry completes, the playlist state is cleared and the normal title flow resumes.

## Implementation

The hook is kept inside the game's switchable PRG bank containing the original title/cutscene code. This avoids the fixed-bank mapping problem found in the earlier prototype.

- Title input hook: file `$10138` / CPU `$8128`
- Cutscene seed hook: file `$100C8` / CPU `$80B8`
- Cutscene end hook: file `$103F0` / CPU `$83F0`
- Input helper: file `$127E9` / CPU `$A7D9`
- Seed helper: file `$12840` / CPU `$A830`
- End helper: file `$12880` / CPU `$A870`
- Playlist state: RAM `$EB` (documented as unused in the Ninja Gaiden RAM map)

SELECT sets a pending scene-0 state. On the following title-loop pass the existing START path is reused to initialize scene 0 normally. Each cutscene's normal end path changes the state to the next pending scene; the next title-loop pass then launches it automatically.

## Validation

The supplied FCEUmm libretro core was used for deterministic runtime tests.

- One SELECT pulse starts scene 0 and automatically advanced through scene 10.
- A separate tail run starting at scene B automatically advanced B -> C -> D and then cleared the playlist state.
- No additional controller input was used after SELECT.
- The ROM remains 262,160 bytes and does not expand the PRG/CHR size.

This build is intended for final manual confirmation in Mesen/FCEUX on the static title screen.
