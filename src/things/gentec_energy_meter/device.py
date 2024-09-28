import datetime
import time
import os
from gentec_energy_meters.extensions import GentecMaestroEnergyMeter as GentecEnergyMeter, EnergyDataPoint
# See base implementation here : https://gitlab.com/hololinked-examples/gentec-optical-energy-meters
# pip install it to use it in this script
from data_storage.file_storage import FileStorage
from triggered_device import HWTriggeredDevice



class GentecMaestroEnergyMeter(HWTriggeredDevice, GentecEnergyMeter):


    def __init__(self, instance_name: str) -> None:
        HWTriggeredDevice.__init__(self, instance_name)
        GentecEnergyMeter.__init__(self, instance_name)
        self.data_file = FileStorage(
                                path=os.environ.get('DATA_PATH', 'data'),
                                filename=f'energy_data_{datetime.datetime.today()}.txt',
                                separator='\t',
                                columns=['shot number', 'shot time', 'measurement time', 'energy']
                            )

    def loop(self):
        self._run = True
        while self._run:
            # Since the data point is a single float value and a timestamp which are very very small in size,
            # Its also sufficient if one implement's this loop purely at a client level. 
            # The server implementation is useful when the acquisition has to happen indenpendently of the
            # client.
            acquisition_start_time = time.perf_counter()
            self.reset_shot_info()
            if self.new_value_ready:
                self._last_measurement = self.current_value
                measurement_time = time.perf_counter()
                timestamp = datetime.datetime.now()
                timestamp = timestamp.strftime("%H:%M:%S") + '.{:03d}'.format(int(timestamp.microsecond /1000))
                if self.trigger_reader is not None:
                    self.wait_for_trigger_event(acquisition_start_time)
                if not self.shot_update_successful:
                    self.logger.error(f"shot event arrived too late")
                    if self.use_only_successful_shots:
                        continue
                self.energy_history.timestamp.append(timestamp)
                self.energy_history.energy.append(self._last_measurement)
                # self.data_point_event.push(EnergyDataPoint(
                #                             timestamp=timestamp, 
                #                             energy=self._last_measurement
                #                         ))
                self.data_file.store([self.shot_number, self.shot_time, timestamp, self._last_measurement])
                if self._statistics_enabled:
                    self.statistics_event.push(self.statistics)
                self.data
                self.logger.debug(f"New data point : {self._last_measurement} J")
            else:
                self.logger.debug("No new data point available")
            # auto serialization of the event data happens when a json() method is implemented,
            # which has been done in the dataclass
        