# Changelog

## Final selector build
- Removed the earlier debug stage-selector approach.
- Fixed the invalid-JMP assembler bug from the earlier prototype.
- Added an explicit armed/disarmed selector state.
- Consumed SELECT/LEFT/RIGHT so the original title debug handler is not triggered.
- Added runtime selection for cutscene indices 0..13.
- Preserved the normal startup cutscene when the selector is not armed.
- Validated all 14 selector values through the supplied FCEUmm core.
