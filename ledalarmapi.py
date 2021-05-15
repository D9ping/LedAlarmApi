#!/usr/bin/env python3
# -*- coding: ascii -*-
import sys

# pylint: disable=C0321
if sys.version_info.major < 3: sys.exit('Python version 2(or lower) is not supported.')
from flask import Flask
from flask import request
from blinkt import set_pixel, set_brightness, show, clear
from configparser import ConfigParser
import argparse
import time
import threading
import hashlib
import base64
import hmac
import os
import random
import string


class localFlask(Flask):
    def process_response(self, response):
       response.headers['Server'] = 'LedAlarmApi/1.0'
       response.headers['Content-Type'] = 'text/plain'
       return(response)

apiapp = localFlask(__name__)
apikeys = { }
# FIXME: make thread safe
leds = { 'led0': False, 'led1': False, 'led2': False, 'led3': False,
         'led4': False, 'led5': False, 'led6': False, 'led7': False }
TIMESLOT_LENGTH = 2
MAXTIMEDRIFTSECONDS = 60
NONCE_LEN_SERVER = 15

@apiapp.errorhandler(404)
def errorpage_notfound(error):
    """
    A non existing page is requested.
    Return E404 as error message.
    """
    return 'E404', 404

@apiapp.errorhandler(405)
def errorpage_wrongmethod(error):
    """
    A api endpoint with the wrong HTTP method is request.
    Return E405 as error message.
    """
    return 'E405', 405

@apiapp.route('/api/v1/testping', methods = ['GET'])
def ping():
    """
    Method to test the api. Reponsed to useragent with testpong
     if everything succeeded.
    """
    apikey_token = request.headers.get('x-apikey')
    ip = request.remote_addr
    msg = 'E401'
    statuscode = 401
    sigheaders = {}
    if check_authentication(apikey_token, ip, 'testping', False):
        msg = 'testpong'
        statuscode = 200
        sigheaders = generate_signature(apikey_token, ip, msg, statuscode)
    return msg, statuscode, sigheaders

@apiapp.route('/api/v1/ledon', methods = ['POST'])
def ledon():
    """
    Turn a led on.
    """
    apikey_token = request.headers.get('x-apikey')
    ip = request.remote_addr
    if not check_authentication(apikey_token, ip, 'ledon', False):
        return 'E401', 401
    statuscode = 400
    if 'lednr' not in request.form:
        msg = 'lednr missing'
        headers = generate_signature(apikey_token, ip, msg, statuscode)
        return msg, 400, headers
    try:
        lednr = int(request.form.get('lednr', 7))
    except:
        msg = 'lednr invalid'
        headers = generate_signature(apikey_token, ip, msg, statuscode)
        return msg, statuscode, headers
    global leds
    leds['led'+str(lednr)] = True
    statuscode = 200
    msg = 'ok'
    headers = generate_signature(apikey_token, ip, msg, statuscode)
    return msg, statuscode, headers

@apiapp.route('/api/v1/ledoff', methods = ['POST'])
def ledoff():
    """
    Turn a led off.
    """
    apikey_token = request.headers.get('x-apikey')
    ip = request.remote_addr
    if not check_authentication(apikey_token, ip, 'ledoff', False):
        return 'E401', 401
    statuscode = 400
    if 'lednr' not in request.form:
        msg = 'lednr missing'
        headers = generate_signature(apikey_token, ip, msg, statuscode)
        return msg, 400, headers
    try:
        lednr = int(request.form.get('lednr', 7))
    except:
        msg = 'lednr invalid'
        headers = generate_signature(apikey_token, ip, msg, statuscode)
        return msg, statuscode, headers
    global leds
    leds['led'+str(lednr)] = False
    statuscode = 200
    msg = 'ok'
    headers = generate_signature(apikey_token, ip, msg, statuscode)
    return msg, statuscode, headers

@apiapp.route('/api/v1/statusleds', methods = ['GET'])
def statusleds():
    """
    Request statuses of all leds. Only with successful authentication a server
     signature is provided in the response.
    """
    global leds
    status_json = "{\"leds\":["
    firstelm = True
    for lednr in leds:
        if not firstelm:
            status_json += ","
        firstelm = False
        if leds[lednr]:
            status_json += "true"
        else:
            status_json += "false"
    status_json += "]}"
    statuscode = 200
    headers = {}
    ip = request.remote_addr
    apikey_token = request.headers.get('x-apikey')
    if apikey_token is not None:
        if check_authentication(apikey_token, ip, 'statusleds', False):
            headers = generate_signature(apikey_token, ip, status_json, statuscode)
    return status_json, statuscode, headers

@apiapp.route('/api/v1/resetleds', methods = ['POST'])
def resetleds():
    """
    Turn all leds off.
    """
    apikey_token = request.headers.get('x-apikey')
    ip = request.remote_addr
    if not check_authentication(apikey_token, ip, 'resetleds', False):
        return 'E401', 401
    global leds
    for lednr in leds:
        leds[lednr] = False
    statuscode = 200
    msg = 'ok'
    headers = generate_signature(apikey_token, ip, msg, statuscode)
    return msg, statuscode, headers

def check_authentication(apikey, ip, api_action, verbose=False):
    """
    Check authentication hmac apikey.
    Should not be vulnerable to replay attacks.
    """
    ts = time.time()
    ts_slot = ts - (ts % TIMESLOT_LENGTH)
    try:
        expected_apikey = apikeys[ip]['apikey']
    except:
        return False
    try:
        apikey_last_used = apikeys[ip]['lastused']
    except:
        return False
    slotnum_start = int((MAXTIMEDRIFTSECONDS / TIMESLOT_LENGTH) * -1)
    slotnum_end = int(MAXTIMEDRIFTSECONDS / TIMESLOT_LENGTH)
    for i in range(slotnum_start, slotnum_end, 1):
        check_ts_slot = ts_slot - (TIMESLOT_LENGTH * i)
        if verbose:
            print("check_ts_slot = %d" % check_ts_slot)
        msg = api_action + str(check_ts_slot)
        h = hmac.new(expected_apikey.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256)
        apikey_digest = h.digest()
        apikey_digest_b64 = base64.b64encode(apikey_digest).decode("utf-8")
        if apikey == apikey_digest_b64:
            if apikey_last_used >= ts_slot:
                if verbose:
                    print("apidigest already used, prevent replay attack.")
                return False
            apikeys[ip]['lastused'] = ts_slot
            if verbose:
                print("Authenticed succesfull.")
            return True
    return False

def generate_signature(apikey_token, ip, msg, statuscode):
    """
    Generate the x-signature and x-server-nonce http header to prove the response
     message was from the server that is knowing the client apikey.
    Must be called after check_authentication and when not false.
    """
    apikey = apikeys[ip]['apikey']
    ts = time.time()
    ts_slot = ts - (ts % TIMESLOT_LENGTH)
    nonce_server = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(NONCE_LEN_SERVER))
    signature_data = "%s%d%s%d%s" % (apikey_token, ts_slot, msg, statuscode, nonce_server)
    h = hmac.new(apikey.encode("utf-8"), signature_data.encode("utf-8"), hashlib.sha256)
    signature_digest_b64 = base64.b64encode(h.digest()).decode("utf-8")
    return {'x-server-nonce': nonce_server, 'x-signature': signature_digest_b64}

def show_led():
    """
    Thread that updates leds.
    """
    update_interval = 2
    while True:
        clear()
        if leds['led0']:
            # red
            set_pixel(0, 255, 0, 0, 0.3)
        if leds['led1']:
            # blue
            set_pixel(1, 0, 0, 255, 0.3)
        if leds['led2']:
            # white
            set_pixel(2, 255, 255, 255, 0.3)
        if leds['led3']:
            # green
            set_pixel(3, 0, 255, 0, 0.3)
        if leds['led4']:
            # purple
            set_pixel(4, 128, 0, 128, 0.3)
        if leds['led5']:
            # yellow
            set_pixel(5, 255, 255, 51, 0.3)
        if leds['led6']:
            # cyan
            set_pixel(6, 80, 255, 255, 0.3)
        if leds['led7']:
            # orange
            set_pixel(7, 255, 80, 0, 0.3)
        show()
        time.sleep(update_interval)

if __name__ == '__main__':
    api_port = '18339'
    api_listenaddress = '0.0.0.0'
    parser = argparse.ArgumentParser(description='Leds REST api for the Blinkt hat.')
    parser.add_argument('configfile', nargs='?', type=str, 
                        default='/etc/ledalarmapi.conf',
                        help="""Path to the ledalarmapi configuration file. If 
 not provided /etc/ledalarmapi.conf is used.""")
    parser.add_argument('-P', '--port', metavar=api_port, type=int, default=None,
                        help="""The port number to use.""")
    parser.add_argument('-L', '--listenaddress', metavar=api_listenaddress,
                        type=str, default=None,
                        help="""Address to listen the HTTP REST server on. 
 By default uses 0.0.0.0 for all IPv4 network interfaces.""")
    args = parser.parse_args()
    if os.path.exists(args.configfile):
        config = ConfigParser()
        config.read(args.configfile)
        for sect in config.sections():
            if sect == 'apikeys':
                for ipaddr, apikeystr in config.items(sect):
                    apikeys[ipaddr] = {}
                    apikeys[ipaddr]['apikey'] = apikeystr
                    apikeys[ipaddr]['lastused'] = 0
            elif sect == 'server':
                for serverkey, servervalue in config.items(sect):
                    lc_serverkey = serverkey.lower()
                    if lc_serverkey == 'port':
                        api_port = servervalue
                    elif lc_serverkey == 'listenaddress':
                        api_listenaddress = servervalue
    elif args.port is None or args.listenaddress is None:
        sys.exit('Error: the %s configuration file could not be found.' % 
                 args.configfile)
    if MAXTIMEDRIFTSECONDS < TIMESLOT_LENGTH:
        sys.exit('MAXTIMEDRIFTSECONDS must be bigger then TIMESLOT_LENGTH.')
    # Override configuration with command-line arguments
    if args.port is not None:
        api_port = str(args.port)
    if args.listenaddress is not None:
        api_listenaddress = args.listenaddress
    thread_show_led = threading.Thread(target=show_led)
    thread_show_led.start()
    #WSGIRequestHandler.protocol_version = "HTTP/1.1"
    apiapp.run(debug=False, port=api_port, host=api_listenaddress)
    thread_show_led.join()

