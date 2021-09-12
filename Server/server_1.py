import paho.mqtt.client as mqtt
import queue

callq =  queue.Queue()
messageq = queue.Queue()

def on_call_message(client,userdata,message:mqtt.MQTTMessage):
    print("message received on wildcard")


class station:
    def __init__(self,left=None,right=None,state=0) -> None:
        self.left = left
        self.right= right
        self.state = state
    

class TurningStation:
    def __init__(self,left=None,right=None,up=None,down=None,direction="STRAIGHT",state=0) -> None:
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.direction = direction 
        self.state = state

    
class Rover:
    def __init__(self) -> None:
        self.state = 0


def on_emergency_message(client:mqtt.Client,userdata,message:mqtt.MQTTMessage):
    initiator = str(message.topic).split('/')[0]
    print("received emergency stop signal:"+ initiator)
    client.publish('emergency_in',"Y")


def on_message(client,userdata,message):
    print("Message received"+message.payload.decode())


def on_message_topic1(client,userdata,message:mqtt.MQTTMessage):
    print("Hello from the other side")
    print(str(message.topic).split('/'))

broker = '127.0.0.1'
broker_port = 1883

client = mqtt.Client()
client.connect(broker,broker_port)
client.on_message = on_message

client.publish('Server/msg','HI')

client.subscribe('Server/msgin')
client.subscribe("+/topic1")
client.subscribe("+/emergency")
client.message_callback_add("+/topic1",on_message_topic1)
client.message_callback_add('+/emergency',on_emergency_message)



client.loop_forever()
