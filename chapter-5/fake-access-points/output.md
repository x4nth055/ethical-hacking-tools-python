$ apt-get install aircrack-ng

root@rockikz:~# airmon-ng start wlan0

PHY    Interface    Driver     Chipset

phy0   wlan0        ath9k_htc  Atheros Communications, Inc. TP-Link TL-WN821N v3 / TL-WN822N v2 802.11n [Atheros AR7010+AR9287]

               (mac80211 monitor mode vif enabled for [phy0]wlan0 on [phy0]wlan0mon)
               (mac80211 station mode vif disabled for [phy0]wlan0)


$ pip3 install faker scapy

python fake_access_points_forger.py wlan0mon -n 5