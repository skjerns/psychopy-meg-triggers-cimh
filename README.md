# cimh-psychopy-MEG

Python module for interacting with NI6321 PCIe card to send triggers to a MEGIN TRIUX MEG.

Supports debug mode for trying stuff outside of the lab in absence of a NI6321.

## Installation

`pip install git+https://github.com/skjerns/cimh-psychopy-MEG`


Anyhwere in the code you can also write `send_trigger(value, duration)` to manually send a trigger, e.g. `send_trigger(15, duration=0.005)` will raise the trigger line to 15 for 5 milliseconds, however, be aware that any script execution is paused for this duration. If you set `duration=0` the line will be kept at the trigger value and not be reset to 0.
