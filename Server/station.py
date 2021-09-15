
import json
from os import DirEntry, execv, path
import queue
from typing import final
class Station:
    junctionlist = []

    def __init__(self,st_id,name=None,description=None,st_type="ST",left=None,right=None,up=None,down=None,state=None):
        self.st_id = st_id
        self.name = name
        self.description = description
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.st_type = st_type
        self.state = state
    
    def updateJunctionlist(self):
        if self.st_type == 'junction':
            Station.junctionlist.append(self)

def readfromlayout(filename):
    print("layout from file")
    station_list = []
    try:
        with open(filename, 'r') as f:
            layout = json.load(f)
    except:
            print("file is empty loading backup")
            with open('layout_bak.json', 'r') as f:
                layout = json.load(f)


    for stations in layout['stations']:
        st_id,st_type,st_name,right,left,up,down = process_layout(stations)
        station_list.append(Station(st_id = st_id,st_type=st_type,name= st_name,right=right,left=left,up = up,down = down))

    station_list.sort(key=lambda  x : x.st_id)
    update_station_neighbours(station_list)
    for stations in station_list:
        print(stations.st_id)
    return station_list


def process_layout(station_dict):
    st_id = station_dict['ID']
    st_type = station_dict['Type']
    right = None
    left = None
    up = None
    down = None
    st_name = None
    print(f"not available for {st_id} ",end="")
    try:
        right = station_dict['right']
    except KeyError:
        print(f"R",end="")
    try:
        st_name = station_dict['name']
    except KeyError:
        print(f"name",end="")
    try:
        left = station_dict['left']
    except KeyError:
        print(f"L",end="")
    try:
        up = station_dict['up']
    except KeyError:
        print(f"U",end="")
    try:
        down = station_dict['down']
    except KeyError:
        print(f"D",end="")
    print()

    return st_id,st_type,st_name,right,left,up,down


def layoutfromText(message):
    print("layoutfromtext")
    station_list = []
    layout = json.loads(message)

    for stations in layout['stations']:
        st_id,st_type,st_name,right,left,up,down = process_layout(stations)
        station_list.append(Station(st_id = st_id,st_type=st_type,name= st_name,right=right,left=left,up = up,down = down))
    station_list.sort(key=lambda  x : x.st_id)
    update_station_neighbours(station_list)
    with open('layout.json','w') as f:
        json.dump(layout,f)
    
    return station_list




finalpath=[]
def search(elem,end,_q,visited,path_search):
    print("search")
    visited.append(elem)
    path_search.append(elem)


    if elem.st_id == int(end) :
        global finalpath
        finalpath = path_search.copy()
        return True

    if elem.left and elem.left not in visited and search(elem.left,end,_q,visited,path_search):
        return True
    if elem.right and elem.right not in visited and search(elem.right,end,_q,visited,path_search):
       return True 
    if elem.up and elem.up not in visited and search(elem.up,end,_q,visited,path_search):
       return True 
    if elem.down and elem.down not in visited and search(elem.down,end,_q,visited,path_search):
       return True

    path_search.pop()
    return False

def get_rover_direction(path_rover_direction):
    print("get rover direction")
    direction = 'STOP'
    print(path_rover_direction)
    if len(path_rover_direction) > 1:
        if path_rover_direction[0].left == path_rover_direction[1]:
            direction = 'FORWARD'
        elif path_rover_direction[0].right == path_rover_direction[1]:
            direction = 'REVERSE'
        elif path_rover_direction[0].up == path_rover_direction[1]:
            direction = 'FORWARD'
        elif path_rover_direction[0].down ==path_rover_direction[1]:
            direction = 'REVERSE'
        else:
            direction = 'STOP'


    return direction


def get_direction(station_list,start,end,path_get_direction):
    print("get direction")
    bfs_q = queue.Queue()
    print(start)
    stat = get_station(station_list,int(start))
    visited = []
    path_possible= search(stat,end,bfs_q,visited,path_get_direction)
    if path_possible:
        print(path_get_direction)
    else:
        print("path not found")

    return finalpath.copy(),get_rover_direction(path_get_direction)

def update_station_neighbours(stat_list):
    for stat in stat_list:
        if stat.right:
            stat.right = get_station(stat_list,stat.right)
        if stat.left:
            stat.left = get_station(stat_list,stat.left)
        if stat.up:
            stat.up = get_station(stat_list,stat.up)
        if stat.down:
            stat.down = get_station(stat_list,stat.down)
    


def get_station_by_name(station_list,stat_name):
    print("get station by name")
    for stat in station_list:
        if stat.name == stat_name:
            return stat
    return None

def get_station(stat_list,stat_id):
    print("get station")
    for stat in stat_list:
        if stat.st_id == stat_id:
            return stat
    return None



if __name__ == '__main__':
    stat_list = (readfromlayout('/home/asim/projects/FreezeFast2/Server/layout.json'))
    print(len(stat_list))
    path_main = []
    path_main,direction = get_direction(stat_list,11,1,path_main)
    
    for stat in stat_list:
        print(stat.st_id,end="\t|")
        if stat.right:
            print('R',stat.right.st_id,end='\t|')
        if stat.left:
            print('L',stat.left.st_id,end='\t|')
        if stat.up:
            print('U',stat.up.st_id,end='\t|')
        if stat.down:
            print('D',stat.down.st_id,end='\t|')
        print()

    print("\n")
    print("path:",path_main)
    print("\n")
    print(direction)


    for elem in path_main:
        print(elem.st_id)