package org.ledalarmapi.ledalarmapicontrol;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.Switch;
import android.widget.CompoundButton;
import android.widget.Toast;

import org.jetbrains.annotations.NotNull;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.time.Instant;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import java.util.Base64;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.FormBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {

    private Switch switchRed, switchBlue, switchGreen, switchWhite, switchPurple, switchYellow, switchCyan, switchOrange;
    private EditText etServerUrl, etApikey;
    private final String CHANNEL_ID = "LedAlarmControl1";
    private final String SETTING_NAME_SERVER_BASE_URL = "serverbaseurl";
    private final String SETTING_NAME_APIKEY= "apikey";
    private OkHttpClient okHttpClient;
    //private boolean initialSetup = false;
    public final String APIURIPREFIX = "/api/v1/";
    private final int TIMESLOT_LENGTH = 2;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        etServerUrl = (EditText) findViewById(R.id.editTextServerUrl);
        etApikey = (EditText) findViewById(R.id.editTextApikey);

        // read settings
        SharedPreferences preferences = this.getSharedPreferences(CHANNEL_ID, Context.MODE_PRIVATE);
        etServerUrl.setText(preferences.getString(SETTING_NAME_SERVER_BASE_URL, "http://"));
        etApikey.setText(preferences.getString(SETTING_NAME_APIKEY, ""));

        //this.createNotificationChannel();
        switchRed = (Switch) findViewById(R.id.switchLed0);
        switchBlue = (Switch) findViewById(R.id.switchLed1);
        switchWhite = (Switch) findViewById(R.id.switchLed2);
        switchGreen = (Switch) findViewById(R.id.switchLed3);
        switchPurple = (Switch) findViewById(R.id.switchLed4);
        switchYellow = (Switch) findViewById(R.id.switchLed5);
        switchCyan = (Switch) findViewById(R.id.switchLed6);
        switchOrange = (Switch) findViewById(R.id.switchLed7);

        this.okHttpClient = new OkHttpClient();
        // Set all switches initial status.
        Request requestStatusLeds = new Request.Builder().url(this.constructUrlApiServer("statusleds")).build();
        okHttpClient.newCall(requestStatusLeds).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                call.cancel();
            }

            @Override
            public void onResponse(Call call, Response responseStatusLeds) throws IOException {
                final String jsonResponse = responseStatusLeds.body().string();
                MainActivity.this.runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            JSONObject jsonObj = new JSONObject(jsonResponse);
                            org.json.JSONArray ledsStatus = jsonObj.getJSONArray("leds");
                            switchRed.setChecked(ledsStatus.getBoolean(0));
                            switchBlue.setChecked(ledsStatus.getBoolean(1));
                            switchWhite.setChecked(ledsStatus.getBoolean(2));
                            switchGreen.setChecked(ledsStatus.getBoolean(3));
                            switchPurple.setChecked(ledsStatus.getBoolean(4));
                            switchYellow.setChecked(ledsStatus.getBoolean(5));
                            switchCyan.setChecked(ledsStatus.getBoolean(6));
                            switchOrange.setChecked(ledsStatus.getBoolean(7));
                        } catch (JSONException e) {
                            e.printStackTrace();
                        }
                    }
                });
            }
        });

        View.OnFocusChangeListener onFocusChangeListener = new View.OnFocusChangeListener()
        {
            @Override
            public void onFocusChange(View v, boolean hasFocus)
            {
                if (!hasFocus) {
                    Toast.makeText(MainActivity.this,
                            "Storing settings.",
                            Toast.LENGTH_LONG).show();
                    SharedPreferences preferences = getSharedPreferences(CHANNEL_ID, Context.MODE_PRIVATE);
                    SharedPreferences.Editor editor = preferences.edit();
                    editor.putString(SETTING_NAME_SERVER_BASE_URL, etServerUrl.getText().toString());
                    editor.putString(SETTING_NAME_APIKEY, etApikey.getText().toString());
                    editor.commit();
                }
            }
        };

        CompoundButton.OnCheckedChangeListener onCheckedChangeListener = new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                int lednr = (int) buttonView.getTag();
                if (isChecked) {
                    Toast.makeText(MainActivity.this,
                            String.format("Led %d on.", lednr),
                            Toast.LENGTH_LONG).show();
                    setLedAction("ledon", lednr);
                } else {
                    Toast.makeText(MainActivity.this,
                        String.format("Led %d off.", lednr),
                            Toast.LENGTH_LONG).show();
                    setLedAction("ledoff", lednr);
                }
            }
        };

        // Assign onchecked to all switches.
        switchRed.setTag(0);
        switchRed.setOnCheckedChangeListener(onCheckedChangeListener);
        switchBlue.setTag(1);
        switchBlue.setOnCheckedChangeListener(onCheckedChangeListener);
        switchWhite.setTag(2);
        switchWhite.setOnCheckedChangeListener(onCheckedChangeListener);
        switchGreen.setTag(3);
        switchGreen.setOnCheckedChangeListener(onCheckedChangeListener);
        switchPurple.setTag(4);
        switchPurple.setOnCheckedChangeListener(onCheckedChangeListener);
        switchYellow.setTag(5);
        switchYellow.setOnCheckedChangeListener(onCheckedChangeListener);
        switchCyan.setTag(6);
        switchCyan.setOnCheckedChangeListener(onCheckedChangeListener);
        switchOrange.setTag(7);
        switchOrange.setOnCheckedChangeListener(onCheckedChangeListener);

        // assign editText fields
        etServerUrl.setOnFocusChangeListener(onFocusChangeListener);
        etApikey.setOnFocusChangeListener(onFocusChangeListener);
    }

    /**
     *
     * @param action
     * @return String
     */
    private String constructUrlApiServer(String action) {
        EditText etServerUrl = (EditText) findViewById(R.id.editTextServerUrl);
        StringBuilder sbApiUrlStatusLeds = new StringBuilder(etServerUrl.getText().toString());
        sbApiUrlStatusLeds.append(APIURIPREFIX);
        return sbApiUrlStatusLeds.append(action).toString();
    }

    /**
     *
     * @param action
     * @param lednr
     */
    public void setLedAction(String action, int lednr) {
        RequestBody formBody = new FormBody.Builder().add("lednr", String.valueOf(lednr)).build();
        Instant instantTimeStamp = Instant.now();
        long ts = instantTimeStamp.getEpochSecond();
        long ts_slot = ts - (ts % TIMESLOT_LENGTH);
        String msg = action + ts_slot;
        EditText etApiKey = (EditText) findViewById(R.id.editTextApikey);
        byte[] hmacSha256 = HMAC.hmac256(etApiKey.getText().toString(), msg);
        String apiToken = Base64.getEncoder().encodeToString(hmacSha256);
        Request requestLedOn = new Request.Builder().url(this.constructUrlApiServer(action))
                .post(formBody)
                .addHeader("X-Apikey", apiToken)
                .build();
        okHttpClient.newCall(requestLedOn).enqueue(new Callback() {
            @Override
            public void onResponse(@NotNull Call call, @NotNull Response response) throws IOException {
                Log.d("ledonStatus", "HTTP statuscode " + response.code());
                if (response.code() != 200) {
                    Toast.makeText(MainActivity.this,
                            "Got HTTP status code " + response.code(),
                            Toast.LENGTH_LONG).show();
                }
            }

            @Override
            public void onFailure(@NotNull Call call, @NotNull IOException e) {
                Log.d("ledonStatus", "Connection failure" + e.getMessage());
                Toast.makeText(MainActivity.this,
                        "Connection failure " + e.getMessage(),
                        Toast.LENGTH_LONG).show();
            }
        });
    }
}