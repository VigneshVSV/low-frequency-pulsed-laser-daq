import time 
import pandas as pd

from picoscope import Picoscope6000
# See base implementation here : https://gitlab.com/hololinked-examples/picoscope
# pip install it to use it in this script
from data_storage.file_storage import FileStorage
from triggered_device import HWTriggeredDevice


class Picoscope(Picoscope6000, HWTriggeredDevice):

    def __init__(self, instance_name: str) -> None:
        Picoscope6000.__init__(self, instance_name)
        HWTriggeredDevice.__init__(self, instance_name)
        self.data_file = FileStorage()

    def block_loop(self, time_interval, resolution, pre_trigger = 0, max_acq = -1):
        self._run = True
        counter = 0
        while self._run:
            if max_acq > 0 and counter >= max_acq:
                break

            acquisition_start_time = time.perf_counter()
            self.reset_shot_info()
            self.logger.debug(f"starting next acquisition")

            data = self.run_block_hl(time_interval, resolution, pre_trigger)  
            counter += 1
            if not len(data) > 0:
                continue
            measurement_time = time.perf_counter()

            if self.trigger_reader is not None:
                self.wait_for_trigger_event(measurement_time)
            if not self.shot_update_successful:
                self.logger.error(f"shot event {counter} arrived too late")
                if self.use_only_successful_shots:
                    continue
            
            if 'A' in data:
                self.channel_A = data['A']
            else:
                self.channel_A = None 
            if 'B' in data:
                self.channel_B = data['B']
            else:
                self.channel_B = None 
            if 'C' in data:
                self.channel_C = data['C']
            else:
                self.channel_C = None
            if 'D' in data:
                self.channel_D = data['D']
            else:
                self.channel_D = None
            self.time = data['t']

            data = pd.DataFrame(data)
            self.data_ready_event.push(measurement_time)
            if hasattr(self, 'data_file'):
                self.data_file.store_in_new_file(data)
            self.logger.debug(f"took measurement {counter} at {measurement_time} system time, total elapsed time {time.perf_counter() - acquisition_start_time} ms")
           

def store_data_in_pickled_format(file_handle, data : pd.DataFrame):
    data.to_pickle(file_handle)
 