#!/usr/bin/env python3
# -*- coding: ascii -*-
import pycurl
import base64
import hashlib
import time
import getopt
import sys
import hmac

# pylint: disable=C0321
if sys.version_info.major < 3: sys.exit('Python version 2(or lower) is not supported.')

if len(sys.argv) != 2:
    sys.exit('lednr argument missing.')

APIKEY = 'changethis!'
API_ACTION = 'ledoff'
SCRIPT_USERAGENT = 'TurnOffLedAlarmScript/1.0'
TIMESLOT_LENGTH = 2

ts = time.time()
ts_slot = ts - (ts % TIMESLOT_LENGTH)
msg = API_ACTION + str(ts_slot)
h = hmac.new(APIKEY.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256)
apikey_digest = h.digest()
apikey_digest_b64 = base64.b64encode(apikey_digest).decode("utf-8")

c = pycurl.Curl()
c.setopt(c.URL, 'http://127.0.0.1:18339/api/v1/' + API_ACTION)
c.setopt(c.USERAGENT, SCRIPT_USERAGENT)
headers = []
headers.append("X-Apikey: " + apikey_digest_b64)
c.setopt(pycurl.HTTPHEADER, headers)
c.setopt(pycurl.FOLLOWLOCATION, 0)
c.setopt(pycurl.TIMEOUT_MS, 9000)
c.setopt(pycurl.POST, 1)
c.setopt(pycurl.POSTFIELDS, 'lednr=' + str(sys.argv[1]))
c.perform()
status_code_on = c.getinfo(pycurl.RESPONSE_CODE)
c.close()
if status_code_on != 200:
    print("Error led-alarm-api server returned HTTP status: %d " % status_code_on)
