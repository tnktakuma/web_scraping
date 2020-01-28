import os
import requests

from slack_api import Slack, MY_CID


global_ip = None
filename = os.path.join(os.environ['HOME'], '.global_ip')
if os.path.exists(filename):
    with open(filename, 'r') as f:
        global_ip = f.read()
response = requests.get('http://inet-ip.info/ip')
ip_address = response.text
if ip_address != global_ip:
    Slack().post_message(MY_CID, ip_address)
    with open(filename, 'w') as f:
        f.write(ip_address)
