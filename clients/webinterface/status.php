<?php
require_once('config.php');
if (strtoupper($_SERVER['REQUEST_METHOD']) !== 'GET') {
    http_response_code(400);
    exit('GET method required.');
}

$apiAction = 'statusleds';
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, 'http://'.APIHOST.':'.APIPORT.'/api/v1/'.$apiAction);
$headers = [
  'x-apikey: '.$apikeyDigest
];

curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$serverResponse = curl_exec($ch);
$statusCode = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
http_response_code($statusCode);
header('X-Content-Type-Options: nosniff');
header('Content-Type: application/json');
echo $serverResponse;
