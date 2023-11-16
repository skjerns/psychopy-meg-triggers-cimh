# cimh-psychopy-MEG

Python module for interacting with NI6321 PCIe card to send triggers to a MEGIN TRIUX MEG.

Supports debug mode for trying stuff outside of the lab in absence of a NI6321.

## Installation

`pip install git+https://github.com/skjerns/cimh-psychopy-MEG`

## Quickstart

```Python
import meg_triggers
from meg_triggers import send_trigger
...
# send trigger value of 16 for 5 milliseconds
# then reset the channel to value 0
# this happend non-blocking, i.e. execution of experiment continues
send_trigger(16, 0.005)
```

If you want to debug your code or test it without having access to a NI6321 PCI card, the library will automatically default back to simpy printing out debug information about triggers that would have been sent.

![image](https://github.com/skjerns/cimh-psychopy-MEG/assets/14980558/2804ad4f-1b7b-47f3-a4c1-add9e052c142)


## Usage

1. Put a custom code component anywhere in your psychopy builder project
2. within the code component add to the `Before experiment` section `import meg_triggers; from meg_triggers import send_trigger`
3. Anywhere in the code, use `send_trigger(value=x, duration=y)` to send a trigger to the port
    - e.g. if you want to send a trigger value of 15 for 5 ms, use `send_trigger(value=15, duration=0.005)`
    - after `duration`, the trigger channel will be reset to 0
    - if you want to set the trigger channel to a value without returning to 0, use use `send_trigger(value=15, duration=0)`
5. The trigger will be send non-blocking, i.e. the code will continue running while `duration` is waited


- You can enable debug printing via `meg_triggers.enable_printin()`. This will print all sent triggers to the console.

## Bugs

If you encounter any bugs, feel free to open an issue. The code has been tested and used in experiments, so it should theoretically work. However, there might be cases in which it doesn't, so let me know.
