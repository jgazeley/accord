LRA-04 Communications Comparison (browser/LLM review of public main as of inspection, October 29 2026)

Inspected revision: current public main of jgazeley/accord (packet dated October 29 2026 by pcb-manager; no write/push performed). Session identifiers unavailable. No bench tests, commits, or vehicle connections executed. Primary sources cited below. Provisional power constraints from reviewed LRA-01/02 used as stated; final schematic freeze requires later coordination with LRA-03 and electrical review. Unresolved limits called out explicitly.

Provisional Power / Interface Constraints Applied
Whole-system parked targets: ≤100 µA (20–30 °C) / ≤500 µA (85 °C) after cutoff, IGN off, USB absent.
Independently energized interfaces aggregate allocation: 10/25 µA; tentative split 8/20 µA for five vehicle inputs + 2/5 µA for future bus/service. These are unproved allocations (not measured capacity). Do not silently enlarge.
Switched rails preferred; do not assign continuous bus load to always-on A5 or assume undocumented headroom. Separate active, shutdown, and externally-supplied (board-off) currents.
Preserve logger resources: GP2/3 capture, GP4 brake, GP5 IGN, GP26/27 ADC, SD SPI0 (GP16–19). Reserve GP6 for HOLD (GP7 not alternate). GP8/9 suggestions only pending LRA-03 agreement.
Firmware: core 0 SD/Wi-Fi, core 1 capture + power supervisor; qualified mode claims hardware alarm + watchdog. Account for bus IRQ/peripheral/PIO/DMA interactions and possible masking; no automatic spare-alarm assumption.
Isolation/protection (R02 vehicle protection, R05 isolation) remain open; demonstrate powered-off bus/GPIO behavior (external power/debug/connector paths). Unpopulated/disconnected fallback permissible. No completed vehicle interface claimed.
Existing keyless uses RS-485 (MAX3485 on 3V3, tied DE//RE with 10 kΩ default-listen pulldown, selectable 120 Ω termination, dedicated bus ground); firmware GP8 TX / GP9 RX / GP10 direction / 115200 baud. Logger allocations proposed separately. Tested 5 V module/dividers remain interim option (do not reopen feasibility). No factory CAN connection assumed; do not promise keyless interoperability.

Key unresolved limits (apply to all options): off-state leakage/measurements unclosed; exact bus protection/isolation; pin/connector freeze with LRA-03; Arduino-Pico IRQ/peripheral interactions with power supervisor and SD; mechanical/return-current for any header; inventory incomplete.

REV_A_OPTIONS.md (proposed contents)

REV_A_OPTIONS — RS-485 / CAN / Daughterboard Comparison

Date: 2026-10-29 (browser review) 
Starting revision: public main (LRA-04 packet date). 
Provisional requirements: LRA-01/02 power interface and margins (100/500 µA whole-system; 10/25 µA interfaces with 2/5 µA tentative bus/service).

Summary Comparison

| Option | GPIO / Peripheral | Active Current (typ/approx) | Off-state / Shutdown | Arduino-Pico Support | Space / BOM | Isolation / Protection Notes | Recommendation |
|--------|-------------------|-----------------------------|----------------------|----------------------|-------------|------------------------------|----------------|
| Onboard RS-485 (MAX3485-class 3.3 V transceiver) | UART TX/RX + 1 DE//RE (or tied + 1 GPIO). Possible GP8/9 + GP10-style. | 0.5–1 mA receiver; higher when driving | Shutdown 2 nA typ (DE low + /RE high); VCC=0 leakage limited per datasheet | Native UART; SoftwareSerial or PIO if needed; direction control simple | Low (SO-8 + passives, 120 Ω term, bias) | Match keyless: 3V3 switched rail, bus ground return, selectable term, bias. External bus when board off needs isolation review | Primary |
| Onboard CAN (MCP2515 + 3.3 V transceiver, e.g. SIT65HVD230 or equiv) | SPI (CS + SCK/MOSI/MISO) + INT. Avoid SPI0 conflict with SD; use SPI1. Pins must not collide with reserved set | MCP2515 ~5–10 mA active; transceiver similar | Power-off leakage higher; many modules 5 V transceiver; continuous clock/oscillator risk | Libraries exist (pico-mcp2515, ACAN2515, Adafruit); SPI + IRQ | Higher (controller + transceiver + crystal/osc + term) | No assumed vehicle CAN; isolation open; 5 V modules common → level/power issues | Secondary / conditional |
| Daughterboard / host header (neither bus populated) | Header: UART or SPI + DE/INT + power/GND/return + optional enable | Minimal (unpopulated) | Zero continuous if unpowered pins floating/isolated | Host-side; firmware later | Lowest on main board; mechanical allowance needed | Unpopulated fallback explicitly allowed; define pinout, orientation, return current | Fallback |

Detailed Option Analysis

1. Onboard RS-485
Controller vs transceiver:** Transceiver only (MAX3485 or equivalent 3.3 V, half-duplex). Keyless precedent: MAX3485 on 3V3, tied DE//RE, 10 kΩ default-listen, selectable 120 Ω, dedicated ground return. Packet notes schematic/PCB mismatch on R14/R15 bias — reconcile before adoption.
GPIO/peripheral:** 2 UART pins + 1 direction (or tied). Suggest GP8 TX, GP9 RX, GP10 DE//RE (pending LRA-03). UART hardware preferred; PIO/DMA possible if contended. No SPI conflict.
Current/voltage:** Power from switched Pico 3V3. Active 0.95–1.1 mA no-load (datasheet). Shutdown mode (DE=0, /RE=1): 0.002 µA typ / 1 µA max. When VCC=0, A/B input current limited (datasheet examples 1 mA max at 12 V / –0.8 mA at –7 V — must fit 2/5 µA allocation or request tradeoff; external isolation preferred).
Off-state / board-off:** Shutdown + switched rail preferred. Demonstrate no backfeed; unpopulated or series isolation acceptable. Fail-safe receiver (open → high).
Termination/bias/protection:** Selectable 120 Ω, bias network (reconcile keyless values), bus ground. Protection deferred to electrical review (TVS/clamps open).
Arduino-Pico:** Hardware UART, direction pin control. Baud 115200 proven on keyless. Core 1 or IRQ considerations with power supervisor — test later.
Primary sources:** Analog Devices/Maxim MAX3485 datasheet (3.3 V, 10 Mbps, 2 nA shutdown, –7 V to +12 V CM, up to 32 nodes); keyless hondaPico schematic notes and firmware assignments; LRA-04 packet; INTERFACE_CONTRACT.md / COMPONENT_MARGIN_CLOSURE.md allocations.

2. Onboard CAN (controller + transceiver)
Controller vs transceiver:** Separate (MCP2515 SPI controller + 3.3 V-capable transceiver preferred over common 5 V TJA1050 modules). No full stack required for prototype.
GPIO/peripheral:** SPI1 (avoid SPI0/SD conflict): CS, SCK, MOSI, MISO + INT. Example libraries use various pins; must free from GP2–6,16–19,26–27. Crystal/oscillator adds pins or shared. IRQ + possible DMA.
Current/voltage:** MCP2515 operable 2.7–5.5 V; many modules require 5 V transceiver → switched 5 V or level shift + continuous draw risk. Active currents typically several mA; off-state often higher than RS-485 shutdown. Oscillator residual current concern.
Off-state:** Harder to meet 2/5 µA without power gating + isolation. Many commercial modules not optimized for µA parked. Unpopulated option safer.
Arduino-Pico:** Supported (pico-mcp2515, ACAN2515, Adafruit MCP2515). SPI mode 0/1; interrupt driven. Interaction with watchdog/alarm/power supervisor untested in this context.
Primary sources:** Microchip MCP2515 datasheet; community Pico libraries and wiring notes (SPI + INT); Adafruit PiCowbell examples; LRA-04 packet (no factory CAN assumed).

3. Daughterboard / Header (neither bus on main)
Minimal main-board footprint: defined header with UART (TX/RX/DE) and/or SPI (CS/SCK/MOSI/MISO/INT) + switched 3V3/5 V + GND + bus return + optional enable/shutdown. Mechanical clearance and orientation required. Return-current plan mandatory.
Zero continuous load when unpopulated. Allows later RS-485 or CAN population or external module.
Firmware deferred; pinout must be frozen with LRA-03.
Explicitly permitted by packet as valid alternative.

Recommendation and Fallback
Primary recommendation:** Onboard RS-485 (MAX3485-class on switched 3V3) — lowest GPIO, proven keyless precedent, excellent shutdown current, simple UART, best fit to 2/5 µA provisional allocation with proper enable. 
Fallback:** Unpopulated daughterboard/header with defined pinout (UART + direction + power/GND/return). Allows either bus later without main-board commitment. 
CAN:** Conditional only; higher resource and power risk; no vehicle bus assumption. Prefer only if specific logger-to-logger or future need emerges and isolation/power measured.

Unresolved (do not freeze schematic until closed): 
Measured off-state bus leakage under vehicle voltages (must fit or trade 2/5 µA). 
Isolation/protection (R02/R05 open). 
Exact GP8/9/10 (or alternatives) reservation with LRA-03. 
Bias/termination reconciliation from keyless. 
IRQ/PIO/DMA interaction with power supervisor, SD, and qualified alarm/watchdog. 
Mechanical header details if fallback chosen. 

Named follow-up tests: off-state current with bus energized/open; direction default; UART loopback; power-supervisor coexistence; decay with bus attached.

INTERFACE_PROPOSAL.md (proposed contents)

INTERFACE_PROPOSAL — Bounded Rev A Communications Provisioning

Date: 2026-10-29 
Status: Proposal only; no selected bus or acceptance claimed. Coordinate pin/connector freeze with LRA-03; electrical review required before schematic freeze.

Recommended Interface (Primary: Onboard RS-485)
Device:** MAX3485 or pin-compatible 3.3 V half-duplex transceiver (SO-8). Powered from switched Pico 3V3. 
Pins (proposed, pending LRA-03):** GP8 TX, GP9 RX, GP10 DE//RE (tied with 10 kΩ pulldown default-listen, matching keyless style). Hardware UART. 
Bus connector:** Dedicated 3-wire (A, B, GND return) or 4-wire; selectable 120 Ω termination; bias network (reconcile R14/R15). 
Enable/reset defaults:** DE low + /RE high = shutdown. Firmware must assert safe state before cutoff. 
Power domains:** Switched 3V3 only. Active ~1 mA; shutdown ≤1 µA (datasheet). Board-off: rely on transceiver leakage limits + external isolation if vehicle bus remains energized. 
Protection:** Series resistors or isolation pending electrical review; no continuous A5 load. 
Firmware notes:** Direction control on transmit; account for possible masking with power supervisor. No spare-alarm assumption. 
BOM/space:** Transceiver + 120 Ω + bias resistors + optional TVS. Low.

Fallback Interface (Daughterboard Header)
Header:** Defined multi-pin (e.g., 2×5 or similar) carrying: UART TX/RX, DE, optional SPI CS/SCK/MOSI/MISO/INT, switched 3V3, GND, bus return, enable. Orientation keyed; mechanical allowance and return-current path specified. 
Population:** Neither RS-485 nor CAN on main board. External module or future daughterboard. 
Off-state:** Unpopulated = zero load. Pins floating or weakly pulled only if isolation verified. 
Pinout must be frozen with LRA-03.**

Explicit Non-Selections / Limits
No onboard CAN controller populated in Rev A baseline. 
No continuous-powered bus. 
No assumption of vehicle CAN or keyless interoperability. 
2/5 µA bus/service allocation is provisional/unproved; any option exceeding it requires explicit tradeoff request. 
Final pin reservations, connector, isolation, and protection deferred to LRA-03 + electrical review.

Next Bounded Actions
LRA-03 coordination for exact GPIO/connector reservations. 
Electrical review of isolation/protection and measured off-state currents. 
Bias/termination reconciliation from keyless schematic/PCB. 
Firmware compatibility check (direction, IRQ, power supervisor) after pin freeze. 

Sources: LRA-04 packet; LRA-01 INTERFACE_CONTRACT.md and LRA-02 COMPONENT_MARGIN_CLOSURE.md (provisional allocations); keyless hondaPico RS-485 notes and firmware pin assignments; Maxim/Analog MAX3485 datasheet (shutdown, currents, CM range); MCP2515 and Pico library documentation for CAN alternative; REV_A_CONTEXT.md.

This completes the LRA-04 comparison and the two requested documents using the packet and linked sources. All limits that remain open are identified; schematic freeze is not claimed. 
