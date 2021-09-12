class Rover:
    def __init__(self,state=None,direction=None,position=None):
        self.state = state
        self.direction = direction
        self.position = position
        self.destination = None

    def roverfree(self):
        return self.state in [0,1]



