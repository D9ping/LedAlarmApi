<?php
require_once('config.php');
if (strtoupper($_SERVER['REQUEST_METHOD']) !== 'POST') {
    http_response_code(400);
    exit('POST method required.');
}

if (!isset($_POST['l'])) {
    http_response_code(400);
    exit('l missing.');
}

$lednr = (int)filter_input(INPUT_POST, 'l', FILTER_SANITIZE_NUMBER_INT);
if ($lednr < 0 || $lednr > 7) {
    http_response_code(400);
    exit('l invalid number.');
}

$apiAction = 'ledoff';
date_default_timezone_set("UTC");
$timeSlot = time() - (time() % TIMESLOT_LENGTH);
// Python string of a float adds and .0 to the number!
$msg = $apiAction.$timeSlot.'.0';
$apikeyDigest = base64_encode(hash_hmac('sha256', $msg, APISECRET, true));

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'http://'.APIHOST.':'.APIPORT.'/api/v1/'.$apiAction);
curl_setopt($ch, CURLOPT_POST, 1);
$headers = [
  'x-apikey: '.$apikeyDigest
];

curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_POSTFIELDS, "lednr=".$lednr);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$serverResponse = curl_exec($ch);
$statusCode = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
http_response_code($statusCode);
header('X-Content-Type-Options: nosniff');
header('Content-Type: text/plain');
echo $serverResponse;
