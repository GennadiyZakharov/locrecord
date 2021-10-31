# LocRecord
This is just a simple GUI to VLC video player
for recording video from IP cameras

It allows user to select desired camera, set recording duration and 
file name to save video.
It also supports automatic adding of current date/time to video file name.

The camera parameters are located in `cameras.ini` file.

## Requirements
- PyQt 5

## Installation
Install PyQt5 using any convenient way: 
- pip: `pip install pyqt5`
- conda: `conda install pyqt5`
- Distributive package manager:
- - Ubuntu/Debian: `sudo apt install python3-pyqt5`

Then download the repository content, unpack (if needed) and run
`locrecord.py`
