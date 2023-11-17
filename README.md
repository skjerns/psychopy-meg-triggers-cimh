# cimh-psychopy-meg

Python module for interacting with NI6321 PCIe card to send triggers to a MEGIN TRIUX MEG.

Supports debug mode for trying stuff outside of the lab in absence of a NI6321.

## Installation

`pip install git+https://github.com/skjerns/cimh-psychopy-meg`

## Quickstart

```Python
import meg_triggers
from meg_triggers import send_trigger
...
# set trigger channel to value 16 
# then wait 5 ms and reset the channel to value 0
# this happend non-blocking, i.e. execution of experiment continues
send_trigger(value=16, duration=0.005)
```

If you want to debug your code or test it without having access to a NI6321 PCI card, the library will automatically default back to simpy printing out debug information about triggers that would have been sent.

![image](https://github.com/skjerns/cimh-psychopy-MEG/assets/14980558/2804ad4f-1b7b-47f3-a4c1-add9e052c142)


## Usage

![image](https://github.com/skjerns/psychopy-meg-triggers-cimh/assets/14980558/d3917f05-a28f-404d-8f79-a7a5063e691b)


1. Put a custom code component anywhere in your psychopy builder project
2. within the code component add to the `Before experiment` section `import meg_triggers; from meg_triggers import send_trigger`
3. Anywhere in the code, use `send_trigger(value=x, duration=y)` to send a trigger to the port
    - e.g. if you want to send a trigger value of 15 for 5 ms, use `send_trigger(value=15, duration=0.005)`
    - after `duration`, the trigger channel will be reset to 0
    - if you want to set the trigger channel to a value without returning to 0, use use `send_trigger(value=15, duration=0)`
5. The trigger will be send non-blocking, i.e. the code will continue running while `duration` is waited

![image](https://github.com/skjerns/psychopy-meg-triggers-cimh/assets/14980558/02771e5e-8f7a-4e73-aacf-ed67a04b880a)


These are all the functions that are available:
```
meg_triggers.send_trigger(value, duration=None, reset_value=None)   # set trigger channel to $value for $duration seconds, reset to $reset_value after that
meg_triggers.set_default_duration(duration)  # set a default value for duration. Per default it is 0.005
meg_triggers.set_default_reset_value(value)  # set the value the trigger channel returns to for neutral state
meg_triggers.enable_printing()               # output all triggers to console as well, e.g. for debugging
meg_triggers.disable_printing()              # don't output to console
```

- You can enable debug printing via `meg_triggers.enable_printing()`. This will print all sent triggers to the console.

## Bugs

If you encounter any bugs, feel free to open an issue. The code has been tested and used in experiments, so it should theoretically work. However, there might be cases in which it doesn't, so let me know.
