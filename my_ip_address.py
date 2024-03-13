#!/usr/bin/env python

# /********************************************************************
# Filename: my_ip_address.py
# Author: AHN
# Creation Date: Oct, 2020
# **********************************************************************/
#
# Occasionally ping the GUI back end to tell them what the server IP is.
# This eliminates problems if the server IP changes.
# Runs as systemctl service /etc/systemd/system/my_ip_address.service .
#

import sys, os, time

while(1):
    tt = os.popen( 'curl "https://katagui-club.herokuapp.com/server_ip?pwd=%s"' % sys.argv[1])
    tt.read()
    tt.close()
    time.sleep( 60)
