
import json
import queue
class Station:


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

def readfromlayout(filename):
    station_list = []
    with open(filename, 'r') as f:
        layout = json.load(f)

    for stations in layout['stations']:
        st_id = stations['ID']
        st_type = stations['Type']
        right = None
        left = None
        up = None
        down = None
        print(f"not available for {st_id} ",end="")
        try:
            right = stations['right']
        except KeyError:
            print(f"R",end="")
        try:
            left = stations['left']
        except KeyError:
            print(f"L",end="")
        try:
            up = stations['up']
        except KeyError:
            print(f"U",end="")
        try:
            down = stations['down']
        except KeyError:
            print(f"D",end="")
        print()
        station_list.append(Station(st_id = st_id,st_type=st_type,right=right,left=left,up = up,down = down))
    station_list.sort(key=lambda  x : x.st_id)
    return station_list

def layoutfromText(message):
    station_list = []
    layout = json.loads(message)

    for stations in layout['stations']:
        st_id = stations['ID']
        st_type = stations['Type']
        right = None
        left = None
        up = None
        down = None
        print(f"not available for {st_id} ",end="")
        try:
            right = stations['right']
        except KeyError:
            print(f"R",end="")
        try:
            left = stations['left']
        except KeyError:
            print(f"L",end="")
        try:
            up = stations['up']
        except KeyError:
            print(f"U",end="")
        try:
            down = stations['down']
        except KeyError:
            print(f"D",end="")
        print()
        station_list.append(Station(st_id = st_id,st_type=st_type,right=right,left=left,up = up,down = down))
    station_list.sort(key=lambda  x : x.st_id)
    with open('layout.json','w') as f:
        json.dump(layout)
    
    return station_list




finalpath=[]
def search(elem,end,_q,visited,path=[]):
    visited.append(elem)
    path.append(elem)
    if elem.st_id == end :
        global finalpath
        finalpath = path.copy()
        return 

    if elem.left and elem.left not in visited:
        search(elem.left,end,_q,visited,path)

    if elem.right and elem.right not in visited:
        search(elem.right,end,_q,visited,path)

    if elem.up and elem.up not in visited:
        search(elem.up,end,_q,visited,path)

    if elem.down and elem.down not in visited:
        search(elem.down,end,_q,visited,path)

    path.pop()


def get_direction(station_list,start,end):
    bfs_q = queue.Queue()
    stat = get_station(station_list,start)
    visited = []
    path = []
    path = search(stat,end,bfs_q,visited,path)
    # for elem in finalpath:
    #     print(elem.st_id,end='|')

    return finalpath.copy()
    






def get_station(stat_list,stat_id):
    for stat in stat_list:
        if stat.st_id == stat_id:
            return stat
    return None



if __name__ == '__main__':
    stat_list = (readfromlayout('/home/asim/projects/FreezeFast2/Server/layout.json'))
    print(len(stat_list))
    for stat in stat_list:
        if stat.right:
            stat.right = get_station(stat_list,stat.right)
        if stat.left:
            stat.left = get_station(stat_list,stat.left)
        if stat.up:
            stat.up = get_station(stat_list,stat.up)
        if stat.down:
            stat.down = get_station(stat_list,stat.down)
    path = get_direction(stat_list,13,11)
    
    # for stat in stat_list:
    #     print(stat.st_id,end="\t|")
    #     if stat.right:
    #         print('R',stat.right.st_id,end='\t|')
    #     if stat.left:
    #         print('L',stat.left.st_id,end='\t|')
    #     if stat.up:
    #         print('U',stat.up.st_id,end='\t|')
    #     if stat.down:
    #         print('D',stat.down.st_id,end='\t|')

    print(path)