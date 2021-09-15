import threading
from time import sleep
import paho.mqtt.client as mqtt
import queue
import process

MQTTHOST = '127.0.0.1'
MQTTPORT = 1883

mqtt_run_flag = True
emergency_flag = False
active_client_list= set()



########## on rover cross #####################################
# check if station has called for rover
# if yes send slow down to rover and cross yes to station
# if no send cross no to station 
# update rover position 
# check if rover is going in correct direction, change if necessary
# pop stations from path as rover moves along

def on_rover_cross(client,userdata,message):
    stat = message.payload.decode()
    rovercross_q.put(stat) 
    

def on_stop_command(client,userdata,message):
    stat = message.payload.decode()
    client.publish('ROVER/msgin',"STOP")
    client.publish(f'{stat}/stopack','ack')


######## on rover cross junction #############################
# check which station called for rover
# if rover needs to turn send slowdown and crossyes
# if rover dont need to turn send crossno
# send direction ??


###### on_rotation done #################################
# check rover destination direction and send rover
# 
def on_junction_rotation_done(client,userdata,message):
    junction_q.put(message.payload.decode())

def on_junction_rover_stopped_at_junction(client,userdata,message):
    junction_q.put(message.payload.decode)

def on_readytoleave(client,userdata,message):
    junction_q.put(message.payload.decode())

########## on GO signal received #################################
def on_go_signal(client,userdata,message):
    go_msg_q.put(message.payload.decode())
    print("added to go q")

def on_slowdown(client,userdata,message):
    stat = message.payload.decode()
    client.publish('ROVER/msgin',"SLOWDOWN")
    client.publish(f'{stat}/slowdown','ack')


############# on call ##################
# add to queue
def on_call_message(client,userdata,message):
    print("call message received ")
    stat = message.topic.split('/')[0]
    callqueue.put(stat)
    print(f"{stat}/callack")
    client.publish(f'{stat}/callack','ack')

############ on status update ##################
def on_rover_stateupdate(client,userdata,message):
    msg = message.payload.decode()
    roverstate_q.put(msg)

############ on connection message #############
def on_status_connnected_message(client,userdata,message:mqtt.MQTTMessage):
    active_client_list.add(message.payload.decode())
    sendlist_active(client)
############ on disconnection #################
def on_status_disconnected_message(client,userdata,message):
    device = message.payload.decode()
    try:
        active_client_list.remove(device)
    except KeyError:
        print(f"cannot find {device} in active client list")
    except :
        raise
    sendlist_active(client)
############ list of active clients #############
def sendlist_active(client:mqtt.Client):
    print(active_client_list)
    message = ":"
    message = message.join(active_client_list)
    client.publish('activeclients',message)
############ on emergency message #############
def on_emergency_message(client,userdata,message):
    client.publish('emergency/in/start','Y')
    global emergency_flag
    emergency_flag = True
    emergency_caller = message.payload.decode()
    emergency_q.put(emergency_caller)
    client.publish('emergency/caller',emergency_caller)
    print(f"emergency was called by {emergency_caller}")
############ on emergency over message #############
def on_emergency_over_message(client,userdata,message):
    global emergency_flag
    if emergency_flag:
        client.publish('emergency/in/end','Y')
        print("emergency over message send")
        emergency_flag = False
############ on connect function #####################
def on_connect(client, userdata, flags, rc):
    client.subscribe('+/emergency')
    client.subscribe('status/+/connection')
    client.subscribe('status/+/disconnection')
    client.subscribe('+/call')
    client.subscribe('Server/msg/in')
    client.subscribe('HMI/emergency_over')
    client.subscribe('ROVER/STATE')
    client.subscribe('HMI/layout/new')
    client.subscribe('+/rovercross')
    client.subscribe('+/go')
    client.subscribe('+/stop')
    client.subscribe('+/slowdown')
    client.subscribe('+/readytoleave')
    client.subscribe('+/roverstoppedjunction')
    client.subscribe('+/rotationdone')
    


def on_disconnect(client:mqtt.Client, userdata, rc):
    print("mqtt disconnected")
############ on message function #####################
def on_message(client, userdata, message):
    print(message.topic,':',message.payload.decode('utf-8'),"put in queue")
    msgQueue.put(message)

def on_layout_message(client, userdata,message):
    print("got new layout")
    layout_q.put(message.payload.decode())



def mqttthread():
    try:
        c_mqtt.connect(MQTTHOST,MQTTPORT,20)
        c_mqtt.on_connect=on_connect
        c_mqtt.on_disconnect=on_disconnect
        c_mqtt.on_message=on_message
        c_mqtt.message_callback_add('+/emergency',on_emergency_message)
        c_mqtt.message_callback_add('HMI/emergency_over',on_emergency_over_message)
        c_mqtt.message_callback_add('+/call',on_call_message)
        c_mqtt.message_callback_add('status/+/connection',on_status_connnected_message)
        c_mqtt.message_callback_add('status/+/disconnection',on_status_disconnected_message)
        c_mqtt.message_callback_add('ROVER/STATE',on_rover_stateupdate)
        c_mqtt.message_callback_add('HMI/layout/new',on_layout_message)
        c_mqtt.message_callback_add('+/rovercross',on_rover_cross)
        c_mqtt.message_callback_add('+/stop',on_stop_command)
        c_mqtt.message_callback_add('+/go',on_go_signal)
        c_mqtt.loop_forever()

    except KeyboardInterrupt:
        print('keyboard interrupt received')
    except :
        raise 



def print_queue(client:mqtt.Client):
    process_obj = process.Process(client,callqueue,roverstate_q,rovercross_q,layout_q,go_msg_q,junction_q)
    while True:

        process_obj.run()
        # sleep(2)
        # if not msgQueue.empty():
        #     print(msgQueue.empty())
        #     msg = msgQueue.get()

        #     print(msgQueue.empty())
        #     print(msg.payload)
        #     client.publish('Server/msg/out',msg.payload)

        # if not callqueue.empty():
        #     msg = callqueue.get()
        #     print(msg)
         
        # if msgQueue.empty():
        #     sleep(0.1)




if __name__ == "__main__":

    msgQueue        = queue.Queue()
    callqueue       = queue.Queue()
    roverstate_q    = queue.Queue()
    rovercross_q    = queue.Queue()
    junction_q      = queue.Queue()
    emergency_q     = queue.Queue()
    layout_q        = queue.Queue()
    go_msg_q        = queue.Queue()

    station_list_new = []
    c_mqtt = mqtt.Client("Server",False)

    t1 = threading.Thread(target=mqttthread,daemon=True)
    t2 = threading.Thread(target=print_queue,daemon=True,args=(c_mqtt,))

    t1.start()
    t2.start()

    print("Server starting")
    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print("keyboard interrupt received from main thread")
    except :
        raise Exception