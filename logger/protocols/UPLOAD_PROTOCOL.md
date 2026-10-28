# `accord-upload/1` — the Pico to bridge protocol

**Status: specified; reference receiver implemented and tested; NO Pico HTTP
client exists.** Receiver tests do not demonstrate device upload, and nothing
in this document is deployed. Bridge deployment is on owner hold pending
database placement and migration planning. See §8, and
`../../archive/root-history-2026-10-27/STATUS_REVIEW_2026-10-24.md`.

Implements `../../ARCHITECTURE.md` ("the Pico uploads raw rows over WiFi") and
the third task of `SEED_firmware_agent.md`. The reference receiver is
`tools/upload_receiver.py` and its test is `tests/check_upload.py`.

---

## 1. The constraint everything else bends around

> The logger's first duty is to log. The SD card is the backstop and
> store-and-forward already works, so an interrupted or failed upload must cost
> nothing.

So the protocol is designed to be **abandonable at any instant**. There is no
session, no transaction, no multi-step handshake to unwind, and no state on the
Pico that a reboot could lose. Pull the power mid-upload and the next attempt
starts from exactly where the receiver actually is, because the receiver is
asked rather than remembered.

## 2. Why HTTP, and not MQTT

The owner's four existing bridges are MQTT-centric and the seed is explicit
that this is not a reason on its own. It is not the right transport here, and
the reason is specific:

**The resume requirement is a byte-offset requirement, and HTTP already has
byte offsets.** A card file is an append-only byte stream with a stable name.
"What have you accepted?" is therefore "how many bytes of this name do you
have?", and "here is more" is a POST with a starting offset. That is two
endpoints and no invented framing.

MQTT would mean building a file-transfer protocol inside a message bus:
chunking, per-chunk acknowledgement, deduplication and reassembly, all on top
of a transport whose delivery guarantees are per-message and whose retained
semantics are wrong for a log. It also means another library on the Pico.
Every one of those pieces is something HTTP gives for free or does not need.

| option | why not |
|---|---|
| MQTT | bulk transfer, not events; resume must be reinvented on top; extra client library |
| raw TCP | would need its own framing, length prefixes and error codes — i.e. a worse HTTP |
| TFTP/FTP | no partial-file resume that survives a reboot cleanly; FTP needs two sockets |
| syslog/UDP | no acknowledgement at all, so not resumable even in principle |

**And MQTT is not displaced to a later hop either.** An earlier version of this
section said it "keeps its place one hop later — the bridge publishes to
mosquitto like its siblings", citing ARCHITECTURE.md. That document was
corrected on 2026-10-24 (commit 341fb42) and now says the opposite, in terms
worth quoting because they are the same mistake this section was written to
avoid:

> **MQTT is not in the data path and must not become a dependency of it.** Raw
> rows are bulk transfer; trips are batch processing; the database is SQL; the
> dashboard is HTTP. None of that wants a broker.

So: the Pico→bridge hop is a file transfer, the bridge's job ends at the
database, and publishing *events* to mosquitto is an optional extra on the
side. The bridge is packaged and hardened like its four siblings; it does not
have to talk like them.

## 3. The two endpoints

Both take `unit` (the RP2040 chip id, the same string in the card header's
`log.unit chip=`) and `file` (the card file name, without its leading `/`).

```
GET /v1/offset?unit=<chip>&file=<name>
    200 {"file": "<name>", "bytes": <n>}       n = 0 if never seen

POST /v1/append?unit=<chip>&file=<name>&from=<n>
    Content-Type: application/octet-stream
    body: raw bytes of the file starting at byte n
    200 {"file": "<name>", "bytes": <new total>}
    409 {"file": "<name>", "bytes": <actual>}  from != actual; retry from there
```

That is the whole protocol. `GET /v1/offset` is strictly an optimisation — a
client that only ever POSTs `from=0` and follows the 409 is correct, just
wasteful, which is a good property for a protocol to have.

### Rules

1. **Append only, offset addressed.** `from` must equal the number of bytes the
   receiver already holds. If it does not, the receiver changes nothing and
   answers 409 with its real size. A disagreement therefore **self-corrects on
   the next attempt instead of corrupting the file** — no range can be written
   twice and no gap can be left.
2. **Idempotent.** Re-sending a chunk whose `from` is now stale is a 409 and a
   no-op, so a lost response costs one wasted chunk and nothing else.
3. **The receiver is the source of truth.** The Pico persists *nothing* about
   upload progress — not in RAM across a reboot, not on the card. This is what
   makes the "must know what has been accepted" requirement safe rather than a
   second thing that can be wrong.
4. **The Pico never deletes or rewrites a card file.** Upload is a copy. The
   card remains the primary artifact (ARCHITECTURE.md) whatever the network
   does.
5. **Raw rows, byte for byte.** The body is the card file's bytes, including
   the `# log.*` header block and every `#` note. No parsing, no filtering, no
   trip building. The bridge runs `tripd` unchanged, so what it receives has to
   be what `cardconv.py` would have produced from the card — and the simplest
   way to guarantee that is to send the file.
6. **Never upload a file whose name still begins with `BOOT_`.** A file opened
   before the first SNTP reply is renamed once the clock arrives
   (`logger_sd.cpp`), and uploading under the provisional name would leave the
   receiver holding the same data under two names. The rename lands within
   seconds; the card loses nothing by waiting.
7. **Oldest first.** A complete older file is worth more than a partial newer
   one, and finishing files keeps the number of partially-held files at one.

## 4. Authentication

A shared bearer token, sent as `Authorization: Bearer <API_TOKEN>`, where
`API_TOKEN` comes from `secrets.h` — which already carries one (SPEC §4.7).
**It is never printed, never logged and never appears in a note**, on either
side; the receiver logs `unit`, `file` and byte counts only.

No TLS. This is a LAN-only service on the owner's own network and the Pico's
TLS would cost flash, RAM and handshake latency for a log of vehicle speed
pulses. **What that costs, stated plainly:** anyone already on the network can
read the rows in flight and, with the token, write to the bridge. The token
stops casual mistakes, not an attacker on the LAN. If the bridge is ever
exposed beyond the LAN this decision has to be revisited, and the protocol does
not change when it is — only the scheme.

## 5. How the firmware will drive it, without touching the report

The same structure the card already uses, for the same reason:

- **Core 0 only.** Core 1 owns the counters, the 1 Hz report and the serial
  port, and contains no network call — a property `tests/check_counter.py`
  asserts for SdFat and SPI today and must be extended to the upload client.
- **One bounded step per `loop()` pass.** Connect, request, send one chunk,
  read one response — never a loop that waits for a whole file.
- **A hard chunk size** (4 KiB proposed), so a single POST cannot monopolise
  core 0 and a failure discards at most that much work.
- **Reading the card to upload is card work** and shares the SPI bus with
  writing it. Writing wins: the uploader must skip a pass rather than delay a
  drain, and `wmax_ms` must keep being the measure of the worst blocking card
  call.
- **Failure is silence.** No retry storm, no backoff tuning: try again on the
  next interval. A missing bridge is the normal state of a car that is not at
  home.

## 6. What the bridge must do with what it receives

Nothing clever, and this is the point. It appends bytes to a file per
`(unit, file)`, and that file is byte-identical to the card's. Then it runs the
existing pipeline: `cardconv.py` to add the `wall` column, `tripd` unchanged,
then `accord_maintenance.db`. **That is the whole data path** — no broker in
it. **One trip builder, two delivery paths, no drift.**

A received file is therefore interchangeable with a card pulled by hand. That
equivalence is worth testing on the bridge side: the same file through both
paths must produce the same trips, which is exactly what
`tests/check_cardconv.py` already asserts for the card path.

## 7. Deliberately not in this protocol

- **No time sync.** SNTP already works and `@`-framed host time (rule 4.10)
  already exists. Two mechanisms for one job is how the clock bugs happened.
- **No commands, no configuration, no firmware update.** The upload path is
  one-directional on purpose: the only thing the bridge can cause is a 409.
- **No deletion or rotation.** If the card fills, that is a card-management
  decision for the owner, not something a network service gets to do.
- **No trips, no aggregates, no calibration.** All downstream.

## 7a. Disposition on `log.closed` / explicit completion

Requested by `bridge/DESIGN.md` §5 and firmware finding 2, which proposes
`# log.closed rows=<n> bytes=<n>` written by the SD module "when it closes a
file — on rotation, on reinsertion, on rollover". **Recommend against, as
proposed.** This is a disposition, not an implementation; nothing here is built.

### What the firmware can actually know

Checked against `logger_sd.cpp` rather than reasoned from the design:

| how a card file stops being written | can the firmware write a closing note? |
|---|---|
| **ignition off / power removed** — how essentially every file in this car ends | **No.** No warning, no shutdown hook, no power latch |
| **card pulled** | **No.** The card is gone; that is *why* the file ended |
| **write or sync failure** | **No.** Same reason |
| **card reinserted** (a new file opens) | Not into the old file — it was closed while the card was absent |
| **rotation / rollover** | **Does not exist.** One file per card-open; there is no size limit and no rotation |
| **clean shutdown** | **Does not exist** |

The decisive detail: **the only `file.close()` in the module is inside
`fail()`** (`logger_sd.cpp:94`). Files are closed exclusively on the failure
path, which is by definition the path on which the card cannot be written. The
"normal closure" the proposal is built around has no code path at all.

So `log.closed` would be absent from very nearly every real file. That is worse
than no marker: a reader would have to treat its absence as meaningless, which
is exactly today's position, while the format carries a new obligation and the
bridge still needs its manual interlock for every file. It converts the
*uncommon* case, not the common one.

### A counter-proposal that is knowable, and verifiable

Put the fact in the **next** file instead of the last one — a file the firmware
can still write:

```
# log.prev name=/20261024_120000.CSV bytes=1483264
```

in the header block of the file that opens next. Why this is better:

- **It is knowable at the moment it is written.** `fileBytes` for the file just
  abandoned is already in memory within a boot.
- **It is verifiable rather than asserted.** The bridge compares it against the
  bytes it holds for that name and *proves* completeness, instead of an
  operator stating it. `bridgectl.py complete` stays for the cases nothing can
  prove.
- **It rides the existing header**, so it costs one line, needs no new wire
  message, and is ignorable by rule 4.

Its limit, stated rather than hidden: **across a reboot the firmware does not
know the previous file.** Ignition-off is exactly that case, so the common path
would need the module to scan the card directory at open time and pick the
newest file — an *inference* about which file preceded, of the kind
`bridge/DESIGN.md` §5 rightly refuses. Either that inference is marked as one
in the note, or the tag is simply omitted after a reboot and the operator
command covers it.

### What this needs from the bridge owner before anything is built

1. Whether verifiable-size-in-the-next-file is worth having when it covers the
   within-boot cases (reinsertion, future rollover) but not ignition-off.
2. If so, whether a reboot should emit a marked inference or nothing.
3. Whether a `POST /v1/complete?unit=&file=&bytes=` is wanted in addition. It
   fits this protocol's shape and the interlock already exists — but note it
   could only be sent by a client that *has* a reason to believe the file is
   done, and per the table above the firmware will not have one.
4. Agreement on the standing rule, which this document already states as rule 7
   and which nothing above changes: **a quiet upload, or a newer filename, is
   never proof that an earlier file is complete.**

## 8. Why no firmware implements this yet

Two reasons, both about sequencing rather than difficulty.

**The format has to be signed off first.** The upload carries the card's bytes
verbatim, so `CARD_FORMAT.md` is this protocol's payload definition. Building
the client before the format is agreed means building it against a moving
target.

**It cannot be validated from here.** The board is in the car and
`~/.local/bin/pico-flash` runs on the car Pi; BOOTSEL cycles are cumulative and
have disabled that host's root port before. So socket code should go on the
board in the *same* flash as the header and the `ign` column, once, after
review — not in a separate iteration. What can be checked without hardware has
been: the receiver, the offset/409 state machine and the resume behaviour all
have tests that run on this host (`tests/check_upload.py`).
