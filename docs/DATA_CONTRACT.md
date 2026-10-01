# Data Contract

This canonical schema defines raw source fields. Examples show **format only**, never real Premier League records.

## Raw source fields

| Field | Meaning | Expected type | Status | Example format only |
| --- | --- | --- | --- | --- |
| Season | Competition season | string | Required | `2023/24` |
| Date | Match date | date/string | Required | `YYYY-MM-DD` |
| HomeTeam | Home team name | string | Required | `Team Name` |
| AwayTeam | Away team name | string | Required | `Team Name` |
| FTHG | Full-time home goals | integer | Required for completed match | non-negative integer |
| FTAG | Full-time away goals | integer | Required for completed match | non-negative integer |
| FTR | Full-time result | string (`H`, `D`, `A`) | Required for completed match | `H` |
| HTHG | Half-time home goals | integer | Required for completed match | non-negative integer |
| HTAG | Half-time away goals | integer | Required for completed match | non-negative integer |
| HTR | Half-time result | string (`H`, `D`, `A`) | Required for completed match | `D` |
| HS | Home shots | integer | Required | non-negative integer |
| AS | Away shots | integer | Required | non-negative integer |
| HST | Home shots on target | integer | Required | non-negative integer |
| AST | Away shots on target | integer | Required | non-negative integer |
| HC | Home corners | integer | Required | non-negative integer |
| AC | Away corners | integer | Required | non-negative integer |
| HY | Home yellow cards | integer | Optional | non-negative integer |
| AY | Away yellow cards | integer | Optional | non-negative integer |
| HR | Home red cards | integer | Optional | non-negative integer |
| AR | Away red cards | integer | Optional | non-negative integer |

## Derived analytical features

| Field | Definition |
| --- | --- |
| total_goals | `FTHG + FTAG` |
| goal_difference | `FTHG - FTAG` |
| result_label | `H → Home Win`, `D → Draw`, `A → Away Win` |
| high_scoring | `total_goals >= 4` |
| shot_difference | `HS - AS` |
| sot_difference | `HST - AST` |

Source metadata must preserve season, source, and collection method. Do not silently mix sources. Contract changes must be explicit and documented.
