#!/usr/bin/env python3
# -*- coding: ascii -*-
import sys
# pylint: disable=C0321
if sys.version_info.major < 3: sys.exit('Python version 2(or lower) is not supported.')

import pycurl
import base64
import hashlib
import time
import getopt
import hmac
from io import BytesIO
from configparser import ConfigParser


if len(sys.argv) < 2:
    sys.exit('led api action argument missing.')
api_action = str(sys.argv[1])
if api_action != 'ledon' and api_action != 'ledoff' and api_action != 'statusleds' and api_action != 'resetleds' and api_action != 'testping':
    sys.exit('Unknown action provided. Valid actions are: testping, statusleds, resetleds, ledon and ledoff.')
lednumber = None
if api_action != 'testping' and api_action != 'statusleds' and api_action != 'resetleds':
    if len(sys.argv) < 3:
        sys.exit('lednr argument missing.')
    lednumber = str(sys.argv[2])
api_key = ''
api_host = ''
api_port = ''
config = ConfigParser()
config.read('ledalarmapiclient.conf')
for sect in config.sections():
    if sect != 'client':
        continue
    for key, value in config.items(sect):
        if key == 'apikey':
            api_key = value
        elif key == 'host':
            api_host = value
        elif key == 'port':
            api_port = value
SCRIPT_USERAGENT = 'LedAlarmApiClient/1.2'
TIMESLOT_LENGTH = 2
MAXTIMEDRIFFT = 16
ts = time.time()
if TIMESLOT_LENGTH >= 1:
    ts = int(ts)
ts_slot = ts - (ts % TIMESLOT_LENGTH)
msg = api_action + str(ts_slot)
h = hmac.new(api_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256)
apikey_digest = h.digest()
apikey_token_b64 = base64.b64encode(apikey_digest).decode("utf-8")
url = 'http://' + api_host + ':' + api_port + '/api/v1/' + api_action
buff_resp_data = BytesIO()
c = pycurl.Curl()
c.setopt(c.URL, url)
c.setopt(c.USERAGENT, SCRIPT_USERAGENT)
headers = []
headers.append('X-Apikey: ' + apikey_token_b64)
c.setopt(pycurl.HTTPHEADER, headers)
c.setopt(pycurl.FOLLOWLOCATION, 0)
c.setopt(pycurl.TIMEOUT_MS, 8000)
c.setopt(pycurl.HEADER, 1)
if api_action != "statusleds" and api_action != "testping":
    c.setopt(pycurl.POST, 1)
if lednumber != None:
    c.setopt(pycurl.POSTFIELDS, 'lednr=' + lednumber)
c.setopt(pycurl.WRITEDATA, buff_resp_data)
c.perform()
statuscode = c.getinfo(pycurl.RESPONSE_CODE)
header_size = c.getinfo(pycurl.HEADER_SIZE)
c.close()
if statuscode != 200:
    sys.exit("Error led-alarm-api server returned HTTP status: %d " % statuscode)

# Get the x-signature and x-server-nonce http header from the response and validate it.
# To figure out if the response is really coming from the server that knowns our apikey and is still valid.
resp_data = buff_resp_data.getvalue().decode('utf-8')
resp_headers = resp_data[:header_size]
msg = resp_data[header_size:]
resp_headers_arr = resp_headers.split("\r\n", 1000)
resp_signature = ''
for line in resp_headers_arr:
    if len(line) == 0:
        continue
    line_parts = line.split(':', 3)
    if len(line_parts) != 2:
        continue
    if line_parts[0] == 'x-server-nonce':
        nonce_server = line_parts[1].strip()
    elif line_parts[0] == 'x-signature':
        actual_signature_b64 = line_parts[1].strip()

def generate_signature(apikey_token_b64, ts_slot, msg, statuscode, nonce_server):
    signature_data = "%s%d%s%d%s" % (apikey_token_b64, ts_slot, msg, statuscode, nonce_server)
    expected_signature = hmac.new(api_key.encode("utf-8"), signature_data.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(expected_signature).decode("utf-8")

expected_signature_b64 = generate_signature(apikey_token_b64, ts_slot, msg, statuscode, nonce_server)
if expected_signature_b64 != actual_signature_b64:
    maxtimeslotsdrifft = int(MAXTIMEDRIFFT / TIMESLOT_LENGTH)
    validsignature = False
    for i in range(1, maxtimeslotsdrifft, 1):
        ts = i * TIMESLOT_LENGTH + ts_slot
        expected_signature_b64 = generate_signature(apikey_token_b64, ts, msg, statuscode, nonce_server)
        if expected_signature_b64 == actual_signature_b64:
            validsignature = True
            break
        ts = -i * TIMESLOT_LENGTH + ts_slot
        expected_signature_b64 = generate_signature(apikey_token_b64, ts, msg, statuscode, nonce_server)
        if expected_signature_b64 == actual_signature_b64:
            validsignature = True
            break
    if not validsignature:
        sys.exit("Security warning: Could not validate the signature from the server!\r\n\
 The response may be tampered and cannot be trusted or the clock is too way off.")
if api_action == 'testping' or api_action == 'statusleds':
    print("Server signature valid.")
    print(resp_data)
