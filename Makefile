sudo apt-get install libasound2 libasound2-dev
sudo pip install pyalsaaudio
sudo apt-get install python-numpy python-scipy python-matplotlib ipython ipython-notebook python-pandas python-sympy python-nose
sudo pip install aubio
git clone https://github.com/jgarff/rpi_ws281x.git libs/neopixel-py
cd libs/neopixel-py
scons
cd python
sudo python setup.py install
cd ../../../
sudo apt-get install build-essential python-dev git scons swig
