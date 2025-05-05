#!/usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
import threading
import time
import traceback
from queue import Empty, Queue

import numpy as np

try:
    from psychopy import core
    curr_exp_time = lambda: core.getTime()
except (ModuleNotFoundError, ImportError):
    print('psychopy not installed, will debug print current time instead of experiment time.')
    curr_exp_time = lambda: time.time()


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
    return np.array([x for x in bin(number)[2:].zfill(8)][::-1], dtype=np.uint8)

def binary_to_int(array):
    """convert number from int to 8 bit binary"""
    return array.dot(2**np.arange(array.size))


class _MEGTriggerThread(threading.Thread):
    def __init__(self, q):
        super(_MEGTriggerThread,self).__init__(daemon=True)
        self.q = q
        self.keep_running = True
        self.default_duration = 0.005
        self.default_reset_value = 0
        self.verbose = False

    def kill(self):
        self.keep_running = False
        self.join(timeout=0.25)

    def run(self):
        self.connect()
        while self.keep_running:
            try:
                res = self.q.get(timeout=1)
            except Empty:
                continue

            # retrieve trigger value and requested length
            if res=='quit':
                self.disconnect()
                break
            try:
                value, duration, reset_value = res
                self.send_trigger(value, duration, reset_value)
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

    def send_trigger(self, value_bin, duration=None, reset_value=None):
        start_time = time.perf_counter()
        self._send_trigger(value_bin)
        if self.verbose or ENABLE_DEBUG:
            value = binary_to_int(value_bin)
            msg = f'trigger channel = {value} @{curr_exp_time():.3f}s '
            _print(msg)
        if duration is not None:
            time.sleep(duration)
            self._send_trigger(reset_value)
            duration = int(np.round((time.perf_counter() - start_time)*1000))
            if self.verbose or ENABLE_DEBUG:
                _print(f'reset trigger channel, active ~{duration}ms')

#########################

_queue = Queue()
_meg_trigger_thread = _MEGTriggerThread(q=_queue)
_meg_trigger_thread.start()

@atexit.register
def _atexit():
    """some cautionary measures. Probably not necessary."""
    _queue.put('quit')
    _meg_trigger_thread.keep_running = False
    _meg_trigger_thread.disconnect()
    try:
        _meg_trigger_thread.join(timeout=0.25)
    except:
        pass

def set_default_duration(duration):
    """set default duration that is used if no duration is indicated"""
    if (duration is not None) and duration>0.1:
        _print(f'default duration is set to {duration} seconds, seems a bit long?')
    _meg_trigger_thread.default_duration = duration

def set_default_reset_value(reset_value):
    """this value is used to reset the channel to a specific value after
    a call with duration>0"""
    _meg_trigger_thread.default_reset_value = reset_value


def enable_printing():
    """print the send trigger values to the console"""
    _meg_trigger_thread.verbose = True

def disable_printing():
    """dont print anything. if ENABLE_DEBUG is active, will always print."""
    _meg_trigger_thread.verbose = False

def send_trigger(value, duration=None, reset_value=None):
    """send a trigger to the NI6321 device
    :param value:     can be any int between 0 and 255
    :param duration:  send
    """


    assert _meg_trigger_thread.is_alive(), 'ERROR: trigger thread died. Please report this error!'

    if duration is None:
        duration = _meg_trigger_thread.default_duration

    if reset_value is None:
        reset_value = _meg_trigger_thread.default_reset_value


    if isinstance(reset_value, int):
        # convert to binary if necessary
            reset_value_bin = int_to_binary(reset_value)
    elif isinstance(value, (np.ndarray, tuple, list)):
        assert (x:=len(value))==8, f'trigger value must be 8bit but is of len {x}'
    else:
        raise ValueError('trigger value must be array, tuple or list')


    if isinstance(value, int):
        # convert to binary if necessary
            value_bin = int_to_binary(value)
    elif isinstance(value, (np.ndarray, tuple, list)):
        assert (x:=len(value))==8, f'trigger value must be 8bit but is of len {x}'
    else:
        raise ValueError('trigger value must be array, tuple or list')

    _queue.put_nowait([value_bin, duration, reset_value_bin])




if __name__=='__main__':

    print('## SEND 5')
    send_trigger(5)

    print('## SEND 5 FOR 0.005')
    send_trigger(5, 0.005)
    time.sleep(0.01)

    print('## SEND 5 FOR 0.005, RESET TO 10')
    send_trigger(5, 0.005, 10)
    time.sleep(0.01)

    print('## SEND 5 WITH DEFAULT 0.005')
    set_default_duration(0.005)
    send_trigger(5)
    time.sleep(0.01)

    print('## SEND 5 WITH DEFAULT 0.005 RESET TO DEFAULT 10')
    set_default_duration(0.005)
    set_default_reset_value(10)
    send_trigger(5)
    time.sleep(0.01)

    for i in range(255):
        set_default_duration(None)
        set_default_reset_value(0)
        send_trigger(i, duration=None)
        time.sleep(0.01)
