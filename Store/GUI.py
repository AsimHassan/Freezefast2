import collections
import tkinter as tk
import threading
import queue
import paho.mqtt.client as mqtt
from time import sleep

# Globals 


MQTTHOST            = '127.0.0.1'
MQTTPORT            = 1883


xbtn1               = 375
ybtn1               = 175
btnsize             = 73
auxiliary_btn_size  = 50
width               = 800
height              = 400
sizeandloc          = "800x400+20+100"
quitflag            = False
framelist           = {}
msg_in_q            = queue.Queue()
rvr_q               = queue.Queue()
msg_out_q           = queue.PriorityQueue()
mqtt_connection_flag= False
active_frame        = 1 


# Topics 
EMERGENCY_IN_TOPIC  ='+/emergency'
EMERGENCY_OVER_TOPIC='HMI/emergency/over'
EMEGENCY_OUT_TOPIC  ='HMI/emergency'
CALL_TOPIC          = 'HMI/CALL'
GO_TOPIC            ='HMI/GO'
ROVER_POSITION_TOPIC='ROVER/position'
ROVER_STATE         ='ROVER/STATE'
ROVER_PINS       = 'ROVER/in/+'
ROVER_LMS_B      ='ROVER/LMS_B'
ROVER_LMS_F      ='ROVER/LMS_F'
ROVER_SENS_B      ='ROVER/SENS_B'
ROVER_SENS_F      ='ROVER/SENS_F'



def changeframe(frame):
    framelist[frame].tkraise()



class Application():
    def __init__(self,root_window:tk.Tk) -> None:
        self.root_window=root_window
        frame1 = Mainframe(master=root_window)
        rover = Roverframe(master=root_window)
        global framelist
        framelist['frame1'] = frame1 
        framelist['rover'] = rover

        changeframe('frame1')
        self.root_window.update()

        





class Mainframe(tk.Frame):




    def __init__(self,master ) -> None:
        super().__init__(master=master,bg='#DDD',height=400,width=800)
        self.place(x=0,y=0,height=400,width=800)

        self.initUI()

    def initUI(self):

        # variabel declarations
        self.btn_list = []
        self.btn_state = []
        self.stnlist=[]
        self.lastposition = None
        self.callflag = False

        # helper functions
        self.add_aux_btns()
        self.add_func_btns()
        self.addlabels()
        self.update()
        self.pollqueue()


    def add_aux_btns(self):
        # change frame 
        button_edit = tk.Button(self,text='Rover',command=lambda:changeframe('rover'))
        button_edit.place(x=width-btnsize,y = 0,height=btnsize,width=btnsize)
        # close the window
        button_close = tk.Button(self,text = 'X' , command=self.closeme)
        button_close.place(x=width-auxiliary_btn_size,y = height-auxiliary_btn_size,width=auxiliary_btn_size,height = auxiliary_btn_size)

    def add_func_btns(self):
        self.button_go = tk.Button(self,text='GO',command=self.go_pressed)
        self.button_call = tk.Button(self,text='CALL',command=self.call_pressed)
        self.button_emergency_stop = tk.Button(self,text='STOP',command=self.emergencystop)
        self.button_reset = tk.Button(self,text='RESET',command=self.reset)
        self.button_go.place(x=1*(20+btnsize),y=30,height=btnsize,width=btnsize)
        self.button_call.place(x=2*(20+btnsize),y=30,height=btnsize,width=btnsize)
        self.button_emergency_stop.place(x=3*(20+btnsize),y=30,height=btnsize,width=btnsize)
        self.button_reset.place(x=4*(20+btnsize),y=30,height=btnsize,width=btnsize)

    def addlabels(self):
        self.msginlabel = tk.Label(self,text="I should get updated when msg comes in")
        self.msginlabel.place(x=0,y=340)
        self.connectionLabel = tk.Label(self,text="MQTT Server: Disconnected")
        self.connectionLabel.place(x=0,y=0)

    def go_pressed(self):
        if self.findtrue():
            st = self.findtrue()[0]
            print(st.st_id)
            msg_out_q.put((5,GO_TOPIC,str(st.st_id)))
            st.btn.configure(background='#DDD')
            st.btn_state = False
            self.button_call.configure(background='#DDD')
            self.callflag = False



    def call_pressed(self):
        msg_out_q.put((4,CALL_TOPIC,"HMI"))
        self.button_call.configure(background='green')
        self.callflag = True


        


    def emergencystop(self):
        msg_out_q.put((1,EMEGENCY_OUT_TOPIC,"HMI"))

    def reset(self):
        msg_out_q.put((2,EMERGENCY_OVER_TOPIC,"HMI"))


    def closeme(self):
        exit()


    #Other auxiliary functions 
    def stationpress(self,btnnumber):
        print(btnnumber)
        stat = self.getstation(btnnumber)

        if stat:
            print(stat)
            lTrue = self.findtrue()
            print(lTrue)
            for station in lTrue:
                if station != stat:
                    station.btn.configure(background="#DDD")
                    station.btnstate = False
            stat.togglestate()
            print(stat.btn)
            if stat.btnstate:
                stat.btn.configure(background="red")
            else:
                stat.btn.configure(background="#DDD")
        else:
            print("ERROR: station not found")


    def findtrue(self):
        return [stat for stat in self.stnlist if stat.btnstate]

    def update(self):
    #button 1-11
        for num in range(11):
            self.btn_list.append(tk.Button(self,text=f"stn_{11-num}",command=lambda num=11-num:self.stationpress(num),background='#DDD'))
            self.stnlist.append(Station(11 - num))
            self.btn_list[num].place(x=num*btnsize,y=200,height=btnsize,width=btnsize)
            self.stnlist[num].addbtn(self.btn_list[num])
            self.stnlist[num].set_btn_position(num*btnsize,200,btnsize)

    #Button 12        
        self.btn_list.append(tk.Button(self,text="stn_12",command=lambda num=12:self.stationpress(num),background='#DDD'))
        self.btn_list[len(self.btn_list)-1].place(x=6*btnsize,y=200-btnsize,height=btnsize,width=btnsize)
        self.stnlist.append(Station(12))
        self.stnlist[-1].addbtn(self.btn_list[-1])
        self.stnlist[-1].set_btn_position(x=6*btnsize,y=200-btnsize,sz=btnsize)

    #Button 13
        self.btn_list.append(tk.Button(self,text="stn_13",command=lambda num=13:self.stationpress(num),background='#DDD'))
        self.btn_list[len(self.btn_list)-1].place(x=6*btnsize,y=200+btnsize,height=btnsize,width=btnsize)
        self.stnlist.append(Station(13))
        self.stnlist[-1].addbtn(self.btn_list[-1])
        self.stnlist[-1].set_btn_position(x=6*btnsize,y=200+btnsize,sz=btnsize)

    def pollqueue(self):
        if active_frame ==1 :
            if not msg_in_q.empty():
                [msg_type,message] = msg_in_q.get()
                if msg_type ==1:
                    stat = self.get_station_by_id(int(message))
                    if stat:
                        stat.btn.configure(background='green')
                        if self.lastposition:
                            self.lastposition.btn.configure(background='#DDD')
                        self.lastposition = stat
                try: self.msginlabel['text'] = msg_in_q.get()
                except IndexError: pass
            if mqtt_connection_flag:

                self.connectionLabel['text'] = 'MQTT Server: Connected'
            else:
                self.connectionLabel['text'] = 'MQTT Server: Disconnected'
        self.master.after(ms=500,func=self.pollqueue)

    def getlayout(self):
        pass

    def getstation(self,btnnumber):

        for stat in self.stnlist:
            if stat.st_id == btnnumber:
                return stat
        return None

    def get_station_by_id(self,st_id):
        for stat in self.stnlist:
            if st_id == stat.st_id:
                return stat
        return None

############################################################################################################################

class Roverframe(tk.Frame):
    def __init__(self,master ) -> None:
        super().__init__(master=master,bg='#DDD',height=400,width=800)
        self.place(x=0,y=0,height=400,width=800)
        self.label_dict={}
        self.init_aux_btns()
        self.init_status_label()
        self.init_limitswitch_label()
        self.init_sensor_label()
        self.init_fwd_rev_label()
        self.init_buz_sld()
        self.pollqueue()
        



    def init_status_label(self):
        self.state_label = tk.Label(self,text='Rover State:_')
        self.state_label.grid(row=1,column=2,pady=20)
        self.label_dict['state']=self.state_label

    def init_limitswitch_label(self):
        self.lms_f_label = tk.Label(self,text='Front limit Switch:_')
        self.lms_f_label.grid(row=4,column=1,pady=10,padx=2)
        self.lms_r_label = tk.Label(self,text='Rear Limit Switch:_')
        self.lms_r_label.grid(row=4,column=3,pady=10,padx=2)
        self.label_dict['LMS_F'] = self.lms_f_label
        self.label_dict['LMS_B'] = self.lms_r_label
        

    def init_sensor_label(self):
        self.sens_f_label = tk.Label(self,text='Front sensor:_')
        self.sens_f_label.grid(row=5,column=1,pady=10,padx=2)
        self.sens_r_label = tk.Label(self,text='Rear sensor:_')
        self.sens_r_label.grid(row=5,column=3,pady=10,padx=2)
        self.label_dict['SENS_F'] = self.sens_f_label
        self.label_dict['SENS_B'] = self.sens_r_label

    def init_fwd_rev_label(self):
        self.FWD_label = tk.Label(self,text='Forward Pin:_')
        self.FWD_label.grid(row=7,column=1,pady=10,padx=2)
        self.REV_label = tk.Label(self,text='Reverse Pin:_')
        self.REV_label.grid(row=7,column=3,pady=10,padx=2)
        self.label_dict['FWD'] = self.FWD_label
        self.label_dict['REV'] = self.REV_label

    def init_buz_sld(self):
        self.BUZ_label = tk.Label(self,text='Buzzer Pin:_')
        self.BUZ_label.grid(row=8,column=1,pady=10,padx=2)
        self.SLD_label = tk.Label(self,text='Slowdown Pin:_')
        self.SLD_label.grid(row=8,column=3,pady=10,padx=2)
        self.label_dict['BUZ'] = self.BUZ_label
        self.label_dict['SLD'] = self.SLD_label


    def init_aux_btns(self):
        self.button_frame1 = tk.Button(self,text='X',command=self.closeme)
        self.button_frame1.place(x=width-auxiliary_btn_size,y = height-auxiliary_btn_size,width=auxiliary_btn_size,height = auxiliary_btn_size)
        self.button_change_frame = tk.Button(self,text='Station',command=lambda:changeframe('frame1'))
        self.button_change_frame.place(x=width-btnsize,y = 0,height=btnsize,width=btnsize)
    
    def pollqueue(self):
        while not rvr_q.empty():
            (lbl,val) = rvr_q.get()
            t = self.label_dict[lbl]['text'][:-1]
            self.label_dict[lbl].configure(text=t+val)
            
        self.master.after(300,self.pollqueue)


    


    def closeme(self):
        exit()
##################################################################################################################
class Station():
    def __init__(self,st_id):
        self.st_id = st_id
        self.x=(width/2)-btnsize
        self.y=(height/2)-btnsize
        self.btnsize = btnsize
        self.btnstate = False

    def addbtn(self,btn):
        self.btn=btn
    def togglestate(self):
        self.btnstate = not self.btnstate
    def set_btn_position(self,x,y,sz):
        self.x = x
        self.y = y
        self.btnsize = sz

#########################################################################################
################          MQTT ##########################################################
#########################################################################################





def on_position_update(client,userdata,message):

    msg_in_q.put((1,message.payload.decode()))

def on_sensor_update(client,userdata,message):
    print("sendsor update")
    split_topic = message.topic.split('/')
    rvr_q.put((split_topic[-1],message.payload.decode()))

def on_state_update(client,userdata,message):
    rvr_q.put(('state',message.payload.decode()))
    print("state update")

def on_pin_update(client,userdata,message):
    split_topic = message.topic.split('/')
    print("pin update")
    rvr_q.put((split_topic[-1],message.payload.decode()))


def on_connect(client, userdata,flags,rc):
    global mqtt_connection_flag
    mqtt_connection_flag = True
    print("mqtt connected ")
    client.subscribe(ROVER_POSITION_TOPIC)
    client.subscribe(ROVER_SENS_B)
    client.subscribe(ROVER_SENS_F)
    client.subscribe(ROVER_LMS_B)
    client.subscribe(ROVER_LMS_F)
    client.subscribe(ROVER_STATE)
    client.subscribe(ROVER_PINS)

def on_disconnect(client,userdata,message):
    global mqtt_connection_flag
    print("mqtt disconnected")
    mqtt_connection_flag = False

def on_message(client,userdata,message):
    print(message.topic,':',message.payload.decode(),"received from broker")
    
    msg_in_q.put(message.payload.decode())



#  Mqtt
def mqttthread(client_mqtt):

    try:
        client_mqtt.connect(MQTTHOST,MQTTPORT,20)
        client_mqtt.on_connect=on_connect
        client_mqtt.on_disconnect = on_disconnect
        client_mqtt.on_message=on_message
        client_mqtt.message_callback_add(ROVER_POSITION_TOPIC,on_position_update)
        client_mqtt.message_callback_add(ROVER_PINS,on_pin_update)
        client_mqtt.message_callback_add(ROVER_STATE,on_state_update)
        client_mqtt.message_callback_add(ROVER_LMS_F,on_sensor_update)
        client_mqtt.message_callback_add(ROVER_LMS_B,on_sensor_update)
        client_mqtt.message_callback_add(ROVER_SENS_F,on_sensor_update)
        client_mqtt.message_callback_add(ROVER_SENS_B,on_sensor_update)

        client_mqtt.loop_forever()
        
    except KeyboardInterrupt:
        print("Keyboard Interrupt from mqtt thread")
    except :
        raise


def mqtt_out_thread(client_mqtt:mqtt.Client):
    while True:
        if client_mqtt.is_connected():
            if msg_out_q.empty():
                sleep(0.2)
                continue
            
            [_,topic,msg] = msg_out_q.get()
            client_mqtt.publish(topic=topic,payload=msg)





##################################################################################


def main():
    client_mqtt = mqtt.Client('HMI',False)
    
    t1 = threading.Thread(target=mqttthread,args=(client_mqtt,),daemon=True)
    t2 = threading.Thread(target=mqtt_out_thread,args=(client_mqtt,),daemon=True)

    try:
        t1.start()
        window = tk.Tk()
        window.attributes('-fullscreen','True')
        window.geometry(sizeandloc)
        app = Application(window)
        t2.start()
        window.mainloop()
    except KeyboardInterrupt:
        exit()
    except:
        raise


if __name__== "__main__":
    main()