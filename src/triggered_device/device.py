import time
import threading 
import typing
from datetime import datetime
from pydantic import BaseModel

from hololinked.param import depends_on
from hololinked.server import Thing 
from hololinked.server.properties import (Number, Integer, String, Selector, 
                                        Boolean, ClassSelector)
from hololinked.client import ObjectProxy


class TriggerReader(BaseModel):
    instance_name: str
    address: str
    protocol : str


class HWTriggeredDevice(Thing):
    """
    Prototype class for hardware triggered devices. Inherit from this class to collect measurement on hardware trigger which 
    arrives as a software event.
    """

    def __init__(self, instance_name : str) -> None:
        super().__init__(instance_name=instance_name)
        self._shot_update_lock = threading.Lock()
        self._shot_updated_event = threading.Event()
        self._shot_update_successful = False
        self._trigger_device = ObjectProxy(self.trigger_reader.address, self.trigger_reader.protocol)


    shot_number = Integer(doc="latest shot number counted, None for never counted", 
                        default=None, allow_None=True, bounds=(0, None))
    
    shot_time = String(doc="time of the lastest shot, None for no shots arrived", 
                        default=None, allow_None=True) 

    system_shot_time = Number(doc="system time of the lastest shot, None for no shots arrived", 
                            default=None, allow_None=True, bounds=(0, None))
    
    shot_counting_enabled = Boolean(default=False, doc="enable counting of shots (consider this also as an action)", 
                                db_commit=True)

    trigger_reader = ClassSelector(doc="trigger reader device address", class_=TriggerReader,
                                default=TriggerReader(instance_name='arduino-trigger-reader', protocol='IPC', address=''), 
                                allow_None=True, readonly=True) # type: TriggerReader
    # will be made read-write in the future when pydantic support becomes stable, this is a hardcoded patch

    counting_mode = Selector(objects=['DAQ-SYSTEM-WIDE', 'COMPUTER-ISOLATED'], default='COMPUTER-ISOLATED',
                        doc="""Judges the way in which the trigger arrival time stamps will be used. 
                        DAQ-SYSTEM-WIDE is to be used when the trigger arrival time stamps originate from a global trigger reading device producing 
                        a global time stamp passed onto all measurement devices in all computers. In this case, the clocks of the computers need to 
                        accurate/in-sync desirable to the speed of the application/trigger frequency. COMPUTER-ISOLATED means the trigger arrival 
                        time stamps will be judged by the system time (performance counter) of the computer. In this case, there must be a trigger 
                        reader in every computer.""")

    trigger_arrival_tolerance_time = Number(doc="trigger arrival tolerance time in seconds, for example, 0.025 for 25ms", 
                                            default=0.025, bounds=(0, None))
    
    def shot_event(self, event_data):
        """"""
        self._shot_update_lock.acquire()
        try: 
            # reset every shot
            self._shot_updated_event.clear()
            self._shot_update_successful = False 

            # retrieve values first
            shot_number = event_data['trigger_count'] # type: int
            system_shot_time = event_data['system_time'] # type: typing.Union[float, int]
            shot_time = event_data['timestamp'] # type: str

            # did shot event come on time? 
            if (self.counting_mode == 'COMPUTER-ISOLATED' and time.perf_counter() - system_shot_time > self.trigger_arrival_tolerance_time) or (
                self.counting_mode == 'DAQ-SYSTEM-WIDE' and datetime.now() - shot_time > self.trigger_arrival_tolerance_time):
                self.logger.error(f"shot event {shot_number} arrived too late")
                return 
            else:
                # if yes, update them
                self.shot_time = shot_time
                self.shot_number = shot_number
                self.system_shot_time = system_shot_time
                # collect the measurement
                self.collect_measurement()
                # claim shot event came on time
                self._shot_update_successful = True
                self._shot_updated_event.set()
        finally:
            # cleanup
            self._shot_update_lock.release()


    def collect_measurement(self):
        """override this method in your device class to collect latest measurement data for the shot"""
        self.logger.debug(f'HWTriggeredDevice prototype collect_measurement - shot number {self.shot_number}')


    def wait_for_trigger_event(self, trigger_delay_tolerance_reference_time) -> None:
        """call this method in sync to wait for trigger event to arrive"""
        if self.counting_mode == 'COMPUTER-ISOLATED':
            assert isinstance(trigger_delay_tolerance_reference_time, float), "you passed a wrong reference time, you need to send a float from time.perf_counter()"
            elapsed_time = time.perf_counter() - trigger_delay_tolerance_reference_time
        else:
            assert isinstance(trigger_delay_tolerance_reference_time, datetime), "you passed a wrong reference time, you need to send python standard datetime object"
            elapsed_time = datetime.now() - trigger_delay_tolerance_reference_time
        if self.trigger_arrival_tolerance_time - elapsed_time > 0:
            self._shot_updated_event.wait(self.trigger_arrival_tolerance_time - elapsed_time)
        self._shot_update_lock.acquire() # ensure no unnecessary blocking from shot event thread -> shot event thread completed
        self._shot_update_lock.release()
        self._shot_updated_event.clear()


    @depends_on(shot_counting_enabled)
    def shot_counting_enabled_changed(self, value):
        if value:
            self.logger.info(f'shot counting enabled')
            self._trigger_device.subscribe_event('hardware-trigger-event', self.shot_event)
        else:
            self.logger.info(f'shot counting disabled')
            self._trigger_device.unsubscribe_event('hardware-trigger-event')