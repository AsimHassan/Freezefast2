#include <Arduino.h>
#include <WiFi.h>
#include <configs.h>
#include "PubSubClient.h"


enum STATION_STATES {
    STOPPED,
    RESET,
    CALL,
    WAITFORCALLACK,
    CALLED,
    ROVER_CROSSED,
    ROVER_CROSSED_AGAIN ,
    ROVER_REACHED,
    GO_PRESSED,
    GONE, 
    EMERGENCY,
    IR_LOW,
    ROVERCROSS_INTER,
    ROVER_LEAVING,
    ROVER_LEAVING_INTER,
    ROVER_LEAVING_2
};


String statestring_station[] ={
    "STOPPED",
    "RESET",
    "CALL",
    "WAITFORCALLACK",
    "CALLED",
    "ROVER_CROSSED",
    "ROVER_CROSSED_AGAIN" ,
    "ROVER_REACHED",
    "GO_PRESSED",
    "GONE",
    "EMERGENCY",
    "IR_LOW",
    "ROVERCROSS_INTER",
    "ROVER_LEAVING",
    "ROVER_LEAVING_INTER",
    "ROVER_LEAVING_2"
};

enum NETWORK_STATES{
    DISCONNECTED,
    RECONNECTING,
    CONNECTED
};

String statestring_network[]={
    "DISCONNECTED",
    "RECONNECTING",
    "CONNECTED"
};
enum OWNER_STATES{
    UNKNOWN,
    FORYOU,
    NOTFORYOU
};

const char* greenled_topic      = STATIONID "/greenled";
const char* redled_topic        = STATIONID "/redled";
const char* ir_topic            = STATIONID "/ir";
const char* call_topic          = STATIONID "/call";
const char* go_topic            = STATIONID "/go";
const char* rovercross_topic    = STATIONID "/rovercross";
const char* slowdown_topic      = STATIONID "/slowdown";
const char* stop_topic          = STATIONID "/stop";
const char* greenswitch_topic   = STATIONID "/greenswitch";
const char* redswitch_topic     = STATIONID "/redswitch";
const char* crossyes_topic      = STATIONID "/crossyes";
const char* crossno_topic       = STATIONID "/crossno";
const char* callack_topic       = STATIONID "/callack";
const char* goack_topic         = STATIONID "/goack";
const char* emergency_topic     = STATIONID "/emergency";
const char* emergencyack_topic  = STATIONID "/emergency_ack"; 
const char* emergencyover_topic = STATIONID "/emergency_over";
const char* state_topic         = STATIONID "/state";


unsigned long emergency_timer_0 = 0l;
unsigned long server_ack_timer_0 = 0l;
unsigned long roverhere_0 = 0l;
unsigned long green_led_time_last_toggle=0l;
unsigned long led_blink_timer = 0l;
unsigned long last_update_to_server = 0l;
unsigned long lastmessagetime = 0l;


uint8_t current_wifi_state = DISCONNECTED;
uint8_t current_mqtt_state = DISCONNECTED;
volatile uint8_t current_station_state = RESET;
uint8_t previous_station_state = RESET;
uint8_t rover_owner = UNKNOWN;
uint8_t previous_send_stationstate = RESET;



bool emergency_ack_flag = false;

WiFiClient espclient;
PubSubClient mqttclient(espclient);
void callback(char* topic, byte* payload, unsigned int length);
void write_to_output(uint8_t greenled,uint8_t redled);
int wifi_state_machine();
int mqtt_state_machine();
int station_state_machine();
void send_to_server(uint8_t state,
        uint8_t greenled,uint8_t redled,uint8_t greenswitch,
        uint8_t redswitch,uint8_t roverIR);


void setup(){

    Serial.begin(115200);
    pinMode(GREEN_SWITCH_PIN,INPUT_PULLDOWN);
    pinMode(RED_SWITCH_PIN,INPUT_PULLDOWN);
    pinMode(IR_RECEIVER_PIN,INPUT_PULLUP);
    pinMode(GREEN_LED_PIN,OUTPUT);
    pinMode(RED_LED_PIN,OUTPUT);
    mqttclient.setServer(SERVER,PORT);

    mqttclient.setCallback(callback);
    mqttclient.setKeepAlive(1);

    delay(500);
}

void loop(){
    static uint8_t green_led = LOW;
    static uint8_t red_led = LOW;
    if(millis()-lastmessagetime > 1000){
        Serial.print(statestring_network[current_wifi_state]);
        Serial.print("   ");
        Serial.print(statestring_network[current_mqtt_state]);
        Serial.print("   ");
        Serial.println(statestring_station[current_station_state]);
        lastmessagetime = millis();
    }
    if(wifi_state_machine() == CONNECTED && mqtt_state_machine() == CONNECTED){
        station_state_machine();
        mqttclient.loop();
        delay(100);
    }else{
        if (millis()-led_blink_timer > LED_BLINK_DELAY_NOT_CONNECTED){
            digitalWrite(GREEN_LED_PIN,green_led);
            digitalWrite(RED_LED_PIN,red_led);
            green_led = !green_led;
            red_led = !red_led;
        }
         

    }


}


int station_state_machine(){
    uint8_t redswitch = digitalRead(RED_SWITCH_PIN);
    uint8_t greenswitch = digitalRead(GREEN_SWITCH_PIN);
    uint8_t roverIR = digitalRead(IR_RECEIVER_PIN);
    static uint8_t redled = LOW;
    static uint8_t greenled = LOW;

    if(redswitch == HIGH){
        previous_station_state = current_station_state;
        current_station_state = EMERGENCY;
    }

    switch (current_station_state){
        case RESET:
            greenled = LOW;
            redled = LOW;
           if(roverIR == LOW){
                previous_station_state = current_station_state;
                current_station_state = IR_LOW;
                return 0;
            }
            if(greenswitch == HIGH){
                previous_station_state = current_station_state;
                current_station_state = CALL;
            }
            break;
        

        case CALL:
            server_ack_timer_0 = millis();
            Serial.println("sending call");
            mqttclient.publish(call_topic,"T");
            previous_station_state = current_station_state;
            current_station_state = WAITFORCALLACK;
            break;

        case WAITFORCALLACK:
            if(millis() - server_ack_timer_0 > 10000){
                previous_station_state = current_station_state;
                current_station_state = RESET;
                return current_station_state;
            }
            break;


        case CALLED:{
            greenled = HIGH;
            digitalWrite( GREEN_LED_PIN,greenled );
            if(roverIR == LOW){
                previous_station_state = current_station_state;
                current_station_state = IR_LOW; 
                return current_station_state;
            }

            break;
        }
        case IR_LOW:
                mqttclient.publish(rovercross_topic,"Y");
                current_station_state = ROVER_CROSSED; 
                rover_owner = UNKNOWN;
                break;

        case ROVER_CROSSED:
            if(rover_owner == NOTFORYOU){
            current_station_state = previous_station_state;
            break;
            }
            if (roverIR == HIGH){
                current_station_state = ROVERCROSS_INTER;
            }

            break;


        case ROVERCROSS_INTER:
            if (roverIR == LOW && rover_owner == FORYOU){
                mqttclient.publish(stop_topic,"Y");
                current_station_state = ROVER_CROSSED_AGAIN;
                roverhere_0 = millis();
            }
            if (rover_owner == NOTFORYOU){
                rover_owner = false;
                current_station_state =previous_station_state;

                break;
            }


            break;

        case ROVER_CROSSED_AGAIN:
            if (roverIR == LOW && (millis() - roverhere_0 > 500)){
                current_station_state = ROVER_REACHED;
            }
            break;
        
        case ROVER_REACHED:
            if(millis()-green_led_time_last_toggle> LED_BLINK_DELAY){
                greenled = !greenled;
                digitalWrite(GREEN_LED_PIN,greenled);
                green_led_time_last_toggle = millis();
            }
            if (greenswitch == HIGH){
                current_station_state = GO_PRESSED;
                mqttclient.publish(go_topic,"Y");    
            } 
            break;

        case GO_PRESSED:
                current_station_state = ROVER_LEAVING;
                digitalWrite(GREEN_LED_PIN,LOW);
            break;
        
        case ROVER_LEAVING:
            if (roverIR  == HIGH){
                current_station_state = ROVER_LEAVING_INTER;
            }
            break;
        
        case ROVER_LEAVING_INTER:
            if (roverIR == LOW){
                current_station_state = ROVER_LEAVING_2;
                roverhere_0 = millis();
            
            }

            break;
        
        case ROVER_LEAVING_2:
            if (roverIR == HIGH && (millis() - roverhere_0 > 500)){
                current_station_state = GONE;
            }
            break;


        case GONE:
            current_station_state = RESET;
            break;
         
        
        

        case EMERGENCY:
            if (redswitch == LOW){
                delay(60);
                mqttclient.publish(emergency_topic,"T");
                emergency_timer_0 = millis();
                current_station_state = STOPPED;
            }
            break;
        
        case STOPPED:
            if(emergency_ack_flag == true){
                digitalWrite(RED_LED_PIN,HIGH);
            }
            if(millis()-emergency_timer_0 > 1000 && emergency_ack_flag == false){
                current_station_state = EMERGENCY;
            }
            break;
    }

     
    if (previous_send_stationstate != current_station_state || millis() -  last_update_to_server > TIME_BETWEEN_UPDATES){
    send_to_server(current_station_state,greenled,redled,greenswitch,redswitch,roverIR);
    previous_send_stationstate = current_station_state;
    last_update_to_server = millis();
    }
    return current_station_state;
}
void send_to_server(uint8_t state,
        uint8_t greenled,uint8_t redled,uint8_t greenswitch,
        uint8_t redswitch,uint8_t roverIR){
    char* s = (char*)malloc(2);
    mqttclient.publish(state_topic,itoa(state,s,10));
    mqttclient.publish(greenled_topic,itoa(greenled,s,10));
    mqttclient.publish(redled_topic,itoa(redled,s,10));
    mqttclient.publish(redswitch_topic,itoa(redswitch,s,10));
    mqttclient.publish(greenswitch_topic,itoa(greenswitch,s,10));
    mqttclient.publish(ir_topic,itoa(roverIR,s,10));
}


void callback(char* topic, byte* payload, unsigned int length){
    Serial.println(topic);
    Serial.println(strcmp(topic,callack_topic));
    
    if(strcmp(topic,callack_topic)==0){
        Serial.print("hi");
        if(current_station_state == RESET || 
           current_station_state == CALL || 
           current_station_state == WAITFORCALLACK)
        {
            Serial.print("hello");
            previous_station_state = current_station_state;
            current_station_state = CALLED;
            Serial.println(current_station_state);
            return;
        }else{
            Serial.println("late call ack");
        }
        Serial.println("bye");
    }
    if(strcmp(topic,crossyes_topic)==0){
        rover_owner=FORYOU;
        return;
    }

    if (strcmp(topic,crossno_topic) == 0){
        rover_owner=NOTFORYOU;
        return;
    }

    if (strcmp(topic,emergencyack_topic)==0){
        previous_station_state = current_station_state;
        current_station_state = STOPPED;
        emergency_ack_flag = true;
        return;
    }
    if (strcmp(topic,emergencyover_topic) == 0){
        emergency_ack_flag = false;
        current_station_state = RESET;
        return;
    }
    if (strcmp(topic,goack_topic)==0){
        current_station_state = GO_PRESSED;
        return;
    }
    
    return;

}
void write_to_output(uint8_t greenled,uint8_t redled){
    digitalWrite(GREEN_LED_PIN,greenled);
    digitalWrite(RED_LED_PIN,redled);
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
                if (mqttclient.connect(STATIONID,"status/" STATIONID "/disconnection",0,false,"DISCONNECTED")){
                    Serial.println("Connected to server");
                    mqttclient.publish("status/" STATIONID "/connection","CONNECTED");
                    mqttclient.subscribe(STATIONID "/msgin");
                    mqttclient.subscribe(crossno_topic);
                    mqttclient.subscribe(crossyes_topic);
                    mqttclient.subscribe(emergencyack_topic);
                    mqttclient.subscribe(emergencyover_topic);

                    mqttclient.subscribe(callack_topic);
                    mqttclient.subscribe(goack_topic);
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


