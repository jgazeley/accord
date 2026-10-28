#!/usr/bin/env python3
"""Turn a Pico card log into a vssrec-shaped CSV so tripd can build trips from it.

The card holds the same device lines the Pi records, minus the one column the
Pi adds: `wall`. Everything else -- the counters, the Hz, the notes -- is byte
identical (SPEC 8 acceptance item 2, verified at 7,445 lines with zero
mismatches on 2026-10-19). So the card is a complete record of a drive that
nothing can currently read.

This is deliberately a TRANSLATOR and not a second trip builder. Trip
segmentation, the epoch rules, the close rules, the warnings and the packet
shape are hard-won and have a regression suite behind them; a second
implementation would drift from the first and the comparison it exists to
support would stop meaning anything. Convert the card to vssrec's format and
`tripd --once` does the rest, unchanged.

WHERE THE WALL CLOCK COMES FROM
-------------------------------
Card rows carry only `ms`, the Pico's monotonic millisecond counter. An
absolute time has to come from somewhere else, and the file carries two
independent sources:

  1. THE FILE NAME. The Pico opens `/BOOT_<openedMs>.CSV` before SNTP lands and
     renames it to `/<YYYYmmdd>_<HHMMSS>.CSV` -- UTC, back-dated to the instant
     the file was OPENED -- the moment a trusted clock arrives (logger_sd.cpp
     nameFor()). Both names appear in the `# SD state=ok file=...` notes inside
     the file, the early ones carrying the BOOT name and the later ones the
     dated one, which is what makes the pair recoverable at all. Together they
     are an exact (UTC, ms) anchor: openedMs is a real counter value, not an
     estimate.

  2. `# TIME <ISO>Z src=sntp synced=1` notes, printed every 60 s, each one the
     Pico stating its own clock. A note carries no `ms` of its own, but it is
     printed between two data rows, so the following row's `ms` brackets it to
     under a second.

Both are used. One is the anchor, the other is the cross-check, and the
residual between them is reported on every run -- if the rename back-dated
wrongly or the clock was stepped by a re-sync, the two disagree and say so.

The filename anchor is preferred where it exists because it was validated
against the Pi's own NTP-corrected clock: over the 2026-10-19 morning drive it
reproduced `wall` EXACTLY, to the second, for 6,856 consecutive rows. The two
rows it "disagreed" with were the Pi being 5561 s slow before NTP reached it --
which is the whole reason this path is worth having. The Pico knew the time and
the Pi did not.

Both anchors are truncated to whole seconds by the firmware, so a reconstructed
stamp is good to about half a second. Rows are 1 Hz. That is below the
resolution of anything being timestamped.

WHAT IT REFUSES TO DO
---------------------
Invent a date. With no dated filename and no synced TIME note the Pico never
learned the time on that boot, and there is no honest wall clock to be had --
so the conversion stops unless `--no-wall` is passed, which stamps from
midnight and makes the output fit for distance and duration only. A log with a
plausible-looking wrong date is worse than one that admits it has none.

Span a power cycle. The anchor is one (UTC, ms) pair and `ms` restarts at zero
on every boot, so a file whose `ms` goes backwards holds two boots and only the
first could be stamped correctly. tripd would survive it -- feed() turns a
backwards `ms` into a new epoch -- but the timestamps after the seam would be
silently hours out, so it is an error here instead.

USAGE
-----
    tools/cardconv.py CARD.CSV [--out OUT.CSV] [--tz America/Los_Angeles]

The output name defaults to `card_<YYYYmmdd>_<HHMMSS>.csv` built from the LOCAL
time of the first data row, because tripd's file_date() takes a log's date from
its name and will fall back to 1970-01-01 without it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys
from zoneinfo import ZoneInfo

# The width a card file has when it does NOT declare one: the original
# seven-column stage-1 format. Every later firmware appends, and from v0.6.0 the
# file states its own columns in the header, so this is the fallback and not an
# assumption -- see CARD_FORMAT.md rule 6, "log.columns is authoritative for
# this file. Do not assume a width."
CARD_COLUMNS = "ms,vss_total,vss_hz,tach_total,tach_hz,rpm,brake"
# `# log.columns ms,vss_total,...` -- the self-describing header, v0.6.0 and on.
LOG_COLUMNS = re.compile(r"^#\s*log\.columns\s+(\S+)$")
# `# log.file name=/20261024_120000.CSV opened_ms=540 clock=sntp`. The header
# states outright what this tool used to infer by pairing a `BOOT_` SD note
# (for the open instant) with a later dated one (for the wall time). One line,
# no pairing, and `clock=` says whether the name's timestamp may be believed.
LOG_FILE = re.compile(
    r"^#\s*log\.file\s+name=(\S+)\s+opened_ms=(\d+)\s+clock=(\S+)")
# `# log.rename from=/BOOT_540.CSV to=/20261024_120000.CSV at_ms=6042`, v0.7.0
# and on. A file opened before the clock was trusted carries a `BOOT_` name and
# `clock=none` in its header -- truthfully -- and is renamed once SNTP lands.
# This note is how the file records that, so the dated name no longer has to be
# recovered from a later `# SD` note that may not be in the fragment you have.
LOG_RENAME = re.compile(
    r"^#\s*log\.rename\s+from=(\S+)\s+to=(\S+)\s+at_ms=(\d+)")
# Every column this firmware family has ever written, in order. Used only to
# name the columns of a PRE-v0.6.0 card, which declares nothing: the list is
# truncated to the width actually observed in the file. Append only, and never
# reorder -- the first seven are indexed by position downstream.
KNOWN_COLUMNS = CARD_COLUMNS.split(",") + [
    "fuel_counts", "fuel_lo", "fuel_hi", "supply_counts", "die_counts",
    "ms_since_ign", "ign"]


def columns_for(kinds):
    """The column names of this card file: declared if it says, inferred if not.

    A declared list wins outright, because the file knows and we are guessing.
    Without one, the names come from KNOWN_COLUMNS truncated to the widest data
    row present -- which is right for the 7-field stage-1 cards and the
    13-field v0.5.0 cards in evidence/, and refuses to invent a name for a
    width this tool has never seen rather than mislabelling it.
    """
    widest = 0
    for is_note, text, _ms in kinds:
        if is_note is True:
            m = LOG_COLUMNS.match(text)
            if m:
                return m.group(1), "declared"
        elif is_note is False:
            widest = max(widest, len(text.split(",")))
    if widest == 0:
        return CARD_COLUMNS, "empty"
    if widest > len(KNOWN_COLUMNS):
        sys.exit(f"card rows have {widest} fields but this cardconv knows only "
                 f"{len(KNOWN_COLUMNS)} column names and the file declares "
                 f"none. It was written by newer firmware: use a cardconv from "
                 f"the same vintage, or pass the names explicitly.")
    return ",".join(KNOWN_COLUMNS[:widest]), f"inferred from {widest} fields"
SW = "cardconv/0.1"

# `# SD state=ok file=/20261019_150841.CSV bytes=... wmax_ms=... drop=...`
SD_FILE = re.compile(r"^#\s*SD\s+state=\S+\s+file=(\S+)")
BOOT_NAME = re.compile(r"^/?BOOT_(\d+)\.CSV$", re.IGNORECASE)
DATED_NAME = re.compile(r"^/?(\d{8}_\d{6})\.CSV$", re.IGNORECASE)
# Only synced=1 notes carry a real time; `# TIME unset src=none synced=0` is the
# Pico saying it has no idea, and must never be read as an anchor.
TIME_NOTE = re.compile(
    r"^#\s*TIME\s+(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)Z\s+src=\S+\s+synced=1")
IGN_NOTE = re.compile(r"^# IGN ms=(\d+) state=(?:on|off) raw=[01] source=gp5$")

# How far the two anchors may disagree before the conversion is a judgement
# call rather than arithmetic. Each is truncated to a whole second by the
# firmware and the TIME note is bracketed by a 1 Hz row, so about 1.5 s is
# ordinary; the observed residual on the validated drive was 0.06 s.
ANCHOR_TOL_S = 2.0


class Anchor:
    """One (UTC instant, ms) pair, plus how it was obtained."""

    def __init__(self, label, utc, ms, detail):
        self.label, self.utc, self.ms, self.detail = label, utc, ms, detail

    def at(self, ms):
        return self.utc + dt.timedelta(milliseconds=ms - self.ms)

    def __str__(self):
        return (f"{self.label}: {self.utc.isoformat(timespec='milliseconds')}Z "
                f"at ms={self.ms}  ({self.detail})")


def scan(path):
    """One pass over the card file: rows, notes, and the ms that brackets each note.

    A note is stamped with the ms of the row that FOLLOWS it, because that is
    how the firmware prints: the periodic notes go out on the 60 s boundary and
    the next 1 Hz row lands a fraction of a second later. Measured over the 118
    synced TIME notes of the 2026-10-19 drive, the following row sat 0.44 s
    after the note's truncated second in 116 cases -- tight enough that the
    association is not in doubt.
    """
    lines = path.read_text(errors="replace").splitlines()
    kinds = []            # (is_note, text, ms)  ms None for a note
    for line in lines:
        if line.startswith("#"):
            # v0.4.0 IGN observations carry their own sample ms. Preserve it,
            # including the last observation when no further row follows.
            ign = IGN_NOTE.fullmatch(line)
            kinds.append([True, line, int(ign.group(1)) if ign else None])
            continue
        head = line.split(",", 1)[0]
        try:
            kinds.append([False, line, int(head)])
        except ValueError:
            # Not a note and not a numbered row: a torn line from a power cut
            # mid-write. tripd drops short rows anyway; drop it here too so it
            # cannot be mistaken for a note and absorb a wall stamp.
            kinds.append([None, line, None])
    # Walk backwards once and hand every note the next data row's ms.
    nxt = None
    for item in reversed(kinds):
        if item[0] is False:
            nxt = item[2]
        elif item[0] is True and item[2] is None:
            item[2] = nxt
    return kinds


def anchors_from(kinds, name_hint):
    """Every absolute-time anchor the file (and its name) can supply."""
    found, boot_ms, dated = [], None, None
    header = None
    renamed_to = None
    # Which source the dated name came from, for the anchor label and the log.
    dated_from = "filename"
    for is_note, text, ms in kinds:
        if is_note is not True:
            continue
        m = LOG_RENAME.match(text)
        if m and renamed_to is None:
            renamed_to = m.group(2)
        m = LOG_FILE.match(text)
        if m and header is None:
            # First one wins: it describes THIS file, written as its first
            # bytes. Anything later would be a concatenation of two files.
            header = (m.group(1), int(m.group(2)), m.group(3))
        m = SD_FILE.match(text)
        if m:
            base = m.group(1)
            b, d = BOOT_NAME.match(base), DATED_NAME.match(base)
            if b and boot_ms is None:
                boot_ms = int(b.group(1))
            elif d and dated is None:
                dated = d.group(1)
        m = TIME_NOTE.match(text)
        if m and ms is not None:
            # Truncated to a whole second by strftime, so the true instant lies
            # in [u, u+1). Take the midpoint: half a second of error either
            # way, rather than a second in one direction.
            u = dt.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
            found.append(Anchor("time-note", u + dt.timedelta(seconds=0.5), ms,
                                f"{m.group(1)}Z, next row ms={ms}"))
    # The self-describing header beats every inference, because it is the
    # firmware stating the two facts rather than this tool deducing them from
    # two notes that happen to be in the same file. A `BOOT_` name still only
    # supplies the open instant -- `clock=none` is the firmware saying its
    # clock was not trustworthy when it chose that name, so the name carries
    # no wall time and the dated name arrives later, after the rename.
    if header is not None:
        name, opened_ms, clock = header
        boot_ms = opened_ms
        d = DATED_NAME.match(name)
        if d and clock == "sntp":
            dated = d.group(1)
            dated_from = "log.file"
        elif renamed_to is not None:
            # Opened before the clock was trusted and renamed afterwards. The
            # header's opened_ms is still the open instant and the rename note
            # carries the dated name, so the pair is a complete anchor with no
            # inference at all -- which is the whole reason the note exists.
            d = DATED_NAME.match(renamed_to)
            if d:
                dated = d.group(1)
                dated_from = "log.rename"

    # The name on the card beats the name of the host's copy, but a copy that
    # kept the name is still better than nothing.
    if dated is None and name_hint:
        m = DATED_NAME.match(name_hint) or re.search(r"(\d{8}_\d{6})",
                                                     name_hint)
        if m:
            dated = m.group(1)
    file_anchor = None
    if dated is not None and boot_ms is not None:
        u = dt.datetime.strptime(dated, "%Y%m%d_%H%M%S")
        file_anchor = Anchor(
            dated_from, u + dt.timedelta(seconds=0.5), boot_ms,
            f"/{dated}.CSV opened at ms={boot_ms}"
            + (" (declared)" if dated_from.startswith("log.") else " (inferred)"))
    return file_anchor, found


def main():
    ap = argparse.ArgumentParser(
        description="convert a Pico card log to vssrec CSV for tripd")
    ap.add_argument("card", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path,
                    help="output path (default card_<date>_<time>.csv beside the input)")
    ap.add_argument("--tz", default="America/Los_Angeles",
                    help="zone to render `wall` in; the Pico logs UTC and "
                         "vssrec logs local, so one of them has to convert")
    ap.add_argument("--name", help="the file's name ON THE CARD, if the copy "
                                   "lost it and the SD notes do not have it")
    ap.add_argument("--no-wall", action="store_true",
                    help="stamp from midnight when the boot never learned the "
                         "time; distance and duration stay valid, dates do not")
    ap.add_argument("--anchor", metavar="ISO@MS",
                    help="override: UTC instant and the ms it belongs to, "
                         "e.g. 2026-10-19T15:08:41@564")
    a = ap.parse_args()

    kinds = scan(a.card)
    data = [k for k in kinds if k[0] is False]
    if not data:
        sys.exit(f"{a.card}: no data rows")

    # One boot per file. A backwards `ms` means two, and only the first could be
    # stamped from one anchor -- see the module docstring.
    last = None
    for n, (_, _, ms) in enumerate(data):
        if last is not None and ms < last:
            sys.exit(f"{a.card}: ms goes backwards at data row {n} "
                     f"({last} -> {ms}). That is two boots in one file; the "
                     f"anchor only covers one. Split it and convert each part.")
        last = ms

    name_hint = a.name or a.card.name
    file_anchor, time_anchors = anchors_from(kinds, name_hint)

    if a.anchor:
        iso, _, msv = a.anchor.partition("@")
        chosen = Anchor("override", dt.datetime.fromisoformat(iso.rstrip("Z")),
                        int(msv), "--anchor")
        others = ([file_anchor] if file_anchor else []) + time_anchors[-1:]
    elif file_anchor is not None:
        chosen, others = file_anchor, time_anchors
    elif time_anchors:
        # The LAST note, not the first: it is the most corrected reading the
        # file holds, which is the same rule tripd uses to back-date a trip.
        chosen, others = time_anchors[-1], time_anchors[:-1]
    elif a.no_wall:
        chosen, others = Anchor("none", dt.datetime(1970, 1, 1), data[0][2],
                                "--no-wall: stamped from midnight"), []
    else:
        sys.exit(f"{a.card}: no absolute time anchor. The file has no dated "
                 f"name and no `# TIME ... synced=1` note, so the Pico never "
                 f"learned the time on this boot. Pass --anchor ISO@MS if you "
                 f"know it, or --no-wall to accept ms-only stamps.")

    print(f"anchor  {chosen}")
    # Cross-check. Every other anchor is an independent statement about the same
    # clock, so project each onto the chosen anchor's ms and compare.
    # The MEDIAN is what the warning is gated on, not the extreme. A TIME note
    # whose following row arrived a tick late is bracketed a second wide and
    # shows up as a lone outlier -- 2 of the 118 notes on the validated drive
    # did exactly that. A clock that was really stepped moves the whole
    # population, so the median is the statistic that notices it and the
    # extremes are the ones that do not.
    resid = sorted((other.at(chosen.ms) - chosen.utc).total_seconds()
                   for other in others)
    if resid:
        mid = resid[len(resid) // 2]
        worst = max(resid[0], resid[-1], key=abs)
        print(f"check   {len(resid)} other anchor(s) [{others[0].label}], "
              f"median residual {mid:+.3f}s, worst {worst:+.3f}s")
        if abs(mid) > ANCHOR_TOL_S:
            print(f"WARNING: anchors disagree by {mid:+.3f}s at the median "
                  f"(> {ANCHOR_TOL_S}s). The clock was stepped mid-file or the "
                  f"rename back-dated wrongly; the stamps are only as good as "
                  f"the one chosen.", file=sys.stderr)
    else:
        mid = worst = 0.0

    zone = ZoneInfo(a.tz) if chosen.label != "none" else None

    def wall(ms):
        at = chosen.at(ms)
        if zone is not None:
            at = at.replace(tzinfo=dt.timezone.utc).astimezone(zone)
        # vssrec writes datetime.now().strftime("%H:%M:%S") -- a TRUNCATED
        # instant, not a rounded one. Matching that is what made the
        # reconstruction land on the Pi's own stamps to the second.
        return at.strftime("%H:%M:%S")

    first_local = chosen.at(data[0][2])
    if zone is not None:
        first_local = first_local.replace(
            tzinfo=dt.timezone.utc).astimezone(zone)
    out = a.out or a.card.parent / (
        "card_" + first_local.strftime("%Y%m%d_%H%M%S") + ".csv")

    card_columns, how = columns_for(kinds)
    print(f"columns {card_columns} ({how})")

    kept = notes = torn = 0
    with out.open("w") as fh:
        fh.write("wall," + card_columns + "\n")
        # Provenance, written as `# HOST:` note rows rather than bare comments.
        # That one prefix is what makes the output work with both existing
        # tools instead of one: tripd reads a `<wall>,#...` row as a note and
        # ignores it, and check_card_copy.py drops `# HOST:` lines by name
        # because they are the recorder's own annotations that the device never
        # emitted -- which is exactly what these are. A bare `#` line would
        # instead come back from csv.reader as an empty device line and break
        # the byte comparison this file should still be able to pass.
        first_wall = wall(data[0][2])
        for note in (f"# HOST: {SW} from {a.card.name}",
                     f"# HOST: anchor {chosen.label} "
                     f"{chosen.utc.isoformat(timespec='milliseconds')}Z "
                     f"at ms={chosen.ms} -- {chosen.detail}",
                     f"# HOST: wall rendered in {a.tz}"
                     + (f" / cross-checked against {len(resid)} anchor(s): "
                        f"median {mid:+.3f}s worst {worst:+.3f}s"
                        if resid else "")):
            fh.write(f"{first_wall},{note}\n")
        for is_note, text, ms in kinds:
            if is_note is None:
                torn += 1
                continue
            if ms is None:
                # A note trailing the last data row: nothing follows to
                # bracket it, and a note tripd cannot stamp it does not need.
                # (Notes ahead of the first row are fine -- the backwards walk
                # hands them that row's ms.)
                notes += 1
                continue
            fh.write(f"{wall(ms)},{text}\n")
            if is_note:
                notes += 1
            else:
                kept += 1

    span = (chosen.at(data[-1][2]) - chosen.at(data[0][2])).total_seconds()
    print(f"wrote   {out}")
    print(f"        {kept} rows, {notes} notes"
          + (f", {torn} torn line(s) dropped" if torn else "")
          + f"  spanning {span/3600:.2f} h")
    print(f"        tripd --once {out}")


if __name__ == "__main__":
    main()
