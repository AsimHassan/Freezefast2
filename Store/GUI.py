## Imports

from time import sleep
from tkinter import *
from tkinter.ttk import Frame,Style
import paho.mqtt.client as mqtt
import json
import threading
import queue




# Constants 
xbtn1 = 375
ybtn1 = 175
btnsize = 73
btnsize_max = 200
btnsize_min =50
auxiliary_btn_size = 50
width = 800
height = 400
MQTTHOST = '127.0.0.1'
MQTTPORT = 1883


quitflag = False




# Globals


msg_in_q = queue.Queue()
btn_q = queue.Queue()
msg_out_q=queue.PriorityQueue()






# TOPICS
EMERGENCY_IN_TOPIC='+/emergency'
EMERGENCY_OVER_TOPIC='HMI/emergency/over'
EMEGENCY_OUT_TOPIC='HMI/emergency'
CALL_TOPIC= 'HMI/CALL'
GO_TOPIC='HMI/GO'
ROVER_POSITION_TOPIC='ROVER/position'




# GUI  
class Mainwindow(Frame):
    """
    Class to handle the main window 
    """

    def __init__(self,root):
        super().__init__()
        self.master = root
        self.initUI()

    def help_me(self,btnnumber):
        print(btnnumber)
        stat = self.getstation(btnnumber)

        if stat:
            print(stat)
            lTrue = self.findtrue()
            print(lTrue)
            for station in lTrue:
                if station != stat:
                    station.btn.configure(background="red")
                    station.btnstate = False
            stat.togglestate()
            print(stat.btn)
            if stat.btnstate:
                stat.btn.configure(background="blue")
            else:
                stat.btn.configure(background="red")
        else:
            print("ERROR: station not found")


    def findtrue(self):
        return [stat for stat in self.stnlist if stat.btnstate]

    def update(self):
    #button 1-11
        for num in range(11):
            self.btn_list.append(Button(self,text=f"stn_{11-num}",command=lambda num=11-num:self.help_me(num),background='red'))
            self.stnlist.append(Station(11 - num))
            self.btn_list[num].place(x=num*btnsize,y=200,height=btnsize,width=btnsize)
            self.stnlist[num].addbtn(self.btn_list[num])
            self.stnlist[num].set_btn_position(num*btnsize,200,btnsize)

    #Button 12        
        self.btn_list.append(Button(self,text="stn_12",command=lambda num=12:self.help_me(num),background='red'))
        self.btn_list[len(self.btn_list)-1].place(x=6*btnsize,y=200-btnsize,height=btnsize,width=btnsize)
        self.stnlist.append(Station(12))
        self.stnlist[-1].addbtn(self.btn_list[-1])
        self.stnlist[-1].set_btn_position(x=6*btnsize,y=200-btnsize,sz=btnsize)

    #Button 13
        self.btn_list.append(Button(self,text="stn_13",command=lambda num=13:self.help_me(num),background='red'))
        self.btn_list[len(self.btn_list)-1].place(x=6*btnsize,y=200+btnsize,height=btnsize,width=btnsize)
        self.stnlist.append(Station(13))
        self.stnlist[-1].addbtn(self.btn_list[-1])
        self.stnlist[-1].set_btn_position(x=6*btnsize,y=200+btnsize,sz=btnsize)

    def pollqueue(self):
        if not msg_in_q.empty():
            [msg_type,message] = msg_in_q.get()
            if msg_type ==1:
                stat = self.get_station_by_id(int(message))
                if stat:
                    stat.btn.configure(background='green')
                    if self.lastposition:
                        self.lastposition.btn.configure(background='red')
                    self.lastposition = stat
            try: self.msginlabel['text'] = msg_in_q.get()
            except IndexError: pass
        self.master.after(ms=200,func=self.pollqueue)

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



    def initUI(self):
        self.master.title("HMI")
        self.pack(fill=BOTH, expand = 1)
        self.btn_list = []
        self.btn_state = []
        self.stnlist=[]
        self.lastposition = None
        Style().configure("Tframe", background="#333")

        button_add = Button(self,text='Add station', command=self.popup)
        button_add.place(x=width-auxiliary_btn_size-30,y = 0,height = auxiliary_btn_size, width=auxiliary_btn_size+30)
        button_edit = Button(self,text='edit',command=self.edit)
        button_edit.place(x=width-auxiliary_btn_size,y = auxiliary_btn_size,height=auxiliary_btn_size,width=auxiliary_btn_size)
        button_close = Button(self,text = 'X' , command=self.closeme)
        button_close.place(x=width-auxiliary_btn_size,y = height-auxiliary_btn_size,width=auxiliary_btn_size,height = auxiliary_btn_size)

        button_go = Button(self,text='GO',command=self.go_pressed)
        button_call = Button(self,text='call',command=self.call_pressed)
        button_emergency_stop = Button(self,text='STOP',command=self.emergencystop)
        button_reset = Button(self,text='Reset',command=self.reset)

        button_go.place(x=1*(20+btnsize),y=20,height=btnsize,width=btnsize)
        button_call.place(x=2*(20+btnsize),y=20,height=btnsize,width=btnsize)
        button_emergency_stop.place(x=3*(20+btnsize),y=20,height=btnsize,width=btnsize)
        button_reset.place(x=4*(20+btnsize),y=20,height=btnsize,width=btnsize)

        self.msginlabel = Label(self,text="I should get updated when msg comes in")
        self.msginlabel.place(x=0,y=340)


        self.update()
        self.pollqueue()




    def go_pressed(self):
        if self.findtrue():
            st = self.findtrue()[0]
            print(st.st_id)
            btn_q.put("GO:")
            msg_out_q.put((5,GO_TOPIC,str(st.st_id)))
            st.btn.configure(background='red')
            st.btn_state = False


    def call_pressed(self):
        btn_q.put("CALL")
        msg_out_q.put((4,CALL_TOPIC,"HMI"))


    def emergencystop(self):
        btn_q.put("EMERGENCY")
        msg_out_q.put((1,EMEGENCY_OUT_TOPIC,"HMI"))

    def reset(self):
        btn_q.put("OVER")
        msg_out_q.put((2,EMERGENCY_OVER_TOPIC,"HMI"))

        pass

    def popup(self):
        print("btn_pressed")
        number = len(self.stnlist)
        self.stnlist.append(Station(number+1,self.master))
        stat = self.stnlist[number]
        stat.addbtn(Button(self,text=stat.st_id,command=stat.togglestate))
        stat.btn.place(x=stat.x,y=stat.y,height=stat.btnsize,width=stat.btnsize)

        print("station added")

    def edit(self):

        pass

    def closeme(self):
        global quitflag
        quitflag = True
        exit()








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



#################Incoming message type to number################
#  Position update: 1
# 



def on_position_update(client,userdata,message):
    msg_in_q.put((1,message.payload.decode()))



def on_connect(client, userdata,flags,rc):
    client.subscribe('HMI/test')
    client.subscribe(ROVER_POSITION_TOPIC)

def on_disconnect(client,userdata,message):
    print("mqtt disconnected")

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





def main():
    
    client_mqtt = mqtt.Client('HMI',False)
    t1 = threading.Thread(target=mqttthread,args=(client_mqtt,),daemon=True)
    t2 = threading.Thread(target=mqtt_out_thread,args=(client_mqtt,),daemon=True)

    try:
        t1.start()
        root = Tk()
        root.attributes('-type', 'dock')
        root.geometry("800x400+20+100")
        app = Mainwindow(root)
        t2.start()
        root.mainloop()
    except KeyboardInterrupt:
        exit()


if __name__ == '__main__':
    main()
