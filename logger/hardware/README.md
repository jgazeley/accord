# Logger hardware interface

The logger is a separate Pico W from the keyless module. The keyless KiCad
board in this repository is not a logger PCB. The current logger uses a
prototype signal-conditioning circuit, SD storage and an external regulated
5 V supply; the Pi is only a flashing and observation bench.

| Measurement/interface | Pico GPIO |
|---|---|
| Vehicle speed pulses | GP2 |
| Tachometer pulses | GP3 |
| Brake-warning level | GP4 |
| Conditioned ignition input | GP5 |
| Fuel analog input | GP26 / ADC0 |
| Supply analog input | GP27 / ADC1 |
| SD MISO / CS / SCK / MOSI | GP16 / GP17 / GP18 / GP19 |

This map comes from `accord-logger.ino` and `logger_sd.cpp`. Automotive
signals require the appropriate conditioning before reaching the Pico; this
pin map alone is not a wiring schematic. The brake-warning signal can represent
parking brake or low fluid, not an unambiguous parking-brake state. The fuel
input records ADC measurements, not an independently calibrated fuel quantity.

A reviewed, consolidated logger schematic and BOM are now published in
[kicad/](kicad/) as `accord-logger.kicad_pro`, integrated October 29 after
review. It is a reviewed candidate, **not frozen and not fabrication-ready**:
one electrical question is open on the ignition optocoupler's return, the
input-isolation part is unselected, and no layout exists. Automatic power
cutoff is not implemented in this firmware baseline. No fabrication-ready
logger board is claimed by this repository.

The pin map above is the **as-built** firmware baseline. Rev A changes what
GP5 means and adds GP6; see [as-built/REV_A_INTERFACES.md](as-built/REV_A_INTERFACES.md) §1.

Current electrical/PCB context: [Rev A context](REV_A_CONTEXT.md).
Active task authority: [project milestones](../../coordination/PROJECT_MILESTONES.md).
