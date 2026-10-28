# The card format — `accord-log/1`

**Status: implemented in deployed v0.6.0 and verified on real boot and
reinsertion files on 2026-10-24.** See the hardware review below and
`../../archive/root-history-2026-10-27/STATUS_REVIEW_2026-10-24.md`. The boot-before-clock rename metadata
finding remains open; compatibility must be preserved for existing cards.
Implements `../../ARCHITECTURE.md` ("the SD card is a first-class artifact")
and the first task of `SEED_firmware_agent.md`.

The requirement this exists to meet, in one sentence: **a stranger with the
card, no server and no access to this repository must be able to turn the file
into miles and volts.**

---

## 1. What a card file looks like

```
# accord-log/1
# log.unit chip=E6614C311B3A3231 vehicle=accord-1 fw=0.6.0
# log.file name=/20261024_101530.CSV opened_ms=540 clock=sntp
# log.columns ms,vss_total,vss_hz,tach_total,tach_hz,rpm,brake,fuel_counts,fuel_lo,fuel_hi,supply_counts,die_counts,ms_since_ign,ign
# log.stable 7
# log.pins vss=GP2 tach=GP3 brake=GP4 ign=GP5 fuel=GP26 supply=GP27
# log.pulses vss_per_mile=4104.3 band=4103.19..4105.42 asof=2026-10-18 source=tripd-refit authority=downstream
# log.adc bits=12 vref_v=3.3 burst=2000 die=rp2040-internal
# log.adc.fuel div=7500/4700 ratio=0.3852 full_scale_v=8.57
# log.adc.supply div=22000/4700 ratio=0.1760 full_scale_v=18.75 dark_counts=155
# log.means brake=1:line-grounded ign=1:on ms_since_ign=0:key-out glitch_us=100
# log.end
1004,0,0.00,0,0.00,0,1,1850,1844,1861,160,2714,0,0
2004,0,0.00,0,0.00,0,1,1851,1843,1860,160,2713,0,0
...
```

Then 1 Hz CSV rows, with `#` status notes interleaved as they always have been.

## 2. The rules a reader may rely on, forever

1. **Every line that is not a CSV data row begins with `#`.** This predates the
   header and is load-bearing well beyond it: `vssrec` classifies a line as a
   note purely on that first byte, and a bare continuation line once became a
   phantom sample gap. The header does not get an exception.
2. **The first line of a card file is the format token**, `# accord-log/1`,
   and it is the only header line not in the `log.` namespace — it is the magic
   number, so it is meant to be recognisable by eye and by `file(1)`-style
   sniffing. A reader that does not recognise the token should stop rather than
   guess. `1` changes only if an existing key changes meaning — never for a new
   key, never for a new column.
3. **Every other header line is `# log.<tag>`, and order is not significant.**
   Parse by tag, never by line number. `log.` is a **reserved namespace**: no
   status note, diagnostic or human line may ever begin with it, which is what
   makes the machine block unambiguously separable from the rest of the stream.
   This matters concretely — `help()` already prints a *human* `# columns: …`
   line, so a bare `columns` tag would have collided with it on day one.
   `# log.adc.fuel` and `# log.adc.supply` are two instances of one tag family
   distinguished by the suffix, so further channels can be added the same way.
4. **Unknown header tags and unknown `key=value` pairs must be ignored**, not
   treated as errors. This is the whole extension mechanism.
5. **`# log.end` terminates the block.** Everything after it is rows and
   ordinary notes. A reader may also simply stop at the first line that does
   not start with `#`, but the explicit terminator means a truncated header is
   detectable rather than silently short.
6. **`log.columns` is authoritative for this file.** Do not assume a width. The
   archive contains 7-column and 8-column files and the live firmware writes
   14; a reader that trusts `log.columns` handles all of them and whatever comes
   next.
7. **`log.stable N` is the count of leading columns that will never be reordered
   or removed** (currently 7: `ms` through `brake`). Everything past it is
   append-only and may be absent in older files. This is the firmware-side
   statement of `tripd`'s `N_CORE_COLS`, which counts 8 because it counts the
   `wall` column `vssrec` prepends. **Two different numbers for the same
   contract; see §6.**
8. **Rows are raw.** Counts, not volts. Pulses, not miles. Nothing in a row has
   a calibration applied to it, and nothing ever will — a count plus a stored
   calibration can be re-derived when the calibration changes, and a volt
   cannot be un-derived.

## 3. Every header line, and why it is there

| tag | carries | why it must be on the card |
|---|---|---|
| `accord-log/1` | format version (the magic line) | a reader must be able to refuse a format it does not know |
| `log.unit` | `chip`, `vehicle`, `fw` | ARCHITECTURE: "no unit or vehicle identity — fine for one car; required the moment there are two". `chip` is the RP2040's unique board id, the same string the USB serial uses, so it needs no configuration and cannot be mis-set |
| `log.file` | `name`, `opened_ms`, `clock` | lets a card-only reader rebuild absolute time. `opened_ms` is the `millis()` at which the file opened and `clock=sntp\|none` says whether the name's timestamp is trustworthy. `cardconv.py` already reconstructs `wall` from exactly these anchors; this stops it having to infer them |
| `log.columns` | the names, in order | removes all width guessing |
| `log.stable` | the no-reorder count | tells an indexing parser how much it may index |
| `log.pins` | the pin map | identifies *which signal* each column came from, which no amount of data analysis recovers |
| `log.pulses` | `vss_per_mile` + its band + provenance | ARCHITECTURE: "lives only in `tripd`. Card-only users have pulses and no path to miles" |
| `log.adc`, `log.adc.*` | bits, vref, burst, dividers, ratios, full scale, dark threshold | ARCHITECTURE: "raw counts are logged, correctly, but counts -> volts needs 0.3852 and 0.1760" |
| `log.means` | the polarity of every encoded level | `brake=1` means the warning line is grounded, which is the parking brake **or** low fluid; `ign=1` means on while the *pin* reads low. Polarity is the single easiest thing for a later reader to get backwards |
| `log.end` | nothing | makes truncation detectable |

## 4. `pulses_per_mile` is on the card as provenance, not as authority

This is the one entry that needs an explicit rule, and the reason is in the
project's own data.

`tripd` carries `PULSES_PER_MILE = 4104.3`, refit on 2026-10-18 from a
384-mile trip to a feasible band of `[4103.19, 4105.42]`. On 2026-10-24 a fuel
reconciliation over a 398.8-mile span required ppm in `(4103.096, 4104.125]`
— which intersects the documented band but **excludes 4104.3 itself.** The
central value in force is already just outside the newest evidence.

So a constant written onto a card in October is not going to be the best
estimate in December, and the architecture's first principle is that
improvements apply *retroactively to every drive already taken*. Therefore:

- `vss_per_mile` on the card is **what the firmware was told, when, and by
  whom** — enough for a card-only reader to get miles to about 0.03%, and
  enough to reproduce exactly what a contemporaneous reading would have said.
- `band` is published with it because **a point value without its interval is
  the thing this project keeps getting burned by.** A reader quoting
  `4104.3 ±0` is quoting a precision that does not exist.
- `authority=downstream` is a literal instruction: **a refit supersedes this
  line.** Anything holding better calibration must use its own and may ignore
  the card's.
- The firmware must never *use* this number. It logs pulses.

The alternative — leave it off the card — was rejected because it fails the
stranger test, which is the entire point of the format. The risk it creates
(a third home for a constant that already has two) is handled by making the
card the explicitly subordinate one.

## 5. The header is written per **file**, not per boot

The current firmware prints its banner from `setup1()`, so the banner lands in
whatever file is open at boot. **This was verified to fail**, on real data: of
the 19 files on the 2026-10-21 card readback, 18 begin with `# picow-logger`
and one does not —

```
evidence/sd-readback-v030-20261021/card/20261019_122242.CSV:
  # SD state=fail err=sync drop=0
  24519752,0,0.00,0,0.00,0,1
```

— because that file was created by a **mid-session card reinsertion**, long
after `setup1()` ran. A card pulled and returned, or a card that fills and
rolls over, produces a file with no header at all.

So the header is emitted by the SD module **as the first bytes of every file it
opens**, on core 0, before the ring drain resumes. Consequences, all of them
deliberate:

- **A card file and the host's recording of the same session are no longer
  byte-identical.** They differ by exactly one header block per card file. The
  card is the standalone artifact and must carry its own description; the host
  stream is a recording and gets the header once, at boot, over USB.
  `tests/check_card_copy.py` knows about this and skips the block.
- The header is written **directly to the file**, not through the ring, so it
  cannot be displaced by a backlog and cannot be dropped when the ring is full.
- It costs ~950 bytes per file, against ~4 MB/day of rows.

## 6. Two column counts for one contract

A reader will meet both of these and they are not in conflict:

```
card file     ms,vss_total,...            stable 7      (no wall column)
vssrec file   wall,ms,vss_total,...       N_CORE_COLS 8 (wall prepended)
```

`vssrec` prepends `wall` when it records a live stream; the card never has it,
because the Pico does not know the wall clock at row-print time and will not
pretend to. `cardconv.py` reconstructs it from the `file`/`TIME` anchors. The
number differs by exactly one and always will.

## 7. What changes in the rows themselves

`# IGN` becomes the column `ign`, appended last. See
`SEED_firmware_agent.md` task 2 and `NOTES-FOR-REVIEW.md` for the migration and
its compatibility rules. In short: the note roughly doubled the line count
(1,824 notes against 1,825 rows), it was keyed to the row's own `ms`, and every
consumer now accepts note-form **and** column-form so the 64 archived logs keep
replaying byte-identically.

`ign=1` means **ignition on**. The GP5 pin reads *low* for on, and the column
prints the meaning rather than the pin, exactly as `brake` already does.

### Why `ign` is a real column and not derived from `ms_since_ign`

`ms_since_ign` cannot stand in for it. It is `0` both when the key is out and
on the **first report of a key-on**, because the ON edge is latched to that
report's own `ms` and the row then prints `now - ignOnMs` = 0. The ambiguity is
structural, not a tuning problem, so the state gets its own column.

---

## 8. Which statistic the analog columns carry — `log.adc stat=`

`fuel_counts` and `supply_counts` are the **median** of the burst from v0.7.0
and were the **mean** through v0.6.0. The reason is in
`fuel/ADC_INTERFACE_SPEC.md` §7 and `adc_median.h`: the noise on this node is
impulsive at a crest factor of 20-50x, and on that distribution a mean is
dragged off by exactly the spikes a median rejects. In a synthetic test case
(20 deliberately rail-high samples in 2000 at 1850), 1 % of samples at the rail
biases the mean by **+22.5 counts** (~47 mV at the sender) while the median is
unchanged — an illustrative synthetic figure, not a measurement of the mean
bias in the archived vehicle data.

**The column names do not change, and will not.** Renaming `fuel_counts` to
`fuel_median` would redefine every historical row and break every reader that
indexes by position. So the file says what its numbers are, once, in the
header:

```
# log.adc bits=12 vref_v=3.3 burst=2000 stat=median die=rp2040-internal
```

Rules for a reader, and these are the compatibility contract:

1. **`stat=` is additive.** It appeared in v0.7.0. A reader that does not know
   the key ignores it, per rule 4.
2. **Absent `stat=` means `mean`.** Every v0.6.0 file, and every v0.5.0 host
   recording, carries the mean and no key. Do not read "absent" as "unknown" —
   it is `mean`, and that is a statement about a format version that is now
   fixed and will never be written again.
3. **`accord-log/1` is unchanged.** Adding a key to an existing line is what
   rule 2 explicitly permits without a version bump. The format version does
   not advertise the statistic, deliberately: the header does, and a reader
   that needs to know looks at the one line that says it rather than mapping a
   firmware version onto a behaviour with a table it does not have.
4. **Firmware provenance alone was considered and rejected.** `log.unit fw=`
   already distinguishes the builds, but using it would require the reader to
   hold a version-to-statistic mapping — the exact dependency on this
   repository that this format exists to remove. One key is cheaper than a
   lookup table a stranger does not have.

`fuel_lo` and `fuel_hi` are unchanged and still mean the **true extremes of the
burst**. With the engine running they characterise the ignition environment
rather than float noise, as `ADC_INTERFACE_SPEC.md` §7 warns; that is a caveat
about interpretation, not a change of definition.

## 9. Recording a rename — `log.rename`

A file opened before the clock is trusted is named `/BOOT_<ms>.CSV` and renamed
once SNTP lands. Its header is written at creation, so it truthfully says
`name=/BOOT_<ms>.CSV` and `clock=none` — and then the file on disk has a
different, dated name. From v0.7.0 the rename is recorded:

```
# log.rename from=/BOOT_540.CSV to=/20261024_115959.CSV at_ms=6042
```

### Syntax and semantics

| field | meaning |
|---|---|
| `from` | the name the file was **created** with — the same string as `log.file name=` |
| `to` | the name it has **now**, which is the name on disk |
| `at_ms` | `millis()` when the rename completed. Not a wall clock: the Pico's monotonic ms, the same time base as the `ms` column |

- **It is a note in the body, not part of the header.** It necessarily happens
  after rows have been written, so `# log.end` has long gone by. There is still
  exactly **one header per file**, written once at creation, and nothing in it
  is ever rewritten.
- **`log.file` keeps its original meaning**, and that is the point of doing it
  this way. `name=` is the creation name and `clock=none` is a true statement
  about the clock *at creation*. The dated name in `to=` is computed backwards
  from the trusted clock to the open instant — it is a **retrospective**
  timestamp, and `clock=none` is what tells a reader so. Nothing pretends the
  clock was synchronised when the file opened.
- **It appears only when a rename actually happened.** A file opened with a
  trusted clock never carries one, so its presence is itself information.
- **A failed rename writes nothing.** No success is claimed for something that
  did not occur; the file keeps its boot name and the `# SD` note keeps
  reporting which file is live.

### What a reader should do with it

Take `to=` as the file's identity and `log.file opened_ms` as the open instant.
Together they are a complete time anchor with no inference —
`tools/cardconv.py` uses exactly that pair and labels the anchor `log.rename`.
Before this note existed, a boot-named file's dated name had to be recovered
from a later `# SD state=ok file=…` note, which is not guaranteed to be in any
given fragment.

### If the note cannot be written

The rename stands — it is a fact on disk. The note is **not retried**, because
a retry loop over card metadata is a way to turn a cosmetic failure into a
logging failure. Instead `# SD` gains ` rnote=lost`, which travels through the
ring and so reaches the **host** even when the card is the thing failing. The
file then degrades to the v0.6.0 situation: the `# SD` note is the only
in-stream record of the new name.

However, a short or unsynced metadata write **cannot simply be followed by the
next sample drain** (review R1, fixed in v0.7.1 via `card_tail.h`): if the note
stopped before its trailing `\n`, appending the next sample chunk directly
would concatenate that sample onto a `# log.rename` prefix and cause every
downstream reader to discard the sample as part of the comment. Before any
sample chunk may be drained after an incomplete metadata write, `Tail::settle()`
syncs, reads back the file's last byte, appends and syncs a `\n` if needed, and
re-verifies that the file ends in `\n`. If settling fails, the file is closed
via `fail("boundary")` **without advancing `ringTail`**, so the queued samples
are preserved for the next file after the 5 s retry backoff.

### Why it waits for a line boundary

`drain()` writes raw ring chunks capped at 512 bytes and at the ring wrap, and
respects no line boundary — so after an arbitrary pass the file can end
mid-row. Anything written **directly** to the file, as this note is, must
therefore wait until both the file and the ring are at a line boundary and no
orphan fragment is pending (`tail.noteAllowed()`), or it would cut a sample row
in half. The wait is bounded: core 1 pushes only complete lines, so the next
drain that empties the ring leaves the file on a boundary. The header is
written before the first drain and passes through the same `appendMetadata()`
check (`hdr=lost` if incomplete, settled before the first drain).

## Review findings — `pcb` session, 2026-10-24, against a real card

Verified by pulling the card and reading it with `tools/fatread.py` (read-only,
unmounted). Evidence: `evidence/card-v060-20261024/`.

**Confirmed on hardware:**

- `20261024_182457.CSV` opens with the full block, every tag present, `log.end`
  terminating it. 14 columns, no `wall`, `ign` present, **zero `# IGN` notes**.
- The human `# columns:` banner appears immediately after `log.end` — which is
  precisely the collision §2 rule 3 reserved the `log.` namespace to prevent.
  Both forms coexist and are unambiguous.
- The previous file, `20261024_182339.CSV`, is v0.5.0 and carries **no**
  `accord-log` header, so old and new files are distinguishable by the first
  byte of the first line.

### CONFIRMED 2026-10-24 — the mid-session reinsertion case works

**The claim no host test could make is now made on hardware.** The owner pulled
the card with the Pico running and reinserted it. `/20261024_183345.CSV`, the
file that reinsertion created, begins:

```
# accord-log/1
# log.unit chip=E6614C311B3A3231 vehicle=accord-1 fw=0.6.0
...
# log.file name=/20261024_183345.CSV opened_ms=529699 clock=sntp
# log.end
```

Full block, 14 columns, `ign` present, **zero `# IGN` notes**. The 2026-10-21
failure — 18 of 19 files carrying a banner and one not, because it was born of
a reinsertion long after `setup1()` — does not recur. §5 was right and the fix
works.

The SD recovery around it is also now validated under v0.6.0:

```
11:33:40  state=fail err=no-card  drop=182     ring shedding newest, keeping oldest
11:35:56  state=ok   drop=189     wmax_ms=2001 SdFat init timeout, card mid-insertion
```

and the recovered file's **first row is `ms=231005` though the file opened at
`ms=529699`** — the ring's retained backlog draining into the new file, nearly
300 s of rows that existed before the file did. Serial logging never broke.

### FINDING, NARROWED — `log.file` goes stale only for a boot-before-clock file

**This is smaller than first written.** The reinsertion file's `log.file`
matches its own filename exactly, with `clock=sntp`, because no rename
occurred. The defect is confined to one path:

| file | `log.file` says | actual name | correct? |
|---|---|---|---|
| boot, clock absent | `name=/BOOT_540.CSV clock=none` | `20261024_182457.CSV` | **no — renamed later** |
| reinsertion, clock present | `name=/20261024_183345.CSV clock=sntp` | same | yes |

So it is not "the header goes stale" generally. It is: **a file opened before
the clock arrives is named `BOOT_<ms>.CSV`, renamed once the clock lands, and
the header keeps the pre-rename name and the stale `clock=none`.**

That is a rare path — it needs a boot with no cached time — and it is
self-announcing, since a `BOOT_*` name in `log.file` beside a timestamped
filename is unambiguous evidence that a rename happened. A reader can already
infer it. The three options below stand, and option 1 (`# log.rename`) remains
the only one that leaves a card-only reader strictly better off, but the case
for spending a flash on it alone is weaker than it looked.

The header on that file reads:

```
# log.file name=/BOOT_540.CSV opened_ms=540 clock=none
```

but the file on the card is named **`20261024_182457.CSV`**. The sequence was:

```
ms=540    opened as BOOT_540.CSV, no clock -> header written, clock=none
          # TIME unset src=none synced=0   (x2)
18:25:05  SNTP arrives
18:25:07  host clock
          -> file renamed to 20261024_182457.CSV
```

Both `name` and `clock` were correct when written and are wrong by the time the
file is closed. **Nothing breaks**: a reader seeing `clock=none` declines to
trust the filename's timestamp, which is the *conservative* direction, and
`cardconv.py` rebuilds wall time from the `# TIME` notes regardless. But a
stranger's tool would discard a name it could have trusted, and the header
contradicting the filename is exactly the kind of thing that makes a reader
distrust the whole block.

Three ways to resolve it, for the firmware owner to choose:

1. **Emit `# log.rename from=… to=…` when the rename happens.** A distinct tag,
   no ambiguity about which `log.file` wins, and it preserves the history.
2. **Re-emit `# log.file` after the rename**, with "last occurrence wins" added
   to §2. Cheapest in firmware, but it weakens rule 3's "order is not
   significant".
3. **Document it**: `log.file` records open-time state; the authoritative name
   is the file's own, and the authoritative clock evidence is the `# TIME`
   notes. No firmware change.

Option 1 is the only one that leaves a card-only reader strictly better off.

**This is worth settling before the format is frozen**, which is the whole
reason the status line at the top of this document exists.
