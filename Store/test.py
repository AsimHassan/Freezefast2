import PySimpleGUI as sg

sg.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
size_btn = (5,3)
z = []
l = []
for x in range (5):
    for y in range (10):
        l.append(sg.Button(f"{x}{y}",size=size_btn))
    z.append(l)
    l = []


layout = z

# Create the Window
window = sg.Window('HMI test', layout = layout,location = (0,0),size=(800,480),no_titlebar=True,element_justification='center',keep_on_top=False)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    try:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        print('You entered ', event)
    except KeyboardInterrupt:
        break

window.close()
