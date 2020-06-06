#!/usr/bin/env python3

import traceback
from ImageSource import ImageSource
from picamera import PiCamera, Color
from MjpegHttpServer import MjpegHttpServer
import argparse, logging, logging.config, sys

if __name__ == '__main__':
    image_source = None
    mjpg_http_server = None
    
    # use logging configration
    logging.config.fileConfig('logging.conf')

    LOGGER = logging.getLogger(__name__)    

    # create argument parser
    parser = argparse.ArgumentParser(
        description='simple mjpeg over http streaming server',
        epilog='feel free to open an issue at https://github.com/binarygamura/SimpleMjpegStreamer if you encounter any issues of errors arise.')
    parser.add_argument('-x', '--width', dest='width', default=1024, type=int, help='horizontal camera resolution (default: %(default)s)')
    parser.add_argument('-y', '--height', dest='height', default=768, type=int, help='vertical camera resolution (default: %(default)s)')
    parser.add_argument('-f', '--fps', dest='fps', default=30, type=int, help='target fps for the camera (default: %(default)s)')

    # parse arguments from argv 
    arguments = parser.parse_args()
    try:
        print('Simple Mjpg Streamer\n====================')

        # initialize the raspberry pi camera
        resolution = (arguments.width, arguments.height)
        picamera = PiCamera(resolution=resolution, framerate=arguments.fps)
        picamera.resolution = resolution
        picamera.annotate_background = Color('black')
        LOGGER.info('camera initialized with x={},y={},fps={}'.format(arguments.width, arguments.height, arguments.fps))

        # start the webserver
        LOGGER.info('setting up environment')
        mjpg_http_server = MjpegHttpServer(socket_port=8088, bind_address='0.0.0.0')
        mjpg_http_server.start()
        LOGGER.info('started webserver')

        # initialze the stuff processing the images from the mjpg
        image_source = ImageSource(**{'fps': arguments.fps, 'camera': picamera})
        LOGGER.info('started webcam process')
        mjpg_http_server.start_polling_images(image_source)

    except KeyboardInterrupt as e:
        LOGGER.info('got ctrl+c from user')
    except Exception as e:
        LOGGER.exception('caught an exception')
        traceback.print_exc()
    except ArgumentError as e:
        LOGGER.exception(e.message)
    finally:
        LOGGER.info('have a nice day')
        if mjpg_http_server is not None:
            mjpg_http_server.close()
