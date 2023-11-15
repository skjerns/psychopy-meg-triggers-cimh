# cimh-psychopy-MEG

Python module for interacting with NI6321 PCIe card to send triggers to a MEGIN TRIUX MEG.

Supports debug mode for trying stuff outside of the lab in absence of a NI6321.

## Installation

`pip install git+https://github.com/skjerns/cimh-psychopy-MEG`


Anyhwere in the code you can also write `send_trigger(value, duration)` to manually send a trigger, e.g. `send_trigger(15, duration=0.005)` will raise the trigger line to 15 for 5 milliseconds, however, be aware that any script execution is paused for this duration. If you set `duration=0` the line will be kept at the trigger value and not be reset to 0.

## Usage

1. Put a custom code component anywhere in your psychopy builder project
2. within the code component add to the `Before experiment` section `import meg_triggers; from meg_triggers import send_trigger`
3. Anywhere in the code, use `send_trigger(value=x, duration=y)` to send a trigger to the port
    - e.g. if you want to send a trigger value of 15 for 5 ms, use `send_trigger(value=15, duration=0.005)`
    - after `duration`, the trigger channel will be reset to 0
    - if you want to set the trigger channel to a value without returning to 0, use use `send_trigger(value=15, duration=0)`
5. The trigger will be send non-blocking, i.e. the code will continue running while `duration` is waited

## Bugs

If you encounter any bugs, feel free to open an issue. The code has been tested and used in experiments, so it should theoretically work. However, there might be cases in which it doesn't, so let me know.
