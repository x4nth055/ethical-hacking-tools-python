import ipinfo
import sys

# get the ip address from the command line
try:
    ip_address = sys.argv[1]
except IndexError:
    ip_address = None

# access token for ipinfo.io, pur yours here
access_token = '7119254625:AAFwPseUa3d0kJIFTUX_Q5ApiqO5QWnKeMY'
# create a client object with the access token
handler = ipinfo.getHandler(access_token)
# get the ip info
details = handler.getDetails(ip_address)
# print the ip info
for key, value in details.all.items():
    print(f"{key}: {value}")
