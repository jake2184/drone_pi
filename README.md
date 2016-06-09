#Raspberry Pi Drone Software

This software is designed for running on a Raspberry Pi connected to the internet and a Pixhack autopilot, collecting data and communicating with both. It is written in pure Python.

Once an updated version of Raspbian is installed, the following installation steps must also be followed.

1. Install dependencies. All commands should be done as root, or prefixed with sudo. Should either of the last two steps fail, ffmpeg must be installed via a different method such as source compilation.

```
apt-get install -y libopencore-armnb-dev libopencore-armwb-dev python-pyaudio python-dev
apt-get remove python-pip
easy_install pip
pip install ibmiotf pymavlink grovepi websocket-client
wget https://github.com/ccrisan/motioneye/wiki/precompiled/ffmpeg_2.8.3.git325b593-1_armhf.deb
dpkg -i ffmpeg_2.8.3.git325b593-1_armhf.deb
```

2. Download source code with `git clone https://github.com/jake2184/drone_pi.git`, and cd into directory

3. Run system with:
`python python/main.py <hostname> <username> <password> <dronename> <dummyDirection>`
Dummy direction can be replaced with 1 if its use is not desired.