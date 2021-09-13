class Rover:
    def __init__(self,state=None,direction=None,position=None):
        self.state = state
        self.direction = direction
        self.position = position
        self.destination = None
        self.path = []
        self.payload = 0
        self.sipupflag = False

    def roverfree(self):
        print("rover_free")
        return self.state in [0,1,'0','1']

















