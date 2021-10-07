from tkinter import *
from tkinter.ttk import Frame,Style
import json
xbtn1 = 375
ybtn1 = 175
btnsize = 50

def popup_bonus():
    win = Toplevel()
    win.wm_title("Window")

    l = Label(win, text="Input")
    l.grid(row=0, column=0)

    b = Button(win, text="Okay", command=win.destroy)
    b.grid(row=1, column=0)

def close():
    exit()




class station:
    def __init__(self, st_id ):
        self.right = None
        self.left = None
        self.up = None
        self.down = None
        self.type = "STATION"
        self.st_id = st_id
        self.pos_x = 0
        self.pox_y = 0
        self.size = btnsize
    def place_in_center_of_screen(self):
        self.pos_x = xbtn1
        self.pos_y = ybtn1A




class popupWindow_station(Frame):
    def __init__(self,master):
        top=self.top=Toplevel(master)

        self.l_name=Label(top,text="Station Number")
        self.l_name.grid(row = 0, column = 0)
        self.e_name=Entry(top)
        self.e_name.grid(row = 0, column = 1)

        self.l_left=Label(top,text="LEFT")
        self.l_left.grid(row = 2, column = 0)
        self.e_left=Entry(top)
        self.e_left.grid(row = 2, column = 1)

        self.l_right=Label(top,text="RIGHT")
        self.l_right.grid(row=3,column=0)
        self.e_right=Entry(top)
        self.e_right.grid(row = 3,column =1)

        self.b=Button(top,text='Ok',command=self.cleanup)
        self.b.grid(row =6,column = 1)

    def add_to_JSON(self):
        tobewritten = {"Type":"ST","Name":self.st_name,"Left":self.l_value,"Right":self.r_value}
        try:
            with open("layout.json",'r') as fp:
                data =json.dump(fp)
                
        except FileNotFoundError:
            print("file not found will create new one") 
        with open('layout.json','w') as fp:
            data

    def cleanup(self):
        self.st_name=self.e_name.get()
        self.l_value=self.e_left.get()
        self.r_value=self.e_right.get()
        self.top.destroy()

class popupWindow_Turningstation(Frame):
    def __init__(self,master):
        top=self.top=Toplevel(master)

        self.l_name=Label(top,text="Station Number")
        self.l_name.grid(row = 0, column = 0)
        self.e_name=Entry(top)
        self.e_name.grid(row = 0, column = 1)


        self.l_type=Label(top,text="Station type")
        self.l_type.grid(row = 1, column = 0)
        self.e_type=Entry(top)
        self.e_type.grid(row = 1, column = 1)


        self.l_left=Label(top,text="LEFT")
        self.l_left.grid(row = 2, column = 0)
        self.e_left=Entry(top)
        self.e_left.grid(row = 2, column = 1)

        self.l_right=Label(top,text="RIGHT")
        self.l_right.grid(row=3,column=0)
        self.e_right=Entry(top)
        self.e_right.grid(row = 3,column =1)

        self.l_up=Label(top,text="UP")
        self.l_up.grid(row=4,column = 0)
        self.e_up=Entry(top)
        self.e_up.grid(row=4,column= 1)

        self.l_down=Label(top,text="DOWN")
        self.l_down.grid(row = 5,column =0)
        self.e_down=Entry(top)
        self.e_down.grid(row = 5,column = 1)

        self.b=Button(top,text='Ok',command=self.cleanup)
        self.b.grid(row =6,column = 1)

            


    def cleanup(self):
        self.st_name=self.e_name.get()
        self.st_type=self.e_type.get()
        self.l_value=self.e_left.get()
        self.r_value=self.e_right.get()
        self.u_value=self.e_up.get()
        self.d_value=self.e_down.get()
        self.top.destroy()



class add_station():
    def __init__(self,master):
        win = self.win = Toplevel(master)
        self.win.wm_title("Add Station")
        self.l1 = Label(win,text="field1")
        self.l1.place(win)
        self.e1 = Entry()
        self.e1.place(win)
        self.btn1=Button(win,text="bye",command=self.clean_exit)
        self.btn1.place(win)

    def clean_exit(self):
        self.value1= self.e1.get()
        print(self.value1)
        self.win.destroy()
        return self.value1


class Example(Frame):

    def __init__(self,root):
        super().__init__()
        self.master = root
        self.initUI()
    def initUI(self):

        self.master.title("Absolute positioning")
        self.pack(fill=BOTH, expand=1)

        Style().configure("TFrame", background="#333")
        button_add = Button(self,text='Add station',command=self.popup)
        button_add.place(x=720,y=0,height = btnsize,width=btnsize+30)
        button_cls = Button(self,text='X',command=close)
        button_cls.place(x=750,y=350,height = btnsize,width=btnsize)
        button_update = Button(self,text='U',command=self.update)
        button_update.place(x=0,y=350,height = btnsize,width=btnsize)
        button_update = Button(self,text='R',command=self.showinput)
        button_update.place(x=350,y=350,height = btnsize,width=btnsize)
        self.btn_list = []
        self.btn_state= []
    def help_me(self,btnnumber):
        print(btnnumber)
        if self.btn_state[btnnumber]:
            self.btn_list[btnnumber].configure(background='red')
            self.btn_state[btnnumber] = False
        else:
            self.btn_list[btnnumber].configure(background='blue')
            self.btn_state[btnnumber] = True
    def update(self):
        for num in range(5):
            self.btn_list.append(Button(self,text=f"btn_{num}",command=lambda num=num:self.help_me(num),background='red'))
            self.btn_list[num].place(x=num*btnsize,y=0,height=btnsize,width=btnsize)
            self.btn_state.append(False)
    def centercross(self):
        btn = Button(self,text='btn1')
        btn.place(x=xbtn1,y=ybtn1,height=50,width=50)
        btn2 = Button(self,text='btn2')
        btn2.place(x=xbtn1-btnsize,y=ybtn1,height=btnsize,width=btnsize)
        btn3 = Button(self,text='btn3')
        btn3.place(x=xbtn1+btnsize,y=ybtn1,height=50,width=50)
        btn4 = Button(self,text='btn4')
        btn4.place(x=xbtn1,y=ybtn1 - btnsize,height=btnsize,width=btnsize)
        btn5 = Button(self,text='btn5')
        btn5.place(x=xbtn1,y=ybtn1 + btnsize,height=btnsize,width=btnsize)

    def popup(self):
        self.w = popupWindow_station(self.master)
        self.master.wait_window(self.w.top)

    def showinput(self):
        print(self.w.l_value,self.w.r_value,self.w.u_value,self.w.d_value)

def main():
    try:
        root = Tk()
        root.attributes('-type', 'dock')
        root.geometry("800x400+20+100")
        app = Example(root)
        root.mainloop()
    except KeyboardInterrupt:
        exit()


if __name__ == '__main__':
    main()
