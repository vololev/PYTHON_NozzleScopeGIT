import Service

#import threading
from tktooltip import ToolTip

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from tkinter.tix import *
from tkinter.font import Font

import os
from PIL import Image, ImageTk, ImageDraw

from datetime import datetime
import time

from jsonrpcclient import request, Error, Ok, parse
import requests
import json



def make_request():
    req = request('Calibrate', params = [4]) #робимо запит
    print('request:', req)
    response = requests.post('http://127.0.0.1:6000', json=req)

def make_request_thread():
    pass
    #t = threading.Thread(target=make_request)
    #t.start()


class AutoRepeatButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.auto_repeat_delay = 500  # milliseconds
        self.auto_repeat_interval = 100  # milliseconds
        self.auto_repeat_job = None
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.invoke()  # Trigger initial button press
        self.auto_repeat_job = self.after(
            self.auto_repeat_delay,
            self.auto_repeat_press
        )

    def on_release(self, event):
        if self.auto_repeat_job is not None:
            self.after_cancel(self.auto_repeat_job)
            self.auto_repeat_job = None

    def auto_repeat_press(self):
        self.invoke()  # Trigger repeated button press
        self.auto_repeat_job = self.after(
            self.auto_repeat_interval,
            self.auto_repeat_press
        )


def _from_rgb(rgb):  # translates an rgb tuple of int to a tkinter friendly color code
    return "#%02x%02x%02x" % rgb

class App:
    def __del__(self):
        pass
    def __init__(self, window, window_title):
        self.SetNoCamera = False

        # create a larger font
        self.megafont = Font(family="Helvetica", size=26, weight='bold')
        self.bigfont = Font(family="Helvetica", size=16, weight='bold')
        self.mediumfont = Font(family="Arial Narrow", size=12, weight='bold')

        self.x=0
        self.y=0

        self.LineStyle={'color':(255,255,255),'opacity':128,'width' : 2}
        self.LineLast=''
        self.LinesH={} # horizontal
        self.LinesV={} # vertical

        window.protocol("WM_DELETE_WINDOW", self.hide_window)
        window.resizable(False, False)
        if cfg('gui.normal') == True:
            window.attributes('-toolwindow', False)
            sts.IN_CameraShow = True
        else:
            #window.protocol("WM_DELETE_WINDOW", self.close_window)
            window.attributes('-toolwindow', True)



        self.window = window
        self.window.title(window_title)

        self.window.bind('<Left>', self.LeftKey)
        self.window.bind('<Right>', self.RightKey)
        self.window.bind('<Up>', self.UpKey)
        self.window.bind('<Down>', self.DownKey)
        self.window.bind("<KP_Subtract>", self.MinusKey)
        self.window.bind("<KP_Add>", self.PlusKey)

        #self.window.bind('<Prior>', self.PageUp)
        #self.window.bind('<Next>', self.PageDown)

        self.window.bind('<Control-Key-o>',self.CtrlO) #відкриваємо файл
        #self.window.bind('<Control-Key-f>',self.CtrlF) #починаємо пошук лазер
        self.window.bind('<Control-Key-r>',self.CtrlR) #починаємо аналіз сопел
        self.window.bind('<Control-Key-p>',self.CtrlP) #друк всіх параметрів

        #h = int(self.vid.height)

        if cfg.conf['nozzle.x0']==0:
            cfg.conf['nozzle.x0'] = cfg.conf['nozzle.y0'] = h/2 #задаємо початкову точку як середину кадра


        #work_frame = tk.Frame(window, width = cfg('crop.size')+20, height = cfg('crop.size')+100)
        work_frame = tk.Frame(window)
        work_frame.pack(side='left')
        # Create a canvas that can fit the above video source size
        self.canvas = tk.Canvas(work_frame, width = cfg('crop.size'), height = cfg('crop.size'))
        self.canvas.pack(side='top', padx=5, pady=5, anchor="center")
        self.canvas.bind("<Button-1>", self.leftclick)
        self.canvas.bind("<Motion>", self.leftmotion)
        #cnvs.bind("<B1-Motion>", self.leftmotion)
        #cnvs.bind('<ButtonRelease-1>', leftup)
        #cnvs.bind("<Button-2>", middleclick)
        #cnvs.bind("<Button-3>", rightclick)
        #cnvs.tag_bind(tag_name, "<Enter>", lambda event: self.check_hand_enter())
        #cnvs.tag_bind(tag_name, "<Leave>", lambda event: self.check_hand_leave())




        bottom_frame = tk.Frame(work_frame, height=48)
        bottom_frame.pack_propagate(0)  # Don't shrink
        bottom_frame.pack(side='bottom', fill='x')
        #bottom_frame.grid_columnconfigure(0, minsize = 600)
        #bottom_frame.grid_propagate(False)

        self.btnConfirm = tk.Button(bottom_frame, text = 'Confirm', bg='green', height=2, width = 6, anchor=tk.CENTER, command = self.btnConfirm_click, state = 'disabled')
        self.btnConfirm.pack(side='right', padx = 8)
        self.btnAbort = tk.Button(bottom_frame, text = 'Abort', bg='red', height=2, width = 6, anchor=tk.CENTER, command = self.btnAbort_click, state = 'disabled')
        self.btnAbort.pack(side='right', padx = 5)

        self.status_label = tk.Label(bottom_frame, height=2, bg=('ivory'), font=self.mediumfont)
        self.status_label.pack(expand = True, fill = 'both', padx=8, pady=5)


        self.framecfg = tk.Frame(window, relief='sunken', borderwidth=1)
        self.framecfg.pack()

        actions_frame = tk.LabelFrame(self.framecfg, text = 'Actions')
        actions_frame.pack(side='top', fill="both", padx=5, pady=3)


        # Button to take a snapshot
        btn_screenshot=tk.Button(actions_frame, text="Screen\nShot", width=10, command=Service.snapshot)
        #btn_snapshot=tk.Button(actions_frame, text="Camera\nsnapshot", width=10, command=lambda: Service.snapshot(readyframe=self.canvas_image()))
        btn_screenshot.pack(side='left', padx=8, pady=8)

        # Button to launch Nozzle analyze AUTO
        btn_nozzleanalyze=tk.Button(actions_frame, text="Nozzle\nAnalyze", width=10, command = self.nozzleanalyze_click)
        btn_nozzleanalyze.pack(side='left', padx=8, pady=8)

        # Button to launch Beam Analyzer ()
        btn_beamanalyze=tk.Button(actions_frame, text="Laser Beam\nFinder", width=10,  command = self.beamanalyze_click)
        btn_beamanalyze.pack(side='left', padx=8, pady=8)

        btn_clearresults=tk.Button(actions_frame, text="Clear\nresults", width=10, command = self.clearresults_click)
        btn_clearresults.pack(side='left', padx=8, pady=8)
        ToolTip(btn_clearresults, msg="Clear Analyze results")



##        self.showOn= tk.IntVar()
##        chkbtn_show = tk.Checkbutton(actions_frame, width=11, text = 'Custom grid', variable = self.showOn)
##        chkbtn_show.pack(side='left', padx=5, pady=5)
##
##        custom_frame = tk.LabelFrame(self.framecfg, width = 350, height = 120, name='frameCustom', text='Custom grid')
##        #frameCustom.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky='nesw')
##        custom_frame.pack(side="top", fill='both', padx=5, pady=3)
##
##        cmbWidth = ttk.Combobox(custom_frame, state='readonly', width=6) #, font=myFontBig)
##        cmbWidth.bind('<<ComboboxSelected>>', self.cmbWidth_change)
##        widthList = (1, 2, 4, 6, 8, 10)
##        cmbWidth['values']=widthList
##        index = widthList.index(self.LineStyle['width'])
##        cmbWidth.current(index)
##        cmbWidth.place(x=10, y=17)
##
##        #self.btnColor = tk.Button(frameCustom, text='LineColor', width = 10, command = self.btnColor_click)
##        btnColor = tk.Button(custom_frame, text='Color', width = 8, bg=_from_rgb(self.LineStyle['color']))
##        btnColor.bind('<ButtonRelease-1>', self.btnColor_click)
##        btnColor.place(x=80, y=15)
##
##        cmbTransparency = tk.Scale(custom_frame, orient = 'horizontal', to=255, length =150) #, font=myFontBig)
##        cmbTransparency.set(self.LineStyle['opacity'])
##        cmbTransparency.bind('<ButtonRelease-1>', self.cmbTransparency_change)
##        cmbTransparency.place(x=170, y=0)
##
##        btn_open = tk.Button(custom_frame, width=8, text='Open',  command=self.open)
##        btn_open.place(x=10, y=60)
##
##        btn_save = tk.Button(custom_frame, width=8, text='Save',  command=self.save)
##        btn_save.place(x=90, y=60)
##
##        btn_new = tk.Button(custom_frame, width=8, text='New',  command=self.new)
##        btn_new.place(x=170, y=60)


        # create Label frame for settings
        settings_frame = tk.LabelFrame(self.framecfg, text="Settings")
        settings_frame.pack(side="top", fill="both", padx=5, pady=3)



        # create label frame for controls
        camera_frame = tk.LabelFrame(settings_frame, text="USB Camera")
        #controls_frame.grid(row=7, columnspan=4, padx=5, pady=5)
        camera_frame.pack(padx=10, pady=5, fill='both')

        # Button for cam settings
        btn_camsett=tk.Button(camera_frame, text="Settings", width=8, height=2, command=self.settings)
        btn_camsett.pack(padx=5, pady=5, side="left")
        ToolTip(btn_camsett, msg="USB camera image settings")

        # Button for cam save
        btn_camsave=tk.Button(camera_frame, text="Save as..", width=8, height=2, command=self.do_popup)
        btn_camsave.pack(padx=5, pady=5, side="left")

        # Button for cam reset
        btn_camreset=tk.Button(camera_frame, text="Reset", width=8, height=2, command=self.camreset)
        btn_camreset.pack(padx=5, pady=5, side="left")
        ToolTip(btn_camreset, msg="Reset camera - same as\nplug-out and plug-in")


        # create buttons frame
        widgets_frame = tk.Frame(settings_frame)
        #widgets_frame.pack(side="top", padx=5, pady=5)
        widgets_frame.pack(side="top", padx=5, pady=5)

        # Button to set beam color
        self.btn_beamcolor=tk.Button(widgets_frame, text="Pick beam\ncolor", width=8, height=2, command=self.beamcolor)
        ToolTip(self.btn_beamcolor, msg='Click on center of "Dark beam" /nto select it color and size')
        self.btn_beamcolor.pack(padx=5, pady=5, side="left")

        # Button to calibrate nozzle and center
        self.btn_calibrate=tk.Button(widgets_frame, text="Calibrate\nscale", width=8, height=2, command=self.calibrate)
        ToolTip(self.btn_calibrate, msg='Calibrate scale by using new/nnozzle with known size')
        self.btn_calibrate.pack(padx=5, pady=5, side="left")


        gridslist = ("Center","Grid", "Military")
        # ShowGrid checkbutton
        self.showgrid= tk.BooleanVar()
        self.showgrid.set(cfg('grid.show'))
        chkbtn_showgrid = tk.Checkbutton(widgets_frame, width=4, text = 'Grid', command=self.chkbtn_showgrid_change, variable = self.showgrid, onvalue = True, offvalue = False)
        chkbtn_showgrid.pack(padx=5, pady=5, side="top")
        # Combobox to select grid

        z = cfg('grid.show')
        self.cmbSight=ttk.Combobox(widgets_frame, state = lambda z: 'readonly' if z else 'disabled', width=8, values = gridslist) #, font=myFontBig)
        self.cmbSight.pack(padx=5, pady=5, side="left")
        self.cmbSight.bind('<<ComboboxSelected>>', self.grid_change)
        #if self.showgrid.get():
            #cfg('grid.current')
        #else:
        self.cmbSight.current(cfg('grid.current'))


        # create label frame for controls
        controls_frame = tk.LabelFrame(settings_frame, text="Set Position and Size")
        #controls_frame.grid(row=7, columnspan=4, padx=5, pady=5)
        controls_frame.pack(padx=10, pady=5, fill='both')

        # create left side button frame
        left_frame = tk.Frame(controls_frame)
        left_frame.grid(row=0, column=0, rowspan=5, padx=40)

        # create zero position button
        self.zero_button = tk.Button(left_frame, text="Zero position\nand zone size", command = self.zero)
        self.zero_button.pack(side="top", padx=10, pady=10)

        # create crop position button
        self.crop_button = tk.Button(left_frame, text="Crop position\nand size", command = self.crop)
        self.crop_button.pack(side="bottom", padx=10, pady=10)


        # create buttons for zooming in and out
        self.minus_button = AutoRepeatButton(controls_frame, text='-', width=3, font=self.bigfont, command = self.minus_click)
        self.plus_button = AutoRepeatButton(controls_frame, text='+', width=3, font=self.bigfont, command = self.plus_click)


        # create cross buttons
        self.left_button = AutoRepeatButton(controls_frame, text='\u25C0', width=3, font=self.bigfont, command = self.left_click)  # left filled triangle
        self.right_button = AutoRepeatButton(controls_frame, text='\u25B6', width=3, font=self.bigfont, command = self.right_click)  # right filled triangle
        self.up_button = AutoRepeatButton(controls_frame, text='\u25B2', width=3, font=self.bigfont, command = self.up_click)  # up filled triangle
        self.down_button = AutoRepeatButton(controls_frame, text='\u25BC', width=3, font=self.bigfont, command = self.down_click)  # down filled triangle

        # create center button
        self.center_button = tk.Button(controls_frame, text='\u25CF', width=3, font=self.bigfont, command = self.reset_click)  # bold circle

        # place controls on grid
        self.minus_button.grid(row=0, column=2)
        self.plus_button.grid(row=0, column=4)
        self.left_button.grid(row=2, column=2, padx=5, pady=5)
        self.center_button.grid(row=2, column=3, padx=5, pady=5)
        self.right_button.grid(row=2, column=4, padx=5, pady=5)
        self.up_button.grid(row=1, column=3, padx=5, pady=5)
        self.down_button.grid(row=3, column=3, padx=5, pady=5)




        json_frame = tk.LabelFrame(self.framecfg, text = 'Settings JSON') #, width=240, height=80, borderwidth=1
        json_frame.pack(side="top", fill="both", padx=5, pady=3)

        # Text for settings edit
        self.text_cfg = tk.Text(json_frame, width = 42, height=12)
        self.restore() # UKR витягаємо попереднє з dictionary
        #self.text_cfg.bind_all("<<Modified>>", self.onModification)
        self.text_cfg.bind("<Key>", self.onModification)
        self.text_cfg.pack(fill="both", padx=5)

        self.but_apply = tk.Button(json_frame, text="Apply", width=10, command=self.apply)
        self.but_apply.pack(padx=5, pady=5,side = 'right')

        self.but_restore = tk.Button(json_frame, text="Restore", width=10, command=self.restore)
        self.but_restore.pack(padx=5, pady=5,side = 'right')

        self.popup() #створюємо менюшку



        # Make all columns the same width using the 'uniform' option
        for i in range(4):
            self.framecfg.columnconfigure(i, uniform='col', minsize=50)

        if cfg.conf.get('gui.normal', False) == False:
            self.hide_window() #ховаємо вікно при запуску

        # Після першого запуску, метод "update", буде автоматично запускатися кожні delay мс. 100мс = 10fps
        self.delay = 100
        self.update()

        # Start the Tkinter event loop. Called only once
        self.window.mainloop()

    #create menu
    def popup(self):
        self.popup_menu = tk.Menu(self.window,
                                       tearoff = 0)

        self.popup_menu.add_command(label = "Save as Nozzle profile",
                                    command = lambda:Service.vid.save_parameters('CONF\CamNozzle.json'))

        self.popup_menu.add_command(label = "Save as Beam profile",
                                    command = lambda:Service.vid.save_parameters('CONF\CamBeam.json'))
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label = "One Extra")

    #display menu on right click
    def do_popup(self):
        x = self.window.winfo_pointerx()
        y = self.window.winfo_pointery()
        try:
            self.popup_menu.tk_popup(x-8, y-8)
        finally:
            self.popup_menu.grab_release()


    def screenshot_click(self):
        #def save_canvas_as_image(canvas, filename):
        # Export the canvas content as PostScript
        ps_data = self.canvas.postscript(colormode='color')

        # Create a PIL Image from the PostScript data
        image = Image.open(io.BytesIO(ps_data.encode('utf-8')))

        image.save(filename)         #Save the image as a file
        return image

    def clearresults_click(self):
        sts.IN_CameraShow = True
        Service.job.setIdle()


    def nozzleanalyze_click(self):
        start_ok, start_result = Service.NozzleAnalyzeStart(1, 1)

    def beamanalyze_click(self):
        start_ok, start_result = Service.BeamAnalyzeStart(Auto=True, Show = False)



    def btn_beam_click(self):
        pass

    def reset_click(self):
        pass

    def left_click(self):
        if sts.IN_NozzleCentering:
            cfg.conf['nozzle.x0']-=1
        if sts.IN_Crop:
            cfg.conf['crop.left']-=2
        pass

    def right_click(self):
        if sts.IN_NozzleCentering:
            cfg.conf['nozzle.x0']+=1
        if sts.IN_Crop:
            cfg.conf['crop.left']+=2
        pass

    def up_click(self):
        if sts.IN_NozzleCentering:
            cfg.conf['nozzle.y0']-=1
        if sts.IN_Crop:
            cfg.conf['crop.top']-=2
        pass

    def down_click(self):
        if sts.IN_NozzleCentering:
            cfg.conf['nozzle.y0']+=1
        if sts.IN_Crop:
            cfg.conf['crop.top']+=2

    def minus_click(self):
        if sts.IN_NozzleCentering:
            cfg.conf['nozzle.zonesize']-=2
        if sts.IN_Crop:
            cfg.conf['crop.size']-=4

    def plus_click(self):
        if sts.IN_NozzleCentering:
            cfg.conf['nozzle.zonesize']+=2
        if sts.IN_Crop:
            cfg.conf['crop.size']+=4


    def confirmabort_enable(self, enable : bool):
        print('buttons enable', enable)
        if enable:
            self.btnConfirm['state'] = 'normal'
            self.btnAbort['state'] = 'normal'
        else:
            self.btnConfirm['state'] = 'disabled'
            self.btnAbort['state'] = 'disabled'


    def chkbtn_showgrid_change(self):
        cfg['grid.show'] = self.showgrid.get()
        if cfg('grid.show'):
            self.cmbSight['state'] = 'readonly'
        else:
            self.cmbSight['state'] = 'disabled'
        pass


    def close_window(self): # Збергіаємся та виходимо
        print("closing main window")
        self.window.destroy()


    def hide_window(self): # вимикаємо отримання кадрів, відмальовку і ховаємо вікно
        # При закриванні вікна і активності центрування променя в ручному режимі
        # виставляємо статус в fault
        if job.Request == job.RequestBeamMANUAL and job.state == job.Work:
            job.setAbort()
        self.framecfg.pack_forget() #ховаємо бічну панель налашутвань
        print("GUI_Hide")
        sts.IN_CameraShow  = False
        self.window.withdraw() #ховаємо вікно

    def show_window(self):
        print("GUI_Show")
        #sts.IN_GuiShow = False
        sts.IN_CameraShow  = True
        self.window.deiconify()
        #self.window.state('zoomed')
        self.window.attributes('-topmost', 1)
        self.window.attributes('-topmost', 0)

    def btnConfirm_click(self):
        self.hide_window()
        job.setReady() #признак того що закінчили

    def btnAbort_click(self):
        self.hide_window()
        job.setAbort() #признак того що закінчили


    #def check_hand_leave(): # Не знаю для чого
    #    pass

    def zero(self):
        sts.IN_NozzleCentering = not sts.IN_NozzleCentering
        if sts.IN_NozzleCentering:
            self.zero_button['relief']=tk.SUNKEN
        else:
            self.zero_button['relief']=tk.RAISED
        pass



    def crop(self):
        if not sts.IN_Crop:
            #треба показати повний кадр - як є
            #виставляємо нульовий кроп і переініалізуємо відео?
            #зчитуємо дані попередньої обрізки і запихуємо їх в контроли
            self.canvas['width'] = Service.vid.width
            self.canvas['height'] = Service.vid.height

            #вхідна точка операції
            sts.IN_Crop = True
            self.crop_button['relief']=tk.SUNKEN
        else:
            self.canvas['width'] = cfg('crop.size')
            self.canvas['height'] = cfg('crop.size')

            sts.IN_Crop = False
            self.crop_button['relief']=tk.RAISED



    def GetOrientation(self, x, y, height = 720, indent = 0.1):
        if (y>0 and (y<indent*height or height-y<indent*height)):
            return 'V' # vertical line
        elif (x>0 and (x<indent*height or height-x<indent*height)):
            return 'H' # horizontal line
        else: return 'X' # unknown (reserved)


    def CheckExist(self, hv, delta = 3):
        if hv=='H':
            for key in self.LinesH.keys():
                if abs(self.y-key)<=delta:
                    #print('found H line. key='+str(key)+' current='+str(self.y))
                    return True, key
        if hv=='V':
            for key in self.LinesV.keys():
                if abs(self.x-key)<=delta:
                    #print('found V line. key='+str(key)+' current='+str(self.x))
                    return True, key
        return False, 0



    def leftclick(self,event):
        # Saving new line or delete previous
        x = event.x
        y = event.y
        print(x,y)

        #Виставляємо центр сопла через клік
        if sts.IN_NozzleCentering:
            cfg.conf['nozzle.x0']=x + cfg.conf['crop.left']
            cfg.conf['nozzle.y0']=y + cfg.conf['crop.top']



        # Calibrating color
        if sts.IN_BeamCalibrating:
            color=Service.ExtractPixelHSV(self.frame, x, y)
            print(f'color={color}') # !!!!якось дибільно викликати функцію класа через Print
            self.btn_beamcolor['background'] = _from_rgb((sts.beamR,sts.beamG,sts.beamB))
            return

        if sts.IN_NetModyfing:
            if self.orientation!='X':
                exist, key = self.CheckExist(self.orientation)
                if exist:  # deleting
                    if self.orientation=='V':
                        print('delete: LinesV x=' + str(key))
                        self.LinesV.pop(key, None)
                        self.canvas['cursor']='tcross'
                    if self.orientation=='H':
                        print('delete: LinesH y=' + str(key))
                        self.LinesH.pop(key, None)
                        self.canvas['cursor']='tcross'
                    pass
                else:      # creating
                    if self.orientation=='V':
                        print('LinesV:' + str(self.LinesV))
                        # Щоб не було однакових значень, зберігаємо не посилання на об`єкт, а його копію.
                        self.LinesV[x] = self.LineStyle.copy()
                        self.canvas['cursor']='X_cursor'
                        print('LinesV:' + str(self.LinesV))
                    if self.orientation=='H':
                        print('LinesH:' + str(self.LinesH))
                        self.LinesH[y] = self.LineStyle.copy()
                        self.canvas['cursor']='X_cursor'
                        print('LinesH:' + str(self.LinesH))
        else:
            pass


    def leftmotion(self, event):
        self.x, self.y = event.x, event.y
        #print("x={}, y={}".format(x,y))

        self.orientation=self.GetOrientation(self.x, self.y)
        # Checking to presence of saved line
        if self.orientation=='X': # not in zone
            self.canvas['cursor']='arrow'
            self.LineLast=''
        else:
            result,value=self.CheckExist(self.orientation)
            if result:
                self.canvas['cursor']='X_cursor'
                self.LineLast = str(value)
            else:
                self.canvas['cursor']='tcross'
                self.LineLast = str(event.x) + ',' + str(event.y)


    def PageUp(self, event):
        Service.vid.gain_up()

    def PageDown(self, event):
        Service.vid.gain_down()


    def CtrlF(self, event):
        pass

    def CtrlR(self, event):
        pass

    def CtrlP(self, event):
        #Service.showparams(self.frame)
        #print(sts.JSON)
        #print(queue1.get())
        pass


    def CtrlO(self, event):
        # replace video by photofile of nozzle
        #filename = filedialog.askopenfilename(initialdir = os.path.dirname(__file__), filetypes=[("JPG files", "*.jpg")],
        #defaultextension='jpg', title='Open nozzle image..')

        #if len(filename)>0:
            # opening file and show it to canvas
            #img = cv2.imread(filename)
            # Load an image using OpenCV
            img = cv2.cvtColor(cv2.imread("d:/___40.jpg"), cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(image = Image.fromarray(img))
            self.canvas.create_image(0, 0, image = photo, anchor = tk.NW)
            #self.window.update()
            self.window.mainloop()

    def btnColor_click(self, event):
        # variable to store hexadecimal code of color
        color_code = colorchooser.askcolor(title ="Choose color", initialcolor=self.LineStyle['color'])
        print('color_code '+str(color_code))
        if color_code!=None:
            event.widget['background'] = color_code[1]
            #print('color_code[1] '+str(color_code[1]))
            self.LineStyle['color'] = color_code[0]
            #print('color_code[0] '+str(color_code[0]))
        pass

    def cmbWidth_change(self, event):
        self.LineStyle['width']=int(event.widget.get())
        print('width='+str(self.LineStyle['width']))
        pass

    def cmbTransparency_change(self, event):
        self.LineStyle['opacity']=event.widget.get()

    def apply(self):
        # we need to check the difference between old and new
        #cfg.save_txt(self.text_cfg.get(1.0,tk.END)) #saving txt into json file

        tmp=self.text_cfg.get(1.0,tk.END) #getting data from
        tmpdict = json.loads(tmp)
        res, text = cfg.validate(tmpdict)
        if res: # validate and save
            self.restart() # ok, restart the program with new settings
        else:
            tk.messagebox.showerror("Error", "JSON is wrong. " + text)
            # we need here just read old (good settings)

            self.restore() # make reset to previous (saved) value


    def restart(self):
        #self.vid.cap.release()
        del Service.vid
        self.window.destroy()
        print('restarting..')
        os.startfile(__file__)    # restart current script


    def restore(self):
        # Reinitilization of program or simple reading of config without initialization
        self.text_cfg.delete('1.0', tk.END)
        self.text_cfg.insert(tk.END, cfg.dumps) # Dictionary -> JSON


    def onModification(self, event):
        #Here we must save settings changes or something else

        #chars = len(event.widget.get("1.0", "end-1c"))
        #print(chars)
        #self.text_cfg._resetting_modified_flag = True
        #label.configure(text="%s chars" % chars)

        #newtext=self.text_cfg.get(1.0,tk.END)
        #newtext=self.text_cfg.get(1.0,'end-1c')+event.char
        #print(newtext)
        pass



    def stop(self):
        os.system("...")
        self.finished=True

    def UpKey(self,event):
        self.up_click()
    def DownKey(self,event):
        self.down_click()
    def LeftKey(self,event):
        self.left_click()
    def RightKey(self,event):
        self.right_click()
    def MinusKey(self,event):
        self.minus_click()
    def PlusKey(self,event):
        self.plus_click()






    def new(self):
        self.LinesH.clear()
        self.LinesV.clear()


    def open(self):
        filename = filedialog.askopenfilename(initialdir = os.path.dirname(__file__), filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        defaultextension='json', title='Open Profile..')
        if len(filename)>0:
            try:
                if os.path.exists(filename):
                    with open(filename, 'r') as fp:
                        Lines = json.load(fp)
                        LinesH = Lines['LinesH']
                        self.LinesH = {int(k):v for k,v in LinesH.items()}
                        LinesV = Lines['LinesV']
                        self.LinesV = {int(k):v for k,v in LinesV.items()}
            except:
                #logger.log('Opening ERROR! ' + w.os.path.basename(filename).split('.')[0])
                pass

    def save(self):
        new_name = 'grid_' + datetime.now().strftime("%Y%m%d_%H%M")
        filename = filedialog.asksaveasfilename(initialdir = os.path.dirname(__file__), filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        confirmoverwrite=True, defaultextension='json', initialfile=new_name, title='Save Profile as..')
        if len(filename)>0:
            #saving grid's JSON
            with open(filename, 'w') as fp:
                Lines = {'LinesH':self.LinesH, 'LinesV':self.LinesV}
                Service.json.dump(Lines, fp, sort_keys = True)
            pass



    def grid_change(self,event): # Вибираємо сітку для відображення в комбобоксі
        selected_item = event.widget.get()
        selected_index = event.widget.current()
        print(f'item={selected_item} index={selected_index}')
        cfg['grid.current'] = selected_index
        #self.window.focus_set() #Знімаємо фокусування з контрола


    def beamcolor(self):
        sts.IN_BeamCalibrating = not sts.IN_BeamCalibrating
        if sts.IN_BeamCalibrating:
            self.btn_beamcolor['relief']=tk.SUNKEN
        else:
            self.btn_beamcolor['relief']=tk.RAISED
        #    event.widget['relief']=tk.RAISED

    def calibrate(self):
        pass
        #req = request('Calibrate', params = [4]) #робимо запит
        #req = request('ping') #робимо запит
        #response = requests.post('http://127.0.0.1:6000', json=req)
        #print('Ping', response)
        #make_request()


    def settings(self):
        Service.vid.run_settings()

    def camreset(self):
        Service.vid.reset()

    def QueueWork(self):
        # get an item from the queue without blocking
        try:
            item = Service.queue1.get(block=False) #.get_nowait()
            if item=='GuiStop':
                return
            if item=='Maximize':
                self.window.state('zoomed')
                #self.window.attributes("-fullscreen", True)
            if str(item).startswith('MsgBox'):
                tk.messagebox.showinfo(title='Увага', message=str(item)[6:])
            if item=='ConfigShow':
                self.framecfg.pack(side='right', fill='both')
            if item=='ConfigHide':
                self.framecfg.pack_forget()
            if item=='GuiShow':                 self.show_window()
            if item=='GuiHide':                 self.hide_window()
            if item=='CameraReset':
                Service.vid.reset()
            if item=='ShowButtons':
                self.confirmabort_enable(True)
            if item=='HideButtons':
                self.confirmabort_enable(False)
        except:
            #print(queue2.get(False))
            pass



    def update(self):
        # get an item from the queue without blocking
        try:
            item = Service.queue1.get(block=False) #.get_nowait()
            if item=='GuiStop':
                self.close_window()
                return
            if item=='Maximize':
                self.window.state('zoomed')
                #self.window.attributes("-fullscreen", True)
            if str(item).startswith('MsgBox'):
                tk.messagebox.showinfo(title='Увага', message=str(item)[6:])
            if item=='ConfigShow':
                self.framecfg.pack(side='right', fill='both')
            if item=='ConfigHide':
                self.framecfg.pack_forget()
            if item=='GuiShow':                 self.show_window()
            if item=='GuiHide':                 self.hide_window()
            if item=='CameraReset':
                Service.vid.reset()
            if item=='ShowButtons':
                self.confirmabort_enable(True)
            if item=='HideButtons':
                self.confirmabort_enable(False)
        except:
            #print(queue2.get(False))
            pass

        if job.isStart():
            sts.IN_CameraShow = True
            job.setWork()             # і активуємо робочий режим

        #self.QueueWork() # планував для обробки черги, не знаю чому закоментував

        #тільки коли отримуємо картинку - робимо щось ще, інакше оновленна кожні 250мс
        if sts.IN_CameraShow == False:
            self.window.after(250, self.update) #повторний захід через 250мс
            return # вивалюємся і до запиту кадра не доходимо

        # Намагаємся отримати кадр з камери і зберегти його всередині GUI класа
        ret, self.frame = Service.vid.get_frame(not sts.IN_Crop) #getRGB and croped
        if ret: #OK
            if self.SetNoCamera: self.SetNoCamera = False

            if sts.IN_Crop:         #малюємо рамку
                # Define the rectangle parameters
                x, y, size = cfg('crop.left'), cfg('crop.top'), cfg('crop.size')  # x and y coordinates of the top-left corner, width and size
                # Draw the rectangle on the image
                Service.cv2.rectangle(self.frame, (x, y), (x + size, y + size), (0, 255, 0), 2)  # (0, 255, 0) represents the color of the rectangle (in BGR format), 2 represents the thickness of the rectangle

            if job.isBeamRequest() and sts.IN_BeamAuto:
                frame = Service.FindLaserBeam(self.frame)
            elif job.isNozzleRequest():  #and job.isWorks() - входимо в обробник завжди, а не тільки коли запит активний
                self.frame = Service.ExtractContours(self.frame)

            if job.isReady():
                if job.isNozzleRequest():
                    keys = ['job_name','InnerStatus','OuterStatus','InnerDiameterMM']
                elif job.isBeamRequest():
                    keys = ['job_name','Centered', 'Dx', 'Dy']
                self.frame = Service.CreateOSD(self.frame, job.result, keys, 0.05, 0.8, 0.95, 0.95, align='left')

                keys.remove('job_name')
                output = ', '.join(map(lambda key: f"{key}={job.result[key]}", # авто-формування рядка
                    filter(lambda key: key in job.result, keys)))
                self.status_label['text'] = output
                print('output', output)


            if sts.IN_CameraCapture and job.isReady():
                sts.IN_CameraCapture = False
                Service.snapshot(False, readyframe=self.frame)
                #Service.vid.snapshot() #чистий кадр
                #Service.cv2.imwrite("Snapshots/" + time.strftime("%d-%m-%Y-%H-%M-%S") + '_frame.jpg', Service.cv2.cvtColor(frame, Service.cv2.COLOR_RGB2BGR))

            if cfg('grid.show'):
                self.img = Image.fromarray(self.frame)
                self.draw = ImageDraw.Draw(self.img, 'RGBA')

                #print(f'self.sight={self.sight()}')
                #if self.curr_sight=='Military':
                if self.cmbSight.get()=='Military':
                    self.photo = self.OSD_Military(320,8,6,20,12)
                #if self.curr_sight=='Grid':
                if self.cmbSight.get()=='Grid':
                    self.photo = self.OSD_Grid(8,40)
                #if self.curr_sight=='Center':
                if self.cmbSight.get()=='Center':
                    self.photo = self.OSD_Center(cfg('nozzle.zonesize'))

            if job.isReady() or job.isAbort(): #20230801
                sts.IN_CameraShow = False
                self.confirmabort_enable(False)

##                if self.showOn.get()==1:
##                    #self.photo = cv2.addWeighted(self.frame, 0.5, self.src2, 0.5, 0)
##                    #self.photo=PIL.Image.alpha_composite(self.frame, self.src2)
##
##                    for y in self.LinesH:
##                        line = self.LinesH[y]
##                        self.draw.line((0, y, h, y),fill = (*line['color'], line['opacity']), width=line['width'])
##                    for x in self.LinesV:
##                        line = self.LinesV[x]
##                        self.draw.line((x, 0, x, h),fill = (*line['color'], line['opacity']), width=line['width'])
##
##                    if sts.IN_NozzleCentering:
##                        #canvas is not suitable, because of not possible make lines semi trnsparent
##                        #self.canvas.create_line(0,self.y,h,self.y, fill = 'white', width = 2)
##                        #self.canvas.create_text((self.x+40, self.y+16), text=str(self.x)+','+str(self.y), fill='white', font="MSGothic 10 bold")
##                        if self.GetOrientation(self.x, self.y, h, 0.1)=='H':
##                            # We must add line for orientation and Text with (new/old) line coordinate to an image
##                            self.draw.line((0, self.y, h, self.y),fill = (*self.LineStyle['color'], self.LineStyle['opacity']), width=self.LineStyle['width'])
##                            self.draw.text((self.x-4, self.y+20), self.LineLast, fill=(255, 255, 255))
##                        if self.GetOrientation(self.x, self.y, h, 0.1)=='V':
##                            self.draw.line((self.x, 0, self.x, h),fill = (*self.LineStyle['color'], self.LineStyle['opacity']), width=self.LineStyle['width'])
##                            self.draw.text((self.x+20, self.y), self.LineLast, fill=(255, 255, 255))
##                    self.photo = ImageTk.PhotoImage(image = self.img)
            else: # Without grid
                self.photo = ImageTk.PhotoImage(image = Image.fromarray(self.frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)
        else:
            if not(self.SetNoCamera):
                self.SetNoCamera=True
                size=cfg('crop.size')
                self.canvas.config(width=size, height=size)
                # Draw a dark gray rectangle that covers the entire canvas
                self.canvas.create_rectangle(0, 0, size, size, fill='#333333')
                nocamera = self.canvas.create_text(0, 0, text="NO CAMERA!", fill="red", font = self.megafont)

                y = x = size / 2                                     # Calculate the center position
                self.canvas.itemconfigure(nocamera, anchor="center") # Set the text anchor to the center
                self.canvas.move(nocamera, x, y) # Move to the center


        self.window.after(self.delay, self.update)

    def OSD_Center (self, r): #треба потім запхати всередину
        x, y = cfg('nozzle.x0')-cfg('crop.left'), cfg('nozzle.y0')-cfg('crop.top')

        self.draw.ellipse((x-r,y-r,x+r,y+r), fill = (255, 255, 255, 16), outline = (255, 255, 255, 64), width=4)
        self.draw.ellipse((x-8,y-8,x+8,y+8), fill = (255, 0, 0, 64))
        self.draw.line((x-1.5*r,y,x-r-1,y),fill = (255, 255, 255, 64), width=4)
        self.draw.line((x+1.5*r,y,x+r+1,y),fill = (255, 255, 255, 64), width=4)
        self.draw.line((x,y-1.5*r,x,y-r-1),fill = (255, 255, 255, 64), width=4)
        self.draw.line((x,y+1.5*r,x,y+r+1),fill = (255, 255, 255, 64), width=4)
        return  ImageTk.PhotoImage(image = self.img)

    def OSD_Grid(self, n, d): #сітка
        x, y = cfg('nozzle.x0')-cfg('crop.left'), cfg('nozzle.y0')-cfg('crop.top')
        x-=(n/2)*d
        y-=(n/2)*d
        for i in range(n+1):
            self.draw.line((x+i*d,y,x+i*d,y+n*d),fill = (255, 255, 255, 64), width=2)
            self.draw.line((x,y+i*d,x+n*d,y+i*d),fill = (255, 255, 255, 64), width=2)

        n*=5
        d/=5
        for i in range(n+1):
            self.draw.line((x+i*d,y,x+i*d,y+n*d),fill = (255, 255, 255, 32), width=1)
            self.draw.line((x,y+i*d,x+n*d,y+i*d),fill = (255, 255, 255, 32), width=1)
        return  ImageTk.PhotoImage(image = self.img)

    def OSD_Military(self, w, nw, nh, l1, l2): #прицільна сітка
        h=w/nw*nh
        dw=w/nw
        dh=h/nh

        x0, y0 = cfg('nozzle.x0')-cfg('crop.left'), cfg('nozzle.y0')-cfg('crop.top')

        x=x0 - w/2
        y=y0 - l1/2
        for i in range(nw+1):
            self.draw.line((x+i*dw,y,x+i*dw,y+l1), fill = (0, 255, 0, 128), width=4)
        y=y0 - l2/2
        for i in range(2*nw+1):
            self.draw.line((x+i*dw/2,y,x+i*dw/2,y+l2), fill = (0, 255, 0, 96), width=2)

        x=x0 - l1/2
        y=y0 - h/2
        for i in range(nh+1):
            self.draw.line((x,y+i*dh,x+l1,y+i*dh), fill = (0, 255, 0, 128), width=4)
        x=x0 - l2/2
        for i in range(2*nh+1):
            self.draw.line((x,y+i*dh/2,x+l2,y+i*dh/2), fill = (0, 255, 0, 96), width=2)

        x=x0 - w/2
        y=y0
        self.draw.line((x,y,x+w,y), fill = (0, 255, 0, 96), width=2)

        x=x0
        y=y0 - h/2
        self.draw.line((x,y,x,y+h), fill = (0, 255, 0, 96), width=2)
        return  ImageTk.PhotoImage(image = self.img)




def main():
    # Create a window and pass it to the Application object
    print('Starting GUI')
    Z = App(tk.Tk(), "NozzleScope")


def stop():
    pass


cfg = Service.cfg
sts = Service.sts
job = Service.job

if __name__ == "__main__":
    main()

