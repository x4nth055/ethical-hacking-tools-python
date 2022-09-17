pip3 install pandas scapy

sudo ifconfig wlan0 down
sudo iwconfig wlan0 mode monitor

iwconfig wlan0mon channel 2

python wifi_scanner.py wlan0mon