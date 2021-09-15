from json.encoder import py_encode_basestring_ascii
from os import spawnl, stat
from time import sleep
from paho.mqtt.client import Client
import rover
import station

rover_msgin_topic = 'ROVER/msgin'



######## processs #################################
# Check call queue 
# Check rovercross_q
# Check turning station_q
# Check go_messages 
# Check emergencyq and flag
# handle stop messages

global layout_q

class Process():
    def __init__(self,mqtt_client:Client,callq,roverstate_q,rovercross_q,layout_q,go_msg_q,junction_q):
        self.station_list = station.readfromlayout('layout.json')

        


#         print(self.station_list)
#         for stat in self.station_list:
#             if stat.right:
#                 print('R',stat.right.st_id,end='\t|')
#             if stat.left:
#                 print('L',stat.left.st_id,end='\t|')
#             if stat.up:
#                 print('U',stat.up.st_id,end='\t|')
#             if stat.down:
#                 print('D',stat.down.st_id,end='\t|')
# # 

        self.rover_obj = rover.Rover(0,0,1)
        self.mqttclient = mqtt_client 
        self.callq = callq
        self.roverstate_q = roverstate_q
        self.rovercross_q = rovercross_q
        self.layout_q = layout_q
        self.go_msg_q = go_msg_q
        self.junction_q = junction_q
        self.rotation_destination = None


    def check_new_layout(self):
        # print(f"check_new_layout")
        if not self.layout_q.empty():
            _layout = self.layout_q.get()
            self.station_list = station.layoutfromText(_layout)
            self.mqttclient.publish('HMI/layoutupdate',"success")

    def checkcallq(self):
        """Check if call q empty, check if roverfree, then get call from the station and send the rover"""

        # print(f"check_callq")
        if not self.callq.empty() and self.rover_obj.roverfree():
            called_station = self.callq.get()
            _station_number = called_station.split('|')[1]
            self.rover_obj.path=[]
            self.rover_obj.path,self.rover_obj.direction = station.get_direction(self.station_list,self.rover_obj.position,_station_number,self.rover_obj.path)
            self.rover_obj.destination = _station_number
            self.mqttclient.publish(rover_msgin_topic,self.rover_obj.direction)
            self.rover_obj.state = 99

    def checkrovercrossq(self):
        
        # print(f"checkrovercrossq")
        while not self.rovercross_q.empty():
            print("cross q not empty")
            crossed_station = self.rovercross_q.get()
            crossed_station_type = crossed_station.split("|")[0]
            crossed_station_id = crossed_station.split("|")[1]
            crossed_station_obj = station.get_station(self.station_list,crossed_station_id)
            self.rover_obj.position =  crossed_station_id
            if self.rover_obj.destination:
                
                if crossed_station_type == 'JUNCTION':
                    if crossed_station_obj.up in self.rover_obj.path or crossed_station_obj.down in self.rover_obj.path:
                        self.mqttclient.publish(f'{crossed_station}/crossyes','Y')
                        self.mqttclient.publish(f'ROVER/msgin','SLOWDOWN')
                    else:
                        self.mqttclient.publish(f'{crossed_station}/crossno','Y')
                    continue
                if self.rover_obj.destination == crossed_station_id:
                    self.mqttclient.publish(f'{crossed_station}/crossyes','Y')
                    self.mqttclient.publish(f'ROVER/msgin','SLOWDOWN')
                    continue
                if crossed_station_obj not in self.rover_obj.path:
                    self.recalculatedirection()
            self.mqttclient.publish(f'{crossed_station}/crossno','Y')
        # print("crossq empty")





    def recalculatedirection(self):
        
        print(f"recalculatedirection")
        self.rover_obj.path=[]
        self.rover_obj.path,self.rover_obj.direction =  station.get_direction(self.station_list,self.rover_obj.position,self.rover_obj.destination,self.rover_obj.path)  
        self.mqttclient.publish(rover_msgin_topic,self.rover_obj.direction)
        self.rover_obj.state = 99



    def check_roverstate_q(self):
        # print(f"checkroverstateq")
        while not self.roverstate_q.empty():
            self.rover_obj.state =  self.roverstate_q.get()
            print(f"state updated {self.rover_obj.state}")

    def checkJunctionmsgs(self):

        """
        junction messages 
        1. rover stopped ->         JUNCTION|ID|RS
        2. rotation done ->         JUNCTION|ID|RD:S/C
        3. rover ready to leave->   JUNCTION|ID|RRL 
        """
        # print("check junction messages")
        if self.junction_q.empty():
            return
        while not self.junction_q.empty():
            message = self.junction_q.get()
            [sender_type,junc_id,msg]= message.split('|')
            junction = station.get_station(junc_id)
            if msg == 'RS':
                if int(self.rover_obj.destination) in [int(junction.left.st_id), int(junction.right.st_id)]:
                    self.mqttclient.publish(f'{sender_type}|{junc_id}/rotate',"S")
                    self.rotation_destination = 'S'
                    return
                if int(self.rover_obj.destination) in [int(junction.up.st_id), int(junction.down.st_id),]:
                    self.mqttclient.publish(f'{sender_type}|{junc_id}/rotate',"C")
                    self.rotation_destination = 'C'
                    return
            if msg == 'RRL':
                self.rover_obj.path=[]
                self.rover_obj.path,self.rover_obj.direction = station.get_direction(self.station_list,self.rover_obj.position,self.rover_obj.destination,self.rover_obj.path)
                self.mqttclient.publish(rover_msgin_topic,self.rover_obj.direction)
                return
            
            direction = msg.split(':')[1]
            if direction != self.rotation_destination :
                self.mqttclient.publish(f'{sender_type}|{junc_id}/rotate',self.rotation_destination)
                return 
            if direction == self.rotation_destination:
                self.rotation_destination = None
                self.mqttclient.publish(f'{sender_type}|{junc_id}/rotate_ok','Y')


            

                

        

    def put_rover_to_rest(self,sender):
        self.rover_obj.state = 99
        self.mqttclient.publish(rover_msgin_topic,"REST")
        self.mqttclient.publish(f'{sender}/goack','Y')
    
    def send_rover_to_coldroom_or_sipup(self,sender,dest):
        self.rover_obj.state = 99
        coldroom = station.get_station_by_name(self.station_list,dest)
        self.rover_obj.path=[]
        self.rover_obj.path,self.rover_obj.direction = station.get_direction(self.station_list,self.rover_obj.position,coldroom.st_id,self.rover_obj.path)
        self.mqttclient.publish(rover_msgin_topic,self.rover_obj.direction)
        self.mqttclient.publish(f'{sender}/goack','Y')


    def checkgomessages(self):
        # check if position and go station are the same
        # print("check go messages")
        if self.go_msg_q.empty():
            return
        sender = self.go_msg_q.get()
        sendersplit =  sender.split('|')
        sender_name = sendersplit[0]
        sender_id = sendersplit[1]
        print(f"{sender}|{sendersplit}|{sender_id}|{sender_name}")
        if int(sender_id) != int(self.rover_obj.position):
            print("why am i getting this go signal")
            return

        if sender_name == 'HMI':
            try:
                sendlocation = sendersplit[2]
            except IndexError:
                sendlocation = None
            if sendlocation:
                self.rover_obj.state =99
                self.rover_obj.destination = sendlocation
                self.rover_obj.path = []
                self.rover_obj.path,self.rover_obj.direction = station.get_direction(self.station_list,sender_id,sendlocation,self.rover_obj.path)
                self.mqttclient.publish(rover_msgin_topic,self.rover_obj.direction)
                self.mqttclient.pulish('HMI/goack','ack')
            else:
                self.mqttclient.pulish('HMI/goerror','No location')
            return

        if sender_name == 'SIPUP' and not self.rover_obj.sipupflag:
            self.rover_obj.sipupflag = True
            if self.rover_obj.payload == 0:
                self.rover_obj.payload = 1
                self.put_rover_to_rest(sender)
                return

            if self.rover_obj.payload == 1:
                self.rover_obj.payload = 2
                self.send_rover_to_coldroom_or_sipup(sender,'SIPUP')
                return

        if sender_name == 'SIPUP' and self.rover_obj.sipupflag:
            if self.rover_obj.payload == 0:
                self.rover_obj.sipupflag = False
                self.put_rover_to_rest(sender) 
            return




        if sender_name == 'COLDROOM':
            self.rover_obj.payload = 0
            self.rover_obj.state = 99
            if self.rover_obj.sipupflag:
                self.send_rover_to_coldroom_or_sipup(sender,'SIPUP')
            else:
                self.mqttclient.publish(rover_msgin_topic,"REST")
            self.mqttclient.publish(f'{sender}/goack','Y')
            return

        if self.rover_obj.payload == 0:
            self.rover_obj.payload = 1
            self.put_rover_to_rest(sender) 
            return


        if self.rover_obj.payload == 1:
            print("has a payload sending to coldroom")
            self.rover_obj.payload =2
            self.send_rover_to_coldroom_or_sipup(sender,'COLDROOM')
            return

    def run(self):
        self.check_new_layout()
        self.checkcallq()
        self.checkrovercrossq()
        self.check_roverstate_q()
        self.checkJunctionmsgs()
        self.checkgomessages()
        sleep(0.1)







# if __name__ == '__main__':

#     station_list = station.readfromlayout()
#     rover_obj = rover.Rover(0,0,1)



