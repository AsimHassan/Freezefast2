#ifndef CONFIGS_H
#define CONFIGS_H
/*****************WiFi Credentials**********************/

#define WIFI_SSID "BSNLFTTH-880"
#define WIFI_PSD "4872962880"
/*****************Server details**********************/

#define SERVER "192.168.3.64"
#define PORT 1234
/*****************Pins**********************/

#define FORWARD_PIN 19
#define REVERSE_PIN 18
#define SLOWDOWN_PIN 5
#define BUZZER_PIN 4
#define OBSTACLE_SENSOR_F_PIN 33
#define OBSTACLE_SENSOR_B_PIN 25
#define LIMIT_SWITCH_F_PIN 27
#define LIMIT_SWITCH_B_PIN 26
/**********************STATION PARAMETERS***********/
#define ROVER_ID "ROVER"

/********************Timings parameters**************/

#define LED_BLINK_DELAY 1000
#define STATUS_UPDATE_DELAY 1000
#define BUZZER_DELAY_REACHED 2000
#define BUZZER_DELAY_STOP 30000
#define BUZZER_DELAY_MOVING 5000
#define BUZZER_PULSE_TIME 500
#define TIME_BETWEEN_UPDATES 1000

#endif
