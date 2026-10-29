# Logger power circuit candidate

Selective export of the existing `9527a14` engineering candidate from
`jgazeley/accord-logger`. It proposes an input-switched onboard supply, a
1800-second firmware hold and a separate nominal 2048-second cutoff.
The circuit has not been assembled or accepted; component, protection,
current-budget, isolation and firmware-interface work remains.

## LRA-01 continuation — October 28, 2026

The electrical lead's [interface contract candidate](INTERFACE_CONTRACT.md)
defines qualified IGN, GP6 HOLD, startup/shutdown timing, reset/USB behavior,
current allocations and bounded component changes. The [firmware review](FIRMWARE_REVIEW.md)
permits isolated implementation with explicit gates; **engineering/bench closure
remains open**. This is not an accepted implementation.
Read its [integration handoff](LRA01_HANDOFF.md) for claim attribution,
validation, unresolved issues and required reviewer dispositions.

The [LRA-02 component review](COMPONENT_MARGIN_CLOSURE.md), [BOM delta](BOM_DELTA.csv)
and [return handoff](LRA02_HANDOFF.md) add conditional part proposals and expose
remaining current-budget gaps. The delta is not an accepted consolidated BOM.

## Read the existing design in revision order

1. [LRA-12](../../../coordination/handoffs/LRA-12_LAYOUT_ELECTRICAL_CLOSURE.md)
   is the current electrical-completion packet; live ownership is in the
   [tracker](../../../coordination/PROJECT_MILESTONES.md). Read the
   [interface contract](INTERFACE_CONTRACT.md) and
   [component review](COMPONENT_MARGIN_CLOSURE.md) for the later decisions.
   The LRA-05 firmware candidate is integrated with manual power as default;
   physical qualification remains open.
2. [Cutoff margin review](CUTOFF_MARGIN_REVIEW.md) controls its listed changes:
   clock, reset/IGN, always-on supply and gate/current calculations.
3. [Maximum-on cutoff](MAX_ON_CUTOFF.md) and [incremental BOM](MAX_ON_BOM.csv)
   contain the latch/counter connections and revised components.
4. [Base design](DESIGN.md) and [base BOM](BOM.csv) supply the underlying
   power stage. Apply the later replacements; these are not a merged BOM.
5. [Interface handoff](INTERFACE_HANDOFF.md) and
   [prototype test plan](PROTOTYPE_TEST_PLAN.md) contain proposed integration
   and physical checks, subject to the later margin-review changes.
6. [Historical continuation](NEXT_SESSION.md), especially its final section,
   and [earlier review](REVIEW_2026-10-25.md) preserve engineering history.

All eleven imported files retain their original bytes. Old `logger-power/`,
firmware paths, commands, ownership, stock and deployment statements describe
October 25 history. They do not redirect active work to the old repository.
Use LRA-12 for the current continuation and the tracker for its assignment.
The old README and full inventory are not exported; historical references to
those files do not create prerequisites. Original engineering attribution,
source commits and hashes are in [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)
and the [export review](../../../coordination/reviews/POWER_EXPORT_9527A14_2026-10-28.md).

## Run the existing checks

From the `accord` repository root:

```sh
python3 -B logger/hardware/power/check_max_on_logic.py
python3 -B logger/hardware/power/check_cutoff_margins.py
python3 -B logger/hardware/power/check_interface_contract.py
python3 -B logger/hardware/power/check_component_margins.py
```

These check settled logic and arithmetic under stated assumptions. They do not
establish component limits, circuit behavior or physical acceptance. Read the
margin review before applying the original prototype plan: shared-qualified IGN
supersedes raw-GP5/100 ms rules, and the original 41.4 V clamp is incompatible
with the selected always-on regulator's input boundary.
The new contract check adds state/generation and timing-budget examples;
it does not test the current logger firmware or qualify hardware.

Circuit connection definitions and BOMs are original hardware design source
under [CERN-OHL-P-2.0](LICENSE). Narrative documentation and verification scripts
follow the repository's Apache-2.0 license. See [NOTICE](NOTICE) and
[LICENSING.md](../../../LICENSING.md); third-party datasheets are linked, not bundled.
