var waitRequired = false;
var waitMs = 2000;
var requestTimeout = 8000;
var ledbuttons = document.querySelectorAll('.ledswitch');

function setInitLedsOnStatus() {
    var xmlhttpstatus = new XMLHttpRequest();
    xmlhttpstatus.open('GET', '/status.php', true);
    xmlhttpstatus.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
    xmlhttpstatus.timeout = requestTimeout;
    xmlhttpstatus.onreadystatechange = function() {
        if (xmlhttpstatus.status == 200 && xmlhttpstatus.readyState == 4) {
            var status = JSON.parse(xmlhttpstatus.responseText);
            for (var i = 0; i < status.leds.length; ++i) {
                ledbuttons.forEach(function(btn, idx) {
                    if (btn.getAttribute('data-lednr') == i) {
                        if (status.leds[i]) {
                            btn.setAttribute('data-ledon', '1');
                            btn.src = 'switch_on.png';
                            document.getElementById('pageBody').style.backgroundColor = '#fff';
                        } else {
                            btn.setAttribute('data-ledon', '0');
                            btn.src = 'switch_off.png';
                        }

                        return;
                    }
                });
            }
        } 
    }

    xmlhttpstatus.send();
}

function dowait() {
    waitRequired = true;
    ledbuttons.forEach(function(b, idx) {
        b.style.cursor = 'not-allowed';
    });
    setTimeout(function() {
        waitRequired = false;
        ledbuttons.forEach(function(b2, idx) {
            b2.style.cursor = 'pointer';
        });
    }, waitMs);
}


setInitLedsOnStatus();
//dowait();

ledbuttons.forEach(function(button, idx) {
    button.addEventListener('click', function() {
        if (waitRequired) {
            return;
        }

        button.src = 'switch_undefined.png';
        let ledon = false;
        if (button.getAttribute('data-ledon') === '1') {
            ledon = true;
        }

        var xmlhttp = new XMLHttpRequest();
        if (ledon) {
            xmlhttp.open('POST', '/turnoff.php', true);
        } else {
            xmlhttp.open('POST', '/turnon.php', true);
        }

        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4) {
                if (xmlhttp.status != 200) {
                    if (ledon) {
                        button.src = 'switch_on.png';
                    } else {
                        button.src = 'switch_off.png';
                    }

                    return;
                }

                if (ledon) {
                    button.setAttribute('data-ledon', '0');
                    button.src = 'switch_off.png';
                    document.getElementById('pageBody').style.backgroundColor = '#000';
                } else {
                    button.setAttribute('data-ledon', '1');
                    button.src = 'switch_on.png';
                    document.getElementById('pageBody').style.backgroundColor = '#fff'
                }

                dowait();
            }
        }

        xmlhttp.timeout = requestTimeout;
        xmlhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
        xmlhttp.send('l='+button.getAttribute('data-lednr'));
        document.getElementById('pageBody').style.backgroundColor = '#999';
    });
});
