import os
import sys

from slack_api import Slack, MY_CID


def main(ip_address: str):
    global_ip = None
    filename = os.path.join(os.environ["HOME"], ".global_ip")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            global_ip = f.read()
    if ip_address != global_ip:
        Slack().post_message(MY_CID, ip_address)
        with open(filename, "w") as f:
            f.write(ip_address)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        raise ValueError("Usage: python " + sys.argv[0] + " $(curl ifconfig.io -4)")
