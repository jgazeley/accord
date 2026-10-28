# Licensing and credit

Accord is an open-source project by **Jayson Gazeley (jgazeley)**.
You may use, modify and redistribute the original work, including commercially,
subject to the applicable license below.

| Material | License |
|---|---|
| Original firmware, tools, tests and documentation | [Apache License 2.0](LICENSE) |
| Original hardware design source under `keyless/hardware/` and generated representations of that design | [CERN Open Hardware Licence 2 — Permissive](keyless/hardware/LICENSE) |
| Third-party material | Its own applicable terms, as described below |

The hardware license covers the original schematic, PCB, custom design
libraries and project configuration. It does not relicense third-party
library content or the separately excluded model below. Hardware design
exports under `keyless/validation/` follow the design's licensing; validation
reports and scripts follow the software/documentation license.

## Credit when sharing

Keep the applicable license, copyright and attribution notices when distributing
this work or derivatives. Apache 2.0 section 4 describes the requirements for
license copies, retained notices, changed-file notices and the attribution in
[NOTICE](NOTICE). CERN-OHL-P-2.0 sections 3 and 4 describe the requirements for
design notices, modification notices and access to notices for product recipients.
The full license texts control the exact requirements.

Suggested credit:

> Based on Accord by Jayson Gazeley — https://github.com/jgazeley/accord

A visible project link in a README, product documentation or showcase is
appreciated. This request does not add an advertising requirement to the
licenses or require public credit merely for private use. Neither license
requires derivatives to be published under the same license.

## Third-party material

The hardware incorporates KiCad standard library symbols and footprints.
Those libraries use CC-BY-SA 4.0 with KiCad's design exception, which permits
projects using the library data to use their own license. Separately
redistributing a library collection has different requirements. See the
[official KiCad library terms](https://www.kicad.org/libraries/license/).
The full standard libraries and standard 3D models are installed separately.

The locally retained `keyless/hardware/3d/039301160.stp` has no established
redistribution license in the available records. It is unused by the current
PCB, excluded by `.gitignore`, and is not covered by the project's license
grant. Do not include it in a public source archive until its terms are resolved.

Arduino-Pico, SdFat and other build dependencies retain their upstream licenses.
They are not relicensed by this repository. Distributing compiled firmware
requires observing the licenses of the dependencies included in that build.
