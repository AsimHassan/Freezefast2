import rover
import station


def checkcallq(callq,rover_obj:rover.Rover,station_list):
    if not callq.empty() and rover_obj.roverfree():
        called_station = callq.get()
        _station_number = called_station.split('|')[1]
        path = station.get_direction(station_list,rover_obj.position,_station_number)


######## processs #################################
# Check call queue 
# Check rovercross_q
# Check turning station_q
# Check go_messages 
# Check emergencyq and flag

class Process():
    def __init__(self):
        self.station_list = station.readfromlayout('layout.json')
    
    def check_new_layout(self):
        if not layout_q.empty():
            _layout = layout_q.get()
            self.station_list = station.readfromText(_layout)

    def check_roverstate_q():
        if not roverstate_q.empty():






if __name__ == '__main__':

    station_list = station.readfromlayout()
    rover_obj = rover.Rover(0,0,1)



