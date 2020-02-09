# SimpleMjpegStreamer

SimpleMjpegStreamer is a very simple http server written in Python 3 for the Raspberry Pi capable of streaming images from
a camera as a mjpeg-stream to multiple clients. This server is more or less just a proof-of-concept and shouldn't be used
in productive environments. Under the hood it starts a thread for every incoming connection, so don't
expect a well scaling app. Also keep in mind, that this projects lacks any kind of authorization and authentication 
methods. 

I developed this when I planned to observe my 3D printers doing their work in my cellar rooms. Why not using a Raspberry Pi
and its camera to monitor while i am sitting on my living room watching the video stream on my mobile? I found many
really cool streaming solutions but all I wanted is a very simple mjpeg-streamer with a focus on easy and fast installation
without the hassle of installing and configuring many things.

## Installation and Usage

1. Make sure you have python 3 installed. Open a shell and simply check its version with 
  ```bash python -V ``` or 
  ```bash python3 -V ```. If an error comes up or the version shown is below 3.7.2 please install python or update
  your installation. 
2. This project uses depends on the excellent Picamera library. If you don't have it installed, please follow the instructions found 
  [here](https://picamera.readthedocs.io/en/release-1.13/install.html). You can check if it is already installed if 
  ```bash python3 -c "import picamera"``` shows no error message.
3. Download this project using the "Download Zip" button and unpack it in a folder. Or clone this repo using git ```bash git clone <THIS URL>```.
4. Start the server ```bash python3 start-mjpeg-server.py```
5. Enjoy! 

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate if there are any (spoiler: there arne any tests right now).

## License
[MIT](https://choosealicense.com/licenses/mit/)