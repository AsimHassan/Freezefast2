#include <Arduino.h>
#include <WiFi.h>
#include "PubSubClient.h"
#include "configs.h"

enum NETWORK_STATES_ENUM{
    DISCONNECTED,
    RECONNECTING,
    CONNECTED
};
String networkstatestring[] = {

    "DISCONNECTED",
    "RECONNECTING",
    "CONNECTED"
};

enum JUNCTIION_STATES_ENUM{
    IDLE,
    ROVER_CROSS,
    ROVER_CROSS_INTER,
    ROVER_CROSS2,
    ROVER_HERE,
    ROTATE,
    ROVER_READY_TO_LEAVE,
    ROVER_LEAVING,
    ROVER_LEAVING2,
    ROVER_LEFT,
    JUNCTION_ERROR
};

String statearray[] = {
    "IDLE",
    "ROVER_CROSS",
    "ROVER_CROSS_INTER",
    "ROVER_CROSS2",
    "ROVER_HERE",
    "ROTATE",
    "ROVER_READY_TO_LEAVE",
    "ROVER_LEAVING",
    "ROVER_LEAVING2",
    "ROVER_LEFT",
    "JUNCTION_ERROR"
};
enum current_rotating_states{
    WAIT,
    ENTRY,
    STRAIGHT,
    CROSS,
    ROTATE_CW,
    ROTATE_CCW,
    ROTATING,
    SEND_MESSAGE,
    DONE,
    ERROR_ROTATION
};
String rotating_state_arrray[]={
    "WAIT",
    "ENTRY",
    "STRAIGHT",
    "CROSS",
    "ROTATE_CW",
    "ROTATE_CCW",
    "ROTATING",
    "SEND_MESSAGE",
    "DONE",
    "ERROR_ROTATION"

};

WiFiClient espclient;
PubSubClient mqttclient(espclient);


const char* rovercross_topic        = JUNCTIONID "/cross1";
const char* rovercross2_topic       = JUNCTIONID "/cross2";
const char* crossyes_topic          = JUNCTIONID "/crossyes";
const char* crossno_topic           = JUNCTIONID "/crossno";
const char* direction_topic         = JUNCTIONID "/direction";
const char* destination_topic       = JUNCTIONID "/destination";
const char* buzzer_topic            = JUNCTIONID "/output/buzzer";
const char* rotateccw_topic         = JUNCTIONID "/output/rotateccw";
const char* rotatecw_topic          = JUNCTIONID "/output/rotatecw";
const char* irsensor_topic          = JUNCTIONID "/input/irsensor";
const char* sensorA1_topic          = JUNCTIONID "/input/sensorA1";
const char* sensorA2_topic          = JUNCTIONID "/input/sensorA2";
const char* readytoleave_topic      = JUNCTIONID "/readytoleave";
const char* rotationdone_topic      = JUNCTIONID "/rotationdone";
const char* roverstopppedjunc_topic = JUNCTIONID "/roverstoppedjunction"
const char* junctionstate_topic     = JUNCTIONID "/junctionstate";
const char* rotationstate_topic     = JUNCTIONID "/rotationstate";
const char* rotatein_topic          = JUNCTIONID "/rotate";

const char* emergency_stop          = "emergency";

uint8_t current_junction_state = IDLE;
uint8_t current_rotating_state = ENTRY;
uint8_t current_mqtt_state = DISCONNECTED;
uint8_t current_wifi_state = DISCONNECTED;
uint8_t current_position = STRAIGHT;
uint8_t destination = STRAIGHT;
bool flag_buzz = false;


unsigned pulsetimer0 = 0l;
unsigned buzztimer_moving = 0l;
unsigned long rover_cross1_timer_0;
unsigned long rover_cross2_timer_0;
unsigned long rotation_start_timer_0;


int wifi_state_machine();
int mqtt_state_machine();
int junction_state_machine();
int rotating_state_machine();
int pulse(int time);
void turnAllOutputOff();
void callback(char* topic, byte* payload, unsigned int length);
void send_to_server(uint8_t junction_state,
        uint8_t rotation_state,uint8_t sensorA1,uint8_t sensorA2,
        uint8_t buzzer,uint8_t roverIR);

void setup(){

    pinMode(SENSOR_A1_PIN,INPUT_PULLDOWN);
    pinMode(SENSOR_A2_PIN,INPUT_PULLDOWN);
    pinMode(IR_SENSOR_PIN,INPUT_PULLDOWN);
    pinMode(BUZZER_PIN,OUTPUT);
    pinMode(TURN_CCW_PIN,OUTPUT);
    pinMode(TURN_CW_PIN,OUTPUT);
    mqttclient.setServer(SERVER,PORT);
    mqttclient.setKeepAlive(1);
    mqttclient.setCallback(callback); 
    Serial.begin(115200);

}

void loop(){


}

int junction_state_machine(){

    int IR_sensor = digitalRead(IR_SENSOR_PIN);
    
    switch(current_junction_state){

        case IDLE:
            if (IR_sensor == HIGH){
                rover_cross1_timer_0 = millis();
                mqttclient.publish(rovercross_topic,"Y");
                current_junction_state = ROVER_CROSS;

            }
            break;
        case ROVER_CROSS:
            if (millis()- rover_cross1_timer_0 > 300){

                if(IR_sensor == LOW){
                    current_junction_state = ROVER_CROSS_INTER;
                }
            }
            break;
        case ROVER_CROSS_INTER:
            if (IR_sensor == HIGH){
                mqttclient.publish(rovercross2_topic,"Y");
                current_junction_state = ROVER_CROSS2;
                rover_cross2_timer_0 = millis();
            }
            break;
        case ROVER_CROSS2:
            if(millis() - rover_cross2_timer_0 > 500){
                if (IR_sensor ==HIGH){
                    current_junction_state = ROVER_HERE;
                }
            }
            break;
        case ROVER_HERE:
            if(millis() - rover_cross2_timer_0 > 500 && IR_sensor == HIGH)
            {
                delay(50);
            }
            // if(millis()-rover_cross2_timer_0 > 1000 && IR_Sensor == LOW){
            //     JUNCTION_STATE = ERROR_ROTATION;
            // }
            break;
        case ROTATE:
            //Serial.print(".");
            delay(10);
            if(current_rotating_state == DONE){
                current_rotating_state = WAIT; 
                current_junction_state = ROVER_READY_TO_LEAVE;
                mqttclient.publish(readytoleave_topic, "Y");
                break;
            }
            if(current_rotating_state == ERROR_ROTATION){
                current_junction_state = JUNCTION_ERROR;
            }
            break;
        case ROVER_READY_TO_LEAVE:
            if(IR_sensor == LOW){
                current_junction_state = ROVER_LEAVING;
                rover_cross1_timer_0 = millis();
            }
            break;
        case ROVER_LEAVING:
            if((millis() - rover_cross1_timer_0) > 500){
                if(IR_sensor == HIGH){
                    current_junction_state = ROVER_LEAVING2; 
                }
            }
            break;
        case ROVER_LEAVING2:
            if((millis()-rover_cross2_timer_0)> 500)
                if(IR_sensor == LOW){
                    current_junction_state = ROVER_LEFT;
                }
            break;
        case ROVER_LEFT:
            delay(1000);
            current_junction_state = IDLE;
            break;
        case JUNCTION_ERROR:
            turnAllOutputOff();
            break;
    }
    return current_junction_state;

            
    }
int rotating_state_machine(){

int sensor_A1 = digitalRead(SENSOR_A1_PIN);
int sensor_A2 = digitalRead(SENSOR_A2_PIN);
//int IR_Sensor = digitalRead(IR_SENSOR_PIN);


switch (current_rotating_state){

    case  ENTRY:
        Serial.println(sensor_A1);
        Serial.println(sensor_A2);
        if (sensor_A1==HIGH && sensor_A2 ==HIGH){
            current_rotating_state = STRAIGHT;
        }
        if ((sensor_A1 == HIGH && sensor_A2 == LOW) || (sensor_A1 == LOW && sensor_A2 == HIGH )){
            current_rotating_state = CROSS;
        }
        if (sensor_A1 == LOW && sensor_A2 ==LOW){
            current_rotating_state = ROTATE_CW;
        }

        break;

    case  STRAIGHT:
        turnAllOutputOff();
        current_position = STRAIGHT;
        if (destination == current_position){
            current_rotating_state = SEND_MESSAGE;
        break;
        }
        current_rotating_state = ROTATE_CW;
        break;

    case  CROSS:
        current_position = CROSS;
        turnAllOutputOff();
        if (destination == current_position){
            current_rotating_state = SEND_MESSAGE;

        break;
        }
        current_rotating_state = ROTATE_CCW;
        break;

    case  ROTATE_CW:
        digitalWrite(TURN_CW_PIN,HIGH);
        digitalWrite(TURN_CCW_PIN,LOW);
        rotation_start_timer_0 = millis();
        current_rotating_state = ROTATING;
        break;

    case  ROTATE_CCW:
        digitalWrite(TURN_CCW_PIN,HIGH);
        digitalWrite(TURN_CW_PIN,LOW);
        rotation_start_timer_0 = millis();
        current_rotating_state = ROTATING;
        break;

    case  ROTATING:
        if (millis() - rotation_start_timer_0 > TIME_BUZZER){
            digitalWrite(BUZZER_PIN,HIGH);
        }
        if (millis() - rotation_start_timer_0 > 30000){
            Serial.println("Rotating for too long going to error state");
            current_rotating_state = ERROR_ROTATION;
        }
        if (sensor_A1==HIGH && sensor_A2 ==HIGH){
            current_rotating_state = STRAIGHT;
        }
        if ((sensor_A1 == HIGH && sensor_A2 == LOW) || (sensor_A1 == LOW && sensor_A2 == HIGH )){
            current_rotating_state = CROSS;
        }
        break;

    case SEND_MESSAGE:
        mqttclient.publish(rotationdone_topic, "Y");
        current_rotating_state = DONE;
        break;

    case DONE:

        break;

    case ERROR_ROTATION:

        break;
}

return current_rotating_state;
}

void send_to_server(uint8_t junction_state,
        uint8_t rotation_state,uint8_t sensorA1,uint8_t sensorA2,
        uint8_t buzzer,uint8_t roverIR){
    char* s = (char*)malloc(2);
    mqttclient.publish(junctionstate_topic,itoa(junction_state,s,10));
    mqttclient.publish(rotationstate_topic,itoa(rotation_state,s,10));
    mqttclient.publish(sensorA1_topic,itoa(sensorA1,s,10));
    mqttclient.publish(sensorA2_topic,itoa(sensorA2,s,10));
    mqttclient.publish(buzzer_topic,itoa(buzzer,s,10));
    mqttclient.publish(irsensor_topic,itoa(roverIR,s,10));
}


void callback(char* topic, byte* payload, unsigned int length){
    strcmp()



}




int mqtt_state_machine(){
    unsigned long reconnection_time_0;
    switch(current_mqtt_state){
        case DISCONNECTED:
            current_mqtt_state = RECONNECTING;
            break;
        case RECONNECTING:
            reconnection_time_0 = millis();
            while (!mqttclient.connected())
                if (mqttclient.connect(JUNCTIONID,"status/" JUNCTIONID "/disconnection",0,false,"DISCONNECTED")){
                    Serial.println("Connected to server");
                    mqttclient.publish("status/" JUNCTIONID "/connection","CONNECTED");
                    mqttclient.subscribe(JUNCTIONID "/msgin");
                    mqttclient.subscribe(emergency_stop);
                    current_mqtt_state = CONNECTED;
                }
                else{
                    Serial.println("connection failed, Try again in 3 seconds");
                    delay(3000);
                }
                
            break;
        case CONNECTED:
            if(!mqttclient.connected()){
                current_mqtt_state = DISCONNECTED;
            }
            break;
    }
    return current_mqtt_state;
}



int wifi_state_machine(){
    unsigned long reconnection_time_0;

    switch(current_wifi_state){


        case DISCONNECTED:
            current_wifi_state = RECONNECTING;
            break;

        case RECONNECTING:
            WiFi.begin(WIFI_SSID,WIFI_PSD);
            reconnection_time_0 = millis();
            while(WiFi.status()!=WL_CONNECTED){
                if (millis() -  reconnection_time_0 > 5000){
                    Serial.println("Wifi Connection timeout");
                    current_wifi_state = DISCONNECTED;
                }
            }
            current_wifi_state =  CONNECTED;
            break;

        case CONNECTED:
            if(WiFi.status() != WL_CONNECTED){
                current_wifi_state = DISCONNECTED;
            }
            break;
    }


    return current_wifi_state;
}
/*
int pulse(int time){
        if(millis() - pulsetimer0 > time && flag_buzz == true){
            buz = LOW;
            flag_buzz = false;
            buzztimer_moving = millis();
            return buz;
        }
        if(flag_buzz == false){
            pulsetimer0 = millis();
            flag_buzz = true;
            buz = HIGH;
        }
        return buz;
}
*/
void turnAllOutputOff(){

    digitalWrite(BUZZER_PIN,LOW);
    digitalWrite(TURN_CW_PIN,LOW);
    digitalWrite(TURN_CCW_PIN,LOW);

}
