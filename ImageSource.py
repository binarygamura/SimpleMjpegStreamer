import time, traceback, logging, datetime
from io import BytesIO
from picamera import PiCamera


class ImageSource:

    def __init__(self, fps: int, camera: PiCamera):
        self.fps = fps
        self.camera = camera
        self.LOGGER = logging.getLogger(__name__)

    def setup_text(self, text: str = None):
        message = text if text is not None else datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.camera.annotate_text = message

    def get_images(self):
        try:
            cycle_duration_s = 1 / self.fps
            self.camera.start_preview()

            buffer = BytesIO()
            self.LOGGER.info('waiting for the camera to startup..')
            time.sleep(2)
            self.setup_text()
            for _ in self.camera.capture_continuous(buffer, format='jpeg', use_video_port=False, burst=True):
                start = time.time()
                image_data = buffer.getvalue()
                yield image_data
                buffer.seek(0)
                buffer.truncate()
                duration = time.time() - start
                time.sleep(max(cycle_duration_s - duration, 0))
                self.setup_text()
        except Exception as e:
            print('something went wrong', e)
            traceback.print_exc()
        finally:
            self.camera.close()

