#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "configs.h"

enum NETWORK_STATES{
    DISCONNECTED,
    RECONNECTING,
    CONNECTED
};
enum ROVER_STATES{
    RESET, 
    RESTING,
    SLOWDOWN,
    STOPPED,
    BUZZER,
    MOVING,
    OBSTACLE,
    EMERGENCY_STOP,
    FORWARD,
    REVERSE,
    IDLE
};

String statestring_rover[]={
    "RESET", 
    "RESTING",
    "SLOWDOWN",
    "STOPPED",
    "BUZZER",
    "MOVING",
    "OBSTACLE",
    "EMERGENCY_STOP",
    "FORWARD",
    "REVERSE",
    "IDLE"
};
String statestring_network[]={
    "DISCONNECTED",
    "RECONNECTING",
    "CONNECTED"
};

const char* fwd_topic = ROVER_ID "in/FWD";
const char* rev_topic = ROVER_ID "in/REV";
const char* sld_topic = ROVER_ID "in/SLD";
const char* buz_topic = ROVER_ID "in/BUZ";
const char* lms_f_topic = ROVER_ID "/LMS_F";
const char* lms_b_topic = ROVER_ID "/LMS_B";
const char* sens_b_topic = ROVER_ID "/SENS_B";
const char* sens_f_topic = ROVER_ID "/SENS_F";
const char* state_topic = ROVER_ID "/STATE";

const char* emergencyover_topic = "emergency/in/end"; 
const char* emergencyin_topic   = "emergency/in/start"; 


uint8_t current_wifi_state = DISCONNECTED;
uint8_t current_mqtt_state = DISCONNECTED;
uint8_t current_rover_state = RESET;
uint8_t buz = LOW;
uint8_t previous_rover_state = RESET;
uint8_t prev_reported_rover_state = RESET;
uint8_t prev_reported_wifi_state = DISCONNECTED;
uint8_t prev_reported_mqtt_state = DISCONNECTED;
uint8_t previous_send_roverstate = RESET;


unsigned long wait_timer_0 = 0l;
unsigned long obstacle_removed_timer0 = 0l;
unsigned long buzztimer_moving = 0l;
unsigned long pulsetimer0 = 0l;
unsigned long last_update_to_server = 0l;

bool flag_obstacle = false;
bool flag_buzz = false;

WiFiClient espClient;
PubSubClient mqttclient(espClient);

int wifi_state_machine();
int mqtt_state_machine();
int rover_state_machine();
int pulse(int time);
void callback(char* topic, byte* payload, unsigned int length);
void write_to_output(uint8_t fwd,uint8_t rev,uint8_t sld,uint8_t buz);
void send_data_to_server(
                        uint8_t fwd,
                        uint8_t rev,
                        uint8_t sld,
                        uint8_t buz,
                        uint8_t lms_f,
                        uint8_t lms_b,
                        uint8_t sens_f,
                        uint8_t sens_b,
                        uint8_t state);


void setup(){

    Serial.begin(115200);
    pinMode(FORWARD_PIN,OUTPUT);
    pinMode(REVERSE_PIN,OUTPUT);
    pinMode(SLOWDOWN_PIN,OUTPUT);
    pinMode(BUZZER_PIN,OUTPUT);
    pinMode(OBSTACLE_SENSOR_B_PIN,INPUT);
    pinMode(OBSTACLE_SENSOR_F_PIN,INPUT);
    pinMode(LIMIT_SWITCH_B_PIN,INPUT);
    pinMode(LIMIT_SWITCH_F_PIN,INPUT);
    digitalWrite(FORWARD_PIN,LOW);
    digitalWrite(REVERSE_PIN,LOW);
    digitalWrite(SLOWDOWN_PIN,LOW);
    digitalWrite(BUZZER_PIN,LOW);
    mqttclient.setServer(SERVER,PORT);
    mqttclient.setKeepAlive(1);
    mqttclient.setCallback(callback);



}

void loop(){
    
    if (prev_reported_rover_state != current_rover_state){
        Serial.printf("ROVER_STATE:%s",statestring_rover[current_rover_state].c_str());
        prev_reported_rover_state = current_rover_state;
    }
    if (prev_reported_mqtt_state != current_mqtt_state){
        Serial.printf("MQTT_STATE:%s",statestring_network[current_mqtt_state].c_str());
        prev_reported_mqtt_state = current_mqtt_state;
    }
    if (prev_reported_wifi_state != current_wifi_state){
        Serial.printf("WIFI_STATE:%s",statestring_rover[current_wifi_state].c_str());
        prev_reported_wifi_state = current_wifi_state;
    }

    if (wifi_state_machine() == CONNECTED && mqtt_state_machine() == CONNECTED){
        rover_state_machine();
        mqttclient.loop();
    }else{
        digitalWrite(FORWARD_PIN,LOW);
        digitalWrite(REVERSE_PIN,LOW);
        digitalWrite(SLOWDOWN_PIN,LOW);
        digitalWrite(BUZZER_PIN,LOW);
    }

}



int rover_state_machine(){

    uint8_t lms_f = digitalRead(LIMIT_SWITCH_F_PIN);
    uint8_t lms_b = digitalRead(LIMIT_SWITCH_B_PIN);
    uint8_t sens_f = digitalRead(OBSTACLE_SENSOR_F_PIN);
    uint8_t sens_b = digitalRead(OBSTACLE_SENSOR_B_PIN);
    uint8_t limit_switch = lms_b || lms_f;
    uint8_t sensor_state = !(sens_f && sens_b);
    uint8_t fwd = LOW;
    uint8_t rev = LOW;
    uint8_t buz = LOW;
    uint8_t sld = LOW;

//    if (sensor_state == 1 || limit_switch ==1){  // if any sensor turns high go to obstacle state
//        if (current_rover_state != OBSTACLE){ 
//            previous_rover_state = current_rover_state;
//            current_rover_state = OBSTACLE;
//            flag_obstacle = true;
//        }
//    }else if((sensor_state ==0) && (flag_obstacle == true) && (limit_switch == 0)){  // when obstacle removed start counter
//        flag_obstacle = false;
//        obstacle_removed_timer0 = millis();
//    }
//
    switch (current_rover_state)
    {
        case  FORWARD:
            fwd = HIGH;
            rev = LOW;
            sld = LOW;
            if(millis() - buzztimer_moving > BUZZER_DELAY_MOVING){
                buz = pulse(BUZZER_PULSE_TIME);
            }
            break;
        case  REVERSE:
            fwd = LOW;
            rev = HIGH;
            sld = LOW;
            if(millis() - buzztimer_moving > BUZZER_DELAY_MOVING){
                buz = pulse(BUZZER_PULSE_TIME);
            }
            break;
        case  STOPPED:
            fwd = LOW;
            rev = LOW;
            sld = LOW;
            if (millis() - wait_timer_0 < BUZZER_DELAY_REACHED){
                digitalWrite(BUZZER_PIN,HIGH);
                buz = HIGH;
            }else{
                digitalWrite(BUZZER_PIN,LOW);
                buz = LOW;
            }
            if (millis()-wait_timer_0 > BUZZER_DELAY_STOP){
                current_rover_state = BUZZER;
            }
            break;
        case BUZZER:
            fwd = LOW;
            rev = LOW;
            sld = LOW;
            buz = HIGH;
            Serial.println("BUZZER");
            break;
        case  SLOWDOWN:
            fwd = LOW;
            rev = LOW;
            sld = HIGH;
            buz = LOW;
            break;
        
        case OBSTACLE:
            fwd = LOW;
            rev = LOW;
            sld = LOW;
            buz = HIGH;
            if (millis() - obstacle_removed_timer0 > 3000 && flag_obstacle == false){
                current_rover_state = previous_rover_state;
            break;

            }
            break;

        case RESTING:
            fwd = LOW;
            rev = LOW;
            sld = LOW;
            buz = LOW;
            break;

        case EMERGENCY_STOP:
            fwd = LOW;
            rev = LOW;
            sld = LOW;
            buz = HIGH;
            break;


        default:
            break;
    }
    write_to_output(fwd,rev,sld,buz);
    if (previous_send_roverstate != current_rover_state || millis() -  last_update_to_server > TIME_BETWEEN_UPDATES){
    send_data_to_server(fwd,rev,sld,buz,lms_f,lms_b,sens_f,sens_b,current_rover_state);
    previous_send_roverstate = current_rover_state;
    last_update_to_server = millis();
    }
    return current_rover_state;
}


void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  if(strcmp(topic,emergency_in_topic)==0){
          current_rover_state = EMERGENCY_STOP;
          mqttclient.publish("rover/ack","EMERGENCY|ACK");
          return;
  }
  for (int i=0;i<length;i++) {
    Serial.print((char)payload[i]);
  }
  if (length < 32){

      char msg[length+1];
      memcpy(msg,payload,length);
      msg[length] = '\0';
      if (strcmp(msg,"FORWARD") == 0){
          current_rover_state = FORWARD;
          mqttclient.publish("rover/ack","FORWARD|ACK");

      }else if (strcmp(msg,"REVERSE") == 0){
          current_rover_state = REVERSE;
          mqttclient.publish("rover/ack","REVERSE|ACK");

      }else if (strcmp(msg,"SLOWDOWN") == 0){
          current_rover_state = SLOWDOWN;
          mqttclient.publish("rover/ack","SLOWDOWN|ACK");

      }else if (strcmp(msg,"STOP") == 0){
          wait_timer_0 = millis();
          current_rover_state = STOPPED;
          mqttclient.publish("rover/ack","STOP|ACK");

      }else if (strcmp(msg,"EMERGENCY") == 0){
          current_rover_state = EMERGENCY_STOP;
          mqttclient.publish("rover/ack","EMERGENCY|ACK");
        
      }else if (strcmp(msg,"REST")==0){
          current_rover_state = RESTING;
          mqttclient.publish("rover/ack","RESTING|ACK");
      }
    if (strcmp(topic,emergencyin_topic)==0){
        current_rover_state =EMERGENCY_STOP;
        return;
    }
    if (strcmp(topic,emergencyover_topic) == 0){
        current_rover_state = RESET;
        //esp_restart();
        return;
    }

      
  }else{
      Serial.println("msg too loong");
  }
  Serial.println();
}
 
void write_to_output(uint8_t fwd,uint8_t rev,uint8_t sld,uint8_t buz){
    digitalWrite(BUZZER_PIN,buz);
    digitalWrite(FORWARD_PIN,fwd);
    digitalWrite(REVERSE_PIN,rev);
    digitalWrite(SLOWDOWN_PIN,sld);
}

void send_data_to_server(
                        uint8_t fwd,
                        uint8_t rev,
                        uint8_t sld,
                        uint8_t buz,
                        uint8_t lms_f,
                        uint8_t lms_b,
                        uint8_t sens_f,
                        uint8_t sens_b,
                        uint8_t state){

    
    char* s= (char*)malloc(2);
    mqttclient.publish(fwd_topic,itoa(fwd,s,10));
    mqttclient.publish(rev_topic,itoa(rev,s,10));
    mqttclient.publish(sld_topic,itoa(sld,s,10));
    mqttclient.publish(buz_topic,itoa(buz,s,10));
    mqttclient.publish(lms_b_topic,itoa(lms_b,s,10));
    mqttclient.publish(lms_f_topic,itoa(lms_f,s,10));
    mqttclient.publish(sens_b_topic,itoa(sens_b,s,10));
    mqttclient.publish(sens_f_topic,itoa(sens_f,s,10));
    mqttclient.publish(state_topic,itoa(state,s,10));
    



   
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
                if (mqttclient.connect("ROVER","status/rover/disconnection",0,false,"DISCONNECTED")){
                    Serial.println("Connected to server");
                    mqttclient.publish("status/rover/connection","CONNECTED");
                    mqttclient.subscribe("rover/msgin");
                    mqttclient.subscribe(emergency_in_topic);
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
