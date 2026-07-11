# DATA NOTES — events_utc.parquet
Generated from forex_factory_calendar_2015..2025.csv (verification-first preprocessing).

## Per-file timezone findings (Stage 1)
Two scrape sessions with different browser timezones:
| year | source tz | verification status |
|---|---|---|
| 2015 | Asia/Singapore | session-verified, price-unverified range |
| 2016 | Asia/Singapore | session-verified, price-unverified range |
| 2017 | Asia/Singapore | session-verified, price-unverified range |
| 2018 | Asia/Singapore | session-verified, price-unverified range |
| 2019 | Asia/Singapore | session-verified, price-unverified range |
| 2020 | Asia/Singapore | price-verified |
| 2021 | Asia/Singapore | price-verified |
| 2022 | Asia/Singapore | price-verified |
| 2023 | Asia/Singapore | price-verified |
| 2024 | Europe/Brussels | price-verified |
| 2025 | Europe/Brussels | price-verified |

- **2015–2023 (Aug-2024 session): fixed UTC+8** (`Asia/Singapore`, no DST). Evidence is
  over-determined: NFP 8:30pm exclusively Apr–Oct (EDT) / 9:30pm exclusively Dec–Mar (EST),
  November split 7/2 exactly at the US DST-end boundary; FOMC 2:00am/3:00am next-day confirms
  both offsets independently.
- **2024–2025 (Jun-2025 session): Europe/Brussels.** Proven by both DST-desync windows:
  NFP 2024-11-01 at 1:30pm (autumn desync), FOMC 2024-03-20 / 2025-03-19 / 2025-10-29 at 7:00pm.
- **2015–2019 credibility**: these years are price-unverifiable (no price data) but belong to the
  SAME scrape session as 2020–2023, whose conversions are price-verified — so they are
  session-verified, not merely pattern-verified. Flagged `price_verified=False`.

## Conversion rule
Parse Date+Time -> tz-AWARE localize in the file's verified source tz -> convert to UTC.
Never fixed hour offsets (the DST desync weeks are exactly where those break).
Leap-day scraper bug ("Mon Feb 29", 59 rows in 2016/2020/2024): date recovered losslessly
from `Combined DateTime`'s date part.

## Drop rules (counted per year below)
Kept: rows with a parseable clock time. Dropped: All Day, Tentative, "Day X", and annotation
rows (e.g. "Oct Data") whose Combined DateTime defaulted to 00:00.
**Shutdown note (2025):** the 26 dropped 2025 annotation rows are labels adjacent to the
shutdown-DELAYED releases; the actual delayed releases (e.g. Dec 16 NFP) survive as timed rows.
No event times were inferred from schedules — actual (including delayed) release times only.

 year  rows_in  timed  all_day  day_x  annotation  tentative
 2015     4592   4350      202     38         2.0        0.0
 2016     4594   4362      202     26         4.0        0.0
 2017     4695   4457      209     28         1.0        0.0
 2018     4669   4423      213     33         0.0        0.0
 2019     4697   4463      199     30         4.0        1.0
 2020     4793   4551      213     26         3.0        0.0
 2021     4809   4582      197     28         2.0        0.0
 2022     4783   4538      203     39         2.0        1.0
 2023     4803   4555      196     47         4.0        1.0
 2024     4947   4699      201     44         3.0        0.0
 2025     5098   4825      208     37        26.0        2.0

## Price ground-truth (Stage 3): 1-min range spike vs ±60min baseline
Spike sits at minute 0 in every verifiable year; no ±60m offset spike anywhere:

 year  n_events  ratio@-60m  ratio@-1m  ratio@+0m  ratio@+1m  ratio@+60m
 2020        10        0.48       1.06       4.91       1.62        1.40
 2021         9        0.49       0.52       4.76       1.76        1.28
 2022        10        0.43       0.92       4.33       2.44        1.03
 2023        10        0.42       0.84       7.43       2.47        0.96
 2024        10        0.34       0.89       9.71       2.63        1.32
 2025        10        0.42       1.01       5.93       2.30        1.26

## Normalization
Conservative: whitespace/case cleanup + exact-variant groups. The ONLY true merge:
`ISM Non-Manufacturing PMI` -> `ISM Services PMI` (official 2020 rename). Future merge
candidates require review; do not extend the mapping silently.

## usd_tier1 (frozen pre-registered primary event set)
High-impact + USD + ['CPI m/m', 'CPI y/y', 'Core CPI m/m', 'FOMC Press Conference', 'FOMC Statement', 'Federal Funds Rate', 'Non-Farm Employment Change'].
FOMC Meeting Minutes deliberately excluded (separate release type).

## Appending future scrapes
Re-run Stage 1 (NFP/FOMC pattern classification) and Stage 3 (price spike at minute 0)
on ANY new file before merging. Assert dedupe on (ts_utc, currency, event_normalized).
