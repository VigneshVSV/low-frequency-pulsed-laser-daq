import base64
import datetime
import time
from ueye_camera import UEyeCamera
# See base implementation here : https://gitlab.com/hololinked-examples/ids-ueye-camera
# pip install it to use it in this script
from data_storage.file_storage import FileStorage
from triggered_device import HWTriggeredDevice


class Camera(HWTriggeredDevice, UEyeCamera):


    def __init__(self, instance_name: str) -> None:
        HWTriggeredDevice.__init__(self, instance_name)
        UEyeCamera.__init__(self, instance_name)
        self.data_file = FileStorage()

    def capture_loop(self, count : int = None):
        self._capture = True
        self.alloc()
        self.start_video()
        self.state_machine.set_state(self.states.CAPTURE)
        i = 0
        while self._capture:
            if count and i >= count:
                break
            try:
                acquisition_start_time = time.perf_counter()
                image, timestamp = self.get_next_image(return_timestamp=True) 
                if self.trigger_reader is not None:
                    self.wait_for_trigger_event(acquisition_start_time)
                if not self.shot_update_successful:
                    self.logger.error(f"shot event arrived too late")
                    if self.use_only_successful_shots:
                        continue
                self._last_numpy_image = image
                self._last_jpeg = base64.b64encode(self.cast_image(image, format='jpeg'))
                self.logger.debug(f"got image at {timestamp} with frame count {self.frame_count}") # framecount read triggers change event  
                self.image_event.push(self._last_jpeg, serialize=False)
            except Exception as ex:
                if "FIFO ring buffer overflow" in str(ex):
                    self.stop_video()
                    self.dealloc()
                    self.alloc()
                    self.start_video()
            i += 1
        self.stop_video()
        self.state_machine.set_state(self.states.ON)