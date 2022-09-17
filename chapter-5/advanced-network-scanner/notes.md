# Ideas for Extending the Network Scanner

- Add MAC Vendor lookup
- Use Deauth to force a client to reconnect to the network, so you get the DHCP request
- Add a new column to the dataframe for the ports that are open.
- Add Latency to the dataframe, with the help of the `timeit` module, you can get the time it takes to receive the ICMP reply packet.
- ARP Spoof all detected devices to monitor the entire traffic.
- Use colorama to color the output, so you can easily distinguish the gateway, your device, and other devices.
- https://stackoverflow.com/questions/65410481/filenotfounderror-errno-2-no-such-file-or-directory-bliblibc-a

# Main features of the Advanced Network Scanner

- Automatically detect the network subnet and mask.
- Passively sniffing for packets
- The ability to IP scan any online IP address range
- UDP scanning
- ICMP scanning
- DHCP Listening

# General Notes

- You can uncomment the prints, even though you should use logging in a large program like that instead of simple prints