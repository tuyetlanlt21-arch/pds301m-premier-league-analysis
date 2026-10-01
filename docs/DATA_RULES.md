# Data Validation Rules

- `HomeTeam` and `AwayTeam` must exist and must differ.
- `FTHG` and `FTAG` must be non-negative when present.
- `FTR` must be one of `H`, `D`, or `A` for completed matches.
- Consistency: home goals greater/equal/less than away goals requires `FTR` to be `H`/`D`/`A`, respectively.
- Unplayed fixtures must never be converted into 0–0 draws by filling missing results with zero.
- Potential duplicate key: `Season`, `Date`, `HomeTeam`, `AwayTeam`.
- Normalize team names before any multi-source merge; never merge external datasets by DataFrame index.

Expected lifecycle: **RAW → VALIDATE → CLEAN → NORMALIZE → FEATURE ENGINEERING → ANALYSIS**.
