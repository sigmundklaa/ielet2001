
## Installation

As seen in the [official guide](https://www.raspberrypi.com/documentation/accessories/camera.html#preparing-the-software), the Raspberry Pi camera requires both libcamera and Picamera2 installed.
This should already be pre-installed with the OS, however if not it can be installed following the above guide.

Installation of the required Python dependencies can be done with:
```
pip install -r requirements.txt
```

To run the supernode it is also required to use a config file. This file can
be created by running `cp super-sample.yml super.yml` in the root directory
of the repository. This file is read at program start, so to change a value
just change it in the config and restart the program.
