package org.ledalarmapi.ledalarmapicontrol;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

// from: https://diego-pacheco.blogspot.com/2020/05/hmac-in-java.html
public class HMAC {
    public static byte[] hmac256(String secretKey,String message){
        try{
            return hmac256(secretKey.getBytes("UTF-8"), message.getBytes("UTF-8"));
        } catch (Exception e) {
            throw new RuntimeException("Failed to generate HMACSHA256 hash", e);
        }
    }

    public static byte[] hmac256(byte[] secretKey,byte[] message){
        byte[] hmac256 = null;
        try{
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec sks = new SecretKeySpec(secretKey, "HmacSHA256");
            mac.init(sks);
            hmac256 = mac.doFinal(message);
            return hmac256;
        } catch (Exception e) {
            throw new RuntimeException("Failed to generate HMACSHA256 hash");
        }
    }
}
