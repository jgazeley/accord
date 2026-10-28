# KiCad copy verification — October 27, 2026

Codex logger-wifi-piless, session 01a17526-034c-78f1-9d09-24c3b88c3dc7.
Resume: codex resume 01a17526-034c-78f1-9d09-24c3b88c3dc7.

KiCad CLI 9.0.2 loaded and exported the copied schematic and PCB successfully.
The original project, schematic, PCB, footprints and copied assets retain their
pre-check hashes. The original repository remains untouched.

Checks used a temporary KiCad configuration with installed standard symbol and
footprint library tables; no global user configuration was changed. For the
baseline comparison, original project files were copied to a temporary directory.

| Check | Copy | Original |
|---|---|---|
| Schematic ERC | 0 errors, 2 warnings | 0 errors, 4 warnings |
| PCB DRC | 0 errors, 3 warnings | Identical |
| Unconnected PCB items | 0 | 0 |
| Schematic/PCB parity | 8 warnings | Identical |

The two remaining ERC warnings concern embedded Pico W and MAX3485 symbols
differing from installed standard library definitions. The new local Custom
library resolves the original two missing-library warnings.

Board warnings: two J1 silkscreen segments clipped by the board edge, plus the
Pico footprint differing from its installed library definition.

Parity warnings: J2 missing from the PCB, R14/R15 values differing from the
schematic, and H1–H5 present only on the PCB. These were already in the original;
no electrical or layout changes were made to resolve them.

The standard 3D-model directory /usr/share/kicad/3dmodels is absent. Standard
model resolution and 3D appearance remain unverified. This is a CLI load/export
and rule-check validation, not a GUI interaction or fabrication approval.

Reports: copy-erc.json, copy-drc.json, original-erc.json, original-drc.json.
Exports: schematic/hondaPico.svg and pcb-top.svg.
Commands and console output are recorded alongside this summary. Rule-check
commands did not use --exit-code-violations; results above come from the JSON
reports, not from treating a zero process exit code as a clean design.
