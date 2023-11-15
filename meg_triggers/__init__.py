#!/usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import threading
import time
import traceback
from queue import Empty, Queue

import numpy as np
# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from psychopy import core


def _print(*args, **kwargs):
    args = ['[meg-triggers]'] + [x for x in args]
    print(*args, **kwargs)

try:
    # try to load PyDAQmx
    import PyDAQmx
    from PyDAQmx import Task
    tpydaqmxtask = Task()
    ENABLE_DEBUG = False

except ModuleNotFoundError:
    # not installed!
    _print('PyDAQmx is not installed. No triggers will be sent.')
    ENABLE_DEBUG = True

except NotImplementedError:
    # installed, but the library or card was not found
    # this can be the case if we are not running in the lab environment
    _print('PyDAQmx is installed, but C library not found (PCI card not installed?)')
    ENABLE_DEBUG = True


# if DEBUG is enabled, create a dummy object so that the other functions
# don't crash when requesting anything from PyDAQmx
if ENABLE_DEBUG:
    _print('ENABLE_DEBUG is activated, no actual triggers will be sent, but you will see a printout in the console.')

    class Dummy_tpydaqmxtask():
        """debug dummy module for pydaqmx"""
        DAQmx_Val_ChanForAllLines = None
        DAQmx_Val_GroupByChannel = None
        def CreateDOChan(self, *args):
            _print('ENABLE_DEBUG - no triggers will be sent.')
        def StartTask(self): pass
        def WriteDigitalLines(self, *args): pass
        def StopTask(self):pass
        def ClearTask(self): pass

    tpydaqmxtask = PyDAQmx = Dummy_tpydaqmxtask()



def int_to_binary(number):
    """convert number from int to 8 bit binary"""
    assert 0<=number<256, f'trigger value needs to be between 0 and 255, but {number=}'
    return np.array([x for x in bin(number)[2:].zfill(8)], dtype=np.uint8)

class MEGTriggerThread(threading.Thread):
    def __init__(self, q):
        super(MEGTriggerThread,self).__init__(daemon=True)
        self.q = q
        self.keep_running = True
        self.verbose = False
        return

    def kill(self):
        self.keep_running = False
        self.join(timeout=0.25)

    def run(self):
        self.connect()
        while self.keep_running:

            try:
                res = self.q.get_nowait()
            except Empty:
                continue

            # retrieve trigger value and requested length
            if res=='quit':
                self.disconnect()
                break
            try:
                value, duration = res
                if value:
                    self.send_trigger(value, duration)
            except Exception as e:
                _print(traceback.format_exc())
                self.kill()
                raise e

    def connect(self, device="Dev1/port0/line0:7", param2="",
              lines=PyDAQmx.DAQmx_Val_ChanForAllLines):
        """start the current connection to the interface"""
        if not ENABLE_DEBUG:
            _print(f'Connecting to device {device}')
        tpydaqmxtask.CreateDOChan(device, param2,lines )
        tpydaqmxtask.StartTask()

    def disconnect(self):
        """quit the current connection to the interface"""
        if not ENABLE_DEBUG:
            _print('Disconnecting from trigger device')
        tpydaqmxtask.StopTask()
        tpydaqmxtask.ClearTask()

    def _send_trigger(self, value_bin):

        tpydaqmxtask.WriteDigitalLines(1,1,10.0,PyDAQmx.DAQmx_Val_GroupByChannel,
                                       value_bin,None,None)

    def send_trigger(self, value_bin, duration=0):
        start_time = time.perf_counter()
        self._send_trigger(value_bin)

        if self.verbose or ENABLE_DEBUG:
            msg = f'set trigger channel to {value_bin} @{core.getTime():.3f}s for '
            if duration>0:
                msg += f'{duration:.3f}s'
            else:
                msg += ' inf s'
            _print(msg)

        if duration>0:
            core.wait(duration)
            self._send_trigger(0)
            duration = time.perf_counter() - start_time
            _print(f'reset trigger channel to 0, was active for {duration:.3f}s')

#########################

_queue = Queue()
_meg_trigger_thread = MEGTriggerThread(q=_queue)
_meg_trigger_thread.start()

@atexit.register
def _atexit():
    """some cautionary measures. Probably not necessary."""
    _queue.put('quit')
    _meg_trigger_thread.keep_running = False
    _meg_trigger_thread.disconnect()
    _meg_trigger_thread.join(timeout=0.25)


def enable_printing():
    """print the send trigger values to the console"""
    _meg_trigger_thread.verbose = True

def disable_printing():
    """dont print anything. if ENABLE_DEBUG is active, will always print."""
    _meg_trigger_thread.verbose = False

def send_trigger(value, duration=0):
    """send a trigger to the NI6321 device
    :param value:     can be any int between 0 and 255
    :param duration:  send
    """
    if isinstance(value, int):
        # convert to binary if necessary
        value_bin = int_to_binary(value)
    elif isinstance(value, (np.ndarray, tuple, list)):
        assert (x:=len(value))==8, f'trigger value must be 8bit but is of len {x}'
    else:
        raise ValueError('trigger value must be array, tuple or list')
    assert _meg_trigger_thread.is_alive(), 'ERROR: trigger thread died. Please report this error!'
    _queue.put_nowait([value_bin, duration])