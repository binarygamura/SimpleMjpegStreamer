#!/usr/bin/env python3

import traceback
from ImageSource import ImageSource
from picamera import PiCamera, Color
from MjpegHttpServer import MjpegHttpServer
import logging, logging.config, sys

if __name__ == '__main__':
    # use logging configration
    logging.config.fileConfig('logging.conf')

    LOGGER = logging.getLogger(__name__)
    image_source = None
    mjpg_http_server = None
    try:
        print('Simple Mjpg Streamer\n====================')

        # initialize the raspberry pi camera
        fps = 30
        resolution = (1024, 768)
        picamera = PiCamera(resolution=resolution, framerate=fps)
        picamera.resolution = resolution
        picamera.annotate_background = Color('black')

        # start the webserver
        LOGGER.info('setting up environment')
        mjpg_http_server = MjpegHttpServer(socket_port=8088, bind_address='0.0.0.0')
        mjpg_http_server.start()
        LOGGER.info('started webserver')

        # initialze the stuff processing the images from the mjpg
        image_source = ImageSource(**{'fps': fps, 'camera': picamera})
        LOGGER.info('started webcam process')
        mjpg_http_server.start_polling_images(image_source)

    except KeyboardInterrupt as e:
        LOGGER.info('got ctrl+c from user')
    except Exception as e:
        LOGGER.exception('caught an exception')
        traceback.print_exc()
    finally:
        LOGGER.info('have a nice day')
        if mjpg_http_server is not None:
            mjpg_http_server.close()
