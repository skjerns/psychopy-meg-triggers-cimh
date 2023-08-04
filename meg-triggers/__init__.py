#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from copy import copy
from pathlib import Path
from psychopy.tools import stringtools as st
from psychopy.experiment.components import BaseComponent, Param, _translate, getInitVals
from psychopy.localization import _localized as __localized
from psychopy import logging
import uuid
import types

def log(*args):
    logging.error(' '.join([str(x) for x in args]))

class MegTriggerComponent(BaseComponent):
    """Send Trigger via NI-6321, a PCIe card, using PyDAQmx."""

    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    version = "2022.2.0"
    iconFile = Path(__file__).parent / 'serial.png'
    tooltip = _translate('MEG Triggers: Send triggers via Ni-6321')
    beta = True

    def __init__(self, exp, parentName, name='MegTrigger',
                 startType='STARTED', startVal='component_name',
                 stopType='duration (frames)', stopVal=1,
                 startEstim='', durationEstim='', binding='onset',
                 triggervalue=1, resetvalue=0,
                 syncScreenRefresh=True):

        super(MegTriggerComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            syncScreenRefresh=syncScreenRefresh)

        self.params['startType'].allowedVals = ['STARTED', 'FINISHED', 'NOT_STARTED', 'condition']
        self.params['stopType'].allowedVals = ['duration (frames)']

        self.params['startType'].label = 'Component name'

        self.type = 'MegTriggerComponent'
        self.url = "https://skjerns.de"

        self.params['triggervalue'] = Param(
            triggervalue, valType='int', inputType="single", allowedTypes=[], categ='Basic',
            hint=_translate("Value that will be sent to the trigger port"),
            label=_translate("Trigger value"))

        self.params['resetvalue'] = Param(
            resetvalue, valType='int', inputType="single", allowedTypes=[], categ='Basic',
            hint=_translate("Value that will indicate that the trigger is over. Usually 0."),
            label=_translate("Reset Trigger value"))

        self.params['enabledebug'] = Param(
            resetvalue, valType='bool', inputType="bool", allowedTypes=[], categ='Basic',
            hint=_translate("Will print triggers to console for this component"),
            label=_translate("Enable component debug printing"))

        self.params['globaldebug'] = Param(
            resetvalue, valType='bool', inputType="bool", allowedTypes=[], categ='Basic',
            hint=_translate("Will print triggers to console for ANY trigger"),
            label=_translate("Enable global debug printing"))

    def writeBlockCode(self, buff, code, writefunc=None):
        assert code.startswith('\n'), 'Code needs to start with newline'
        code = code.split('\n')
        assert len(code[1].strip())>0, 'Code needs to be on second line'

        # find out intendation level
        for base_indent, c in enumerate(code[1]):
            if c!=' ': break

        code = [c[base_indent:] for c in code]
        code = '\n'.join(code)
        if writefunc is not None:
            return writefunc(code)
        return buff.writeIndented(code)

    def writeInitCode(self, buff):
        name = self.params['name'].val

        code = f"""
                def {name}(): pass
                """
        self.writeBlockCode(buff, code)


    def writeRunOnceInitCode(self, buff):
        code =  f'''
                try:
                    from PyDAQmx import Task
                    import PyDAQmx
                    tpydaqmxtask = Task()
                    trigger_global_debug = False

                except ModuleNotFoundError as e:
                    raise e
                except NotImplementedError as e:
                    logging.warning('PyDAQmx is installed, but library not found')
                    logging.warning('trigger debug will be activated, no actual triggers will be sent')
                    trigger_global_debug = True

                    class Dummy_tpydaqmxtask():
                        """debug dummy module for pydaqmx"""
                        DAQmx_Val_ChanForAllLines = None
                        DAQmx_Val_GroupByChannel = None
                        def CreateDOChan(self, *args):
                            logging.info(f'created trigger channel with {{args=}}')
                        def StartTask(self): pass
                        def WriteDigitalLines(self, *args): pass
                        def StopTask(self):pass
                        def ClearTask(self): pass

                    tpydaqmxtask = PyDAQmx = Dummy_tpydaqmxtask()

                tpydaqmxtask.CreateDOChan("Dev1/port0/line0:7","",
                                          PyDAQmx.DAQmx_Val_ChanForAllLines)
                tpydaqmxtask.StartTask()

                def _send_trigger(value, debug, debug_extras):
                    if trigger_global_debug or debug:
                        print(f'@{{core.getTime():.4f}}: sent {{value}} for {{debug_extras}}')
                    if isinstance(value, int):
                        value_bin = int_to_binary(value)
                    tpydaqmxtask.WriteDigitalLines(1,1,10.0,PyDAQmx.DAQmx_Val_GroupByChannel,
                                                   value_bin,None,None)

                # stores whether we are currently in progress of sending something
                active_meg_trigger = False

                def int_to_binary(number):
                    # assert 0<=number<256, f'trigger value needs to be between 0 and 255, but {{number=}}'
                    return np.array([x for x in bin(number)[2:].zfill(8)], dtype=np.uint8)

                def send_trigger(value, duration=0, debug=False, debug_extras=None):
                    """send a trigger to the NI6321 device
                    :param value: can be any int between 0 and 255
                    :param duration: is optional. Blocks execution and sends the reset
                                     trigger after the interval has passed
                    :param debug: print trigger output to console
                    """
                    _send_trigger(value, debug, debug_extras)
                    if duration>0:
                        core.wait(duration)
                        _send_trigger(0, debug)

              '''
        self.writeBlockCode(buff, code, buff.writeOnceIndentedLines)

    def writeRoutineStartCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")

        name = self.params['name'].val
        startVal = self.params['startVal'].val
        stopVal = int(self.params['stopVal'].val)
        triggerdebug = self.params['enabledebug'].val
        globaldebug = self.params['globaldebug'].val
        assert stopVal>0


        code=f"""
                # stores how many frames the trigger has been sent
                {name}_enable_trigger_debug = {triggerdebug}
                {name}_count = {stopVal}
                {'trigger_global_debug = True' if globaldebug else ''}
              """
        self.writeBlockCode(buff, code)

    def writeFrameCode(self, buff):
        params = copy(self.params)

        condition_type = self.params['startType'].val
        startVal = self.params['startVal'].val
        stopVal = self.params['stopVal'].val
        name = self.params['name'].val
        triggervalue = self.params['triggervalue'].val
        resetvalue = self.params['resetvalue'].val

        cond_statement = startVal if condition_type=='condition' else f'{startVal}.status=={condition_type}'
        cond_statement = cond_statement.replace("'", '"')

        code = f"""
                if {cond_statement}:
                    if {name}_count=={stopVal}:
                        if active_meg_trigger:
                            logging.warning('two active MEG triggers at the same time @{{core.getTime():.4f}}, check timing and conditions!')
                        send_trigger({triggervalue}, duration = 0,
                                     debug = {name}_enable_trigger_debug,
                                     debug_extras = '{startVal}@{condition_type}')
                        {name}_count -= 1
                        active_meg_trigger = True
                    elif {name}_count>0:
                        {name}_count -= 1
                    elif {name}_count==0:
                        send_trigger({resetvalue}, debug = {name}_enable_trigger_debug,
                                     debug_extras = ' (reset) {startVal}@{condition_type}')
                        active_meg_trigger = False
                        {name}_count -= 1
               """
        self.writeBlockCode(buff, code)



    def writeExperimentEndCode(self, buff):
        code="""
                tpydaqmxtask.StopTask()
                tpydaqmxtask.ClearTask()
             """
        self.writeBlockCode(buff, code, buff.writeOnceIndentedLines)
