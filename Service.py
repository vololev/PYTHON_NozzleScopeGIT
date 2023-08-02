import numpy as np
import math
import cv2
import json, jsonschema
import os
from dataclasses import dataclass
import colorsys
import queue
import time, datetime
import logging




class MyVideoCapture:
    def __init__(self, CamNum):
        # Open the video source
        self.camid=CamNum
        self.Ready = False
        print("Camera initialization")
        self.cap = cv2.VideoCapture(CamNum, cv2.CAP_DSHOW)
        if self.cap.isOpened():
            # завантажуємо налаштування камери з словаря settings
            self.LoadParamsFromFile('CONF\CamGeneral.json')

            # Зчитуємо фактичні ширину і висоту з камери. Зберігаємо їх в власну змінну  and save it to internal variables
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.Ready = True
            print(f"Camera #{cfg('cam.selected')} initialization complete")
        else: #Якщо не змогли отримати зображення з камери
            self.width = 640
            self.height = 480
            print(f"Camera #{cfg('cam.selected')} initialization FAILED!")


    def reset(self):
        self.shutdown()
        print("Camera reset..")
        self.__init__(self.camid)

    def shutdown(self):
        print("Camera shutdown..")
        self.Ready = False
        try:
            self.cap.release()
        except:
            print('cap is None')


    def LoadParamsFromFile(self, path: str):
        #відкриваємо файл з додатковими налаштуваннями для камери
        #порядково зчитуємо ключ і зосовивуємо значення в self.cap
        if os.path.exists(path):
            with open(path, 'r') as fp:
                settings = json.load(fp)
                for key in settings.keys():
                    if 'CAP_PROP_' in key.upper(): #повинно бути 1-в-1 як CV2, але можна писати маленькими
                        cv2key = getattr(cv2, key.upper())
                        current = self.cap.get(cv2key)
                        if key=='CAP_PROP_FOURCC':
                            new_fourcc = cv2.VideoWriter_fourcc(*settings.get(key)) #декодування ANSII string в DW
                            if current!=new_fourcc:
                                ret = self.cap.set(cv2key, new_fourcc)
                        else:
                            new_value = settings.get(key)
                            if current!=new_value:
                                ret = self.cap.set(cv2key, new_value)
                        print(f'Set CAP.{key} = {settings.get(key)} |{ret}|')




    def ExtractModes(self):
        resolutions_full='''320×240,320×256,384×224,368×240,376×240,272×340,400×240,512×192,448×224,
        320×320,432×240,560×192,400×270,512×212,384×288,480×234,400×300,480×250,312×390,512×240,320×400,
        640×200,480×272,512×256,416×352,480×320,640×240,640×256,512×342,368×480,496×384,800×240,512×384,
        640×320,640×350,640×360,480×500,512×480,720×348,720×350,640×400,720×364,800×352,600×480,640×480,
        640×512,768×480,800×480,848×480,854×480,800×600,960×540,832×624,960×544,1024×576,960×640,1024×600,
        1024×640,960×720,1136×640,1138×640,1024×768,1024×800,1152×720,1152×768,1280×720,1120×832,1280×768,
        1152×864,1334×750,1280×800,1152×900,1024×1024,1366×768,1280×854,1280×960,1600×768,1080×1200,1440×900,
        1440×900,1280×1024,1440×960,1600×900,1400×1050,1440×1024,1440×1080,1600×1024,1680×1050,1776×1000,
        1600×1200,1600×1280,1920×1080,1440×1440,2048×1080,1920×1200,2048×1152,1792×1344,1920×1280,2280×1080,
        2340×1080,1856×1392,2400×1080,1800×1440,2880×900,2160×1200,2048×1280,1920×1400,2520×1080,2436×1125,
        2538×1080,1920×1440,2560×1080,2160×1440,2048×1536,2304×1440,2256×1504,2560×1440,2304×1728,2560×1600,
        2880×1440,2960×1440,2560×1700,2560×1800,2880×1620,2560×1920,3440×1440,2736×1824,2880×1800,2560×2048,
        2732×2048,3200×1800,2800×2100,3072×1920,3000×2000,3840×1600,3200×2048,3240×2160,5120×1440,3200×2400,
        3840×2160,4096×2160,3840×2400,4096×2304,5120×2160,4480×2520,4096×3072'''
        resolutions_medium='''160×120,176×144,192×144,240×160,320×240,352×240,352×288,384×288,480×360,
        640×360,640×480,704×480,720×480,800×480,800×600,960×720,1024×768,1280×720,1280×800,1280×960,
        1280×1024,1600×1200,1920×1080,2048×1536,2560×2048,3200×2400,4096×2160,4096×3072'''
        resolutions = '''640×480,800×600,1024×768,1280×720,1280×960,1280×1024,1600×1200,1920×1080,2048×1536,2560×1440,2560×2048'''

        extracted = {}
        for item in resolutions.split(','):
            (w,h) = item.split('×')
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(w))
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(h))
            width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            extracted[str(int(width))+"x"+str(int(height))] = True
        print(extracted)
        return extracted


    def gain_up(self):
        step = 20
        gain = self.cap.get(cv2.CAP_PROP_GAIN)
        self.cap.set(cv2.CAP_PROP_GAIN, min(gain + step,100))


    def gain_down(self):
        step = 20
        gain = self.cap.get(cv2.CAP_PROP_GAIN)
        self.cap.set(cv2.CAP_PROP_GAIN, max(gain - 20, 0))

    def gain_zero(self):
        self.cap.set(cv2.CAP_PROP_GAIN, 0)


    def crop_frame(self, frame):
        return cfg('crop.size'), frame[cfg('crop.top'):cfg('crop.top')+cfg('crop.size'),cfg('crop.left'):cfg('crop.left')+cfg('crop.size')]
        pass

    def get_frame(self, croped: bool):
        if not self.isReady():
            return (False, None)

        if not self.cap.isOpened():
            self.Ready=False
            print('cap.isOpened() ERROR')
            return (False, None)

        if not self.cap.grab():
            self.Ready=False
            print('cap.grab() ERROR')
            return (False, None)

        #ret, frame = self.cap.retrieve()  # decode the grabbed frame captured by cap.grab(). !!Don't work after CamReset()!
        ret, frame = self.cap.read() #SLOW READING FRAME
        if not(ret):
            self.Ready=False
            print('cap.read() ERROR')
            return (False, None)

        if croped:
            frame = frame[cfg('crop.top'):cfg('crop.top')+cfg('crop.size'),cfg('crop.left'):cfg('crop.left')+cfg('crop.size')] #croping

        if cfg('cam.rotation')==90:
            cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE, frame)
        elif cfg('cam.rotation')==180:
            cv2.rotate(frame, cv2.ROTATE_180, frame)
        elif cfg('cam.rotation')==270:
            cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE, frame)
        return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


    def isReady(self):
        return self.Ready

    def CamReady(self):
        if self.cap.isOpened():
            ret, _ = self.cap.read()
            return ret
        return False

    def run_settings(self):
        self.cap.set(cv2.CAP_PROP_SETTINGS, 1) #запуск системних налаштувань

    def get_parameters(self):
        result={}
        result['cam.brightness'] = int(self.cap.get(cv2.CAP_PROP_BRIGHTNESS))
        result['cam.contrast'] = int(self.cap.get(cv2.CAP_PROP_CONTRAST))
        result['cam.gain'] = int(self.cap.get(cv2.CAP_PROP_GAIN))
        return result
        #self.cap.set(cv2.CAP_PROP_BRIGHTNESS, cfg('cam.brightness'))
        #self.cap.set(cv2.CAP_PROP_CONTRAST, cfg('cam.contrast'))
        #self.cap.set(cv2.CAP_PROP_GAIN, cfg('cam.gain'))

    def save_parameters(self, file_path):
        params = self.get_parameters() #extracting from camera to dictionary
        with open(file_path, "w") as file:  #save dictionary to file
            json.dump(params, file)

    # Release the video source when the object is destroyed
    def __del__(self):
        self.shutdown()




class Config:
    path='CONF\config.json'
    configSchema = {
        "type": "object",
        "properties":
            {
            "gui.lang": {"type": "string", "enum":["en","uk","ru"], "default":"en"},
            "gui.normal" : {"type": "boolean", "default": True},
            "cam.fps": {"type": "number", "enum":[5,10,15,30], "default":10},
            "cam.selected": {"type": "number","minimum":0,"maximum":2, "default":0},
            "cam.rotation": {"type": "number","enum":[0, 90, 180, 270], "default":0},
            #"cam.fourcc": {"type": "string", "enum":["MJPG","YUYV","H264"]},
            #"cam.resolution": {"type": "string", "enum":["640x480", "800x600", "1280x720", "1280x960","1920x1080"]},
            #"cam.brightness": {"type": "number","minimum":-64,"maximum":64},
            #"cam.contrast": {"type": "number","minimum":0,"maximum":95},
            #"cam.gain": {"type": "number","minimum":0,"maximum":100},
            "crop.left":{"type": "number"}, "crop.top":{"type": "number"}, "crop.size":{"type": "number"},
            "nozzle.x0":{"type": "number", "default":0}, "nozzle.y0":{"type": "number", "default":0},
            "nozzle.zonesize" : {"type": "number","minimum":2,"maximum":96, "default":48},
            "autoshots":{"type": "boolean", "default": True},
            "beam.xysize":{"type": "number", "minimum":6, "maximum":64, "default":48},
            "grid.show":{"type": "boolean", "default": False},
            "grid.current": {"type": "number", "default": 0}
            },
        "required":["gui.lang"]
    }
    def __init__(self):
        #ініціалізацію параметрів по замовчанню
##        self.conf_default = {'gui.lang': 'en', 'cam.count' : 0, 'cam.selected' : 0, 'cam.rotation': 90,
##            # 'cam.fourcc' : 'MJPG', 'cam.fps' : 10, 'cam.resolution' : '1280x960',
##            # 'cam.brightness' : 20, 'cam.contrast' : 60, 'cam.gain' : 0,
##            'nozzle.zonesize' : 32,
##            'nozzle.x0' : 0, 'nozzle.y0' : 0, 'scalecoeff' : -1}
        self.conf={}
        self.read_cfg()


    def __call__(self, key): #ппрямий виклик cfg('somekey')
        value = self.conf.get(key)
        if value != None:
            return self.conf.get(key)
        else:
            default=self.configSchema["properties"][key].get("default")
            return default

    def __setitem__(self, key, value):
        self.conf[key] = value

    def update(self, tmp):
        #In Python 3.9.0 or greater (PEP-584):          z = x | y
        #In Python 3.5 or greater:                      z = {**x, **y}
        self.conf = {**self.conf, **tmp}

    def read_cfg(self) -> bool:
        tmp={}
        if os.path.exists(self.path):
            with open(self.path, 'r') as fp:
                tmp = json.load(fp) #зчитуємо в тимчасовий словник
                #self.validate(tmp)[0]
                if self.validate(tmp, self.configSchema)[0]:
                    self.conf = tmp
                    print('Validated is:',tmp)
                    return True
        return False

    def save_cfg(self):
        print('save_cfg')
        with open(self.path, 'w') as fp:
            json.dump(self.conf, fp, sort_keys = True)
    def save_txt(self, text):
        print('save_txt')
        with open(self.path, 'w') as fp:
            fp.write(text)


    # Custom validation function to handle value exceeding maximum and set default value
    def _validate_with_default(validator, data, instance, schema):
        if not validator.is_type(instance, "integer"):
            return

        maximum = schema.get("maximum")
        minimum = schema.get("minimum")
        default = schema.get("default")

        if maximum is not None and instance > maximum:
            instance = default if default is not None else maximum
        if minimum is not None and instance < minimum:
            instance = default if default is not None else minimum

        yield from validator.descend(instance, schema)

    def validate(self, tmpconf, tmpschema): #dictionary
        # If no exception is raised by validate(), the instance is valid.
        try:
            #tmpconf = json.loads(text)
            jsonschema.validate(instance=tmpconf, schema=tmpschema)
        except jsonschema.exceptions.ValidationError as err:
            print('Validate error:', err.message)
            return False, err.message
        else:
            print('Validation Ok')
            return True, None


    @property
    def dumps(self):
        return json.dumps(self.conf)



class ResultsQueue:
    def __init__(self, size):
        self.zero = [0, 0, 0, 0, 0, 0, 0] #пусті 5ть значень - 2 округлості, різниця між центрами, 2 радіуси, x, y (центр внутрішнього контура)
        self.size = size
        self.reset()
        self.max = self.zero.copy() #найкращі значеня
        self.lastavg = self.zero.copy()

    def reset(self): #виставлення нульових результатів
        self.__count = 0
        self.queue = [self.zero]*self.size

    def enqueue(self, x):
        self.queue.insert(0, x)
        self.queue.pop(-1)      #removing old (last element)
        self.__count = min(self.__count+1, self.size) #quantity of measuring

    def average(self):
        avg = self.zero.copy() #пустий набір даних (5 значень з нулями)
        #elesize = len(tmp)
        elesize = len(self.zero)
        for tmp in self.queue: #для кожного запису в черзі значень
            for i in range(elesize): #кожен елемент
                avg[i] += tmp[i] / self.size
        for i in range(elesize):
            avg[i] = round(avg[i], 3) #Second parameter - number of digits after point
        return avg

    def jsonresult(self):
        if self.isFull():
            self.lastavg = self.average()
            self.reset()
        #return json.dumps(self.lastavg) #Поки-що JSON нам не потрібен
        return self.lastavg

    def isEmpty(self):      return self.__count == 0
    def isFull(self):       return self.__count == self.size
    def front(self):        return self.queue[-1]
    def rear(self):         return self.queue[0]
    def len(self):          return self.__count


class CommandStatus:
    def __init__(self):
        self.Idle = 0          # Нема запиту
        self.Start = 1         # Перед початком роботи, необхідна для підготовчих робіт
        self.Work = 2          # Статус
        self.Abort = 500       # Закінчили неуспішно (аварія)
        self.Ready = 200       # Закінчили успішно
        self.state = self.Idle #Запиту немає, скидати після отримання результатів
        #self.timetostop = 1

        #self.Requests={}
        self.RequestNone = -1   #дуже не подобається
        self.RequestBeamAUTO = 0
        self.RequestBeamMANUAL = 1
        self.RequestNozzle = 2
        self.Request = self.RequestNone

        #self.TimeStart = time.time()     # Треба якесь початкове значення
        self.TimeStart = 0


    @property
    def Name(self):
        if self.Request==self.RequestNone:
            return None
        elif self.Request==self.RequestBeamAUTO:
            return 'BeamAnalyzeAUTO'
        elif self.Request==self.RequestBeamMANUAL:
            return 'BeamAnalyzeMANUAL'
        elif self.Request==self.RequestNozzle:
            return 'NozzleAnalyze'
        else:
            return 'Don''t know what request'


    #@property
    def isBeamRequest(self):
        return self.Request in (self.RequestBeamAUTO, self.RequestBeamMANUAL)
    #@property
    def isNozzleRequest(self):
        return self.Request==self.RequestNozzle

    #def __call__(self):
    #    return self.state

    @property
    def statejson(self):
        return {"job_state" : self.state}


    def isIdle(self):
        return self.state == self.Idle
    def isStart(self):
        return self.state == self.Start
    def isWork(self):
        return self.state == self.Work
    def isReady(self):
        return self.state == self.Ready
    def isAbort(self):
        return self.state == self.Abort
    def isComplete(self):
        return self.state in (self.Abort, self.Ready)


    #Питання де робити скидання  - в setIdle чи в setStart
    def setIdle(self):
        if self.state in (self.Ready, self.Abort):
            self.state = self.Idle
            self.Request = self.RequestNone

    def setStart(self, id, seconds:int = 120):
        self.result = {} #онуляємо попередні результати
        # fixing TimeStart and seconds to elapse
        self.timetostop=seconds
        self.TimeStart = time.time()

        self.state = self.Start
        if id in (self.RequestBeamAUTO, self.RequestBeamMANUAL, self.RequestNozzle):
            self.Request = id
            if id == self.RequestNozzle: # А треба перевірка чи не треба
                sts.OUT_NozzleExists = False
                sts.results.reset()                     #!!!скидаємо значення якось не дуже гарно
        else:
            self.Request = self.RequestNone

    def setWork(self):
        self.state = self.Work
        #self.ResultsCreate()

    def setReady(self):
        self.state = self.Ready
        self.ResultsCreate()
        queue1.put('ShowResults') #нагору, для відрисовки результатів. Операцію треба винести із класу назовні!!

    def setAbort(self):
        self.state = self.Abort
        self.ResultsCreate()


    def ResultsCreate(self):
##        #TimeOut check
##        if job.isWork() and time.time()-self.TimeStart>self.timetostop:
##                print("TimeOut happened!!!")
##                job.setAbort()
        result={}
        result['job_state'] = job.state

        #СКОРІШ ЗА ВСЕ НЕ ТРЕБА, АБО ТРЕБА ПЕРЕРОБИТИ
        if job.isIdle():
            job_info = "NO request started yet"
        elif job.isWork():
            job_info = job.Name + " still working"
        elif job.isReady():
            job_info = job.Name + " is Ready"
        elif job.isAbort():
            job_info = job.Name + " Abort"
        else:
            request.info = job.Name + " indefinite"

        result['job_info'] = job_info
        result['job_name'] = job.Name
        result['job_id'] = job.Request

        if job.state in (job.Abort,job.Ready): # якщо закінчили - готовимо результати і скидаємо операцію
            if job.Request in (job.RequestBeamAUTO, job.RequestBeamMANUAL):
                if sts.IN_BeamAuto:
                    result['Centered'] = sts.OUT_BeamCentered
                    result['Dx'] = sts.OUT_BeamDX
                    result['Dy'] = sts.OUT_BeamDY
                    sts.IN_BeamAuto = False

                else: #manual
                    if job.state==job.Ready:
                        result['Centered'] = True
                    else:
                        result['Centered'] = False

            if job.Request ==job.RequestNozzle:
                if sts.OUT_NozzleExists:
                    result['Outer'] = sts.OUT_NozzleOuterCircularity
                    result['Inner'] = sts.OUT_NozzleInnerCircularity
                    result['Delta'] = sts.OUT_NozzleDelta
                    result['OuterDiameterPX'] = sts.OUT_NozzleOuterDiameterPX
                    result['InnerDiameterPX'] = sts.OUT_NozzleInnerDiameterPX
                    result['OuterDiameterMM'] = round(sts.OUT_NozzleOuterDiameterPX/cfg('nozzle.gradescale'),1)
                    result['InnerDiameterMM'] = round(sts.OUT_NozzleInnerDiameterPX/cfg('nozzle.gradescale'),1)

                    result['OuterStatus'], result['OuterStatusId'] = GetNozzleStatus(cfg('CircNewMin'),cfg('CircGoodMinOuter'), sts.OUT_NozzleOuterCircularity)
                    result['InnerStatus'], result['InnerStatusId'] = GetNozzleStatus(cfg('CircNewMin'),cfg('CircGoodMinInner'), sts.OUT_NozzleInnerCircularity)
                    result['InnerX0'], result['InnerY0'] = sts.OUT_NozzleInnerX0, sts.OUT_NozzleInnerY0
                else:
                    result['OuterStatus'], result['OuterStatusId'] = GetNozzleStatus(cfg('CircNewMin'),cfg('CircGoodMinOuter'), 0)
                    result['InnerStatus'], result['InnerStatusId'] = GetNozzleStatus(cfg('CircNewMin'),cfg('CircGoodMinInner'), 0)


        #print(f'results: {result}')
        # Log a message with the current timestamp
        logging.info(f'Result: {result}')
        print('result:', result)
        self.result=result
        #return result



@dataclass
class Status:
    GuiNoWait:  bool = False                # Прапорець, що ми не будемо очікувтаи натисання кнопки Confirm/Abort
    IN_CameraShow:  bool = False            #показувати чи не показувати потік з камери, прапорець

    IN_BeamAuto: bool = False               #шукаємо не шукаємо АВТОматично промінь, прапорець
    IN_BeamCalibrating: bool = False        #запуск відбору кольору після натискання кнопки, прапорець

    IN_NozzleCentering: bool = False        #дозвіл виставляти вручну X0,Y0 через натискаяння клавіш курсору, прапорець
    IN_NetModyfing:     bool = False        #редагуємо сітку, прапорець
    IN_Crop : bool = False                  #редагуємо розмір і положення обрізки, прапорець

    IN_CameraCapture: bool = False
    IN_CameraCaptureFilePath: str = None    #шлях з назвою файла скріншота, значення яке передається запитом куди будемо зберігати фото
    OUT_CameraReady: bool = None

    OUT_BeamShowResult: bool = None
    OUT_BeamDX: int = 0
    OUT_BeamDY: int = 0
    OUT_BeamCentered: bool = False

    #OUT_Beam: list = [0,0]
    #OUT_Beam: tuple(str) = ('0','0')
    #OUT_Beam : list[int] = [0, 0] #will woork in python>=3.9

    OUT_NozzleOuterCircularity: int = 0
    OUT_NozzleInnerCircularity: int = 0
    OUT_NozzleOuterDiameterPX: float = 0
    OUT_NozzleOuterDiameterMM: float = 0
    OUT_NozzleInnerDiameterPX: float = 0
    OUT_NozzleInnerDiameterMM: float = 0
    OUT_NozzleInnerX0:         float = 0
    OUT_NozzleInnerY0:         float = 0
    OUT_NozzleDelta: int = 0
    OUT_NozzleExists: bool = False
    OUT_NozzleInnerStatus: str = '' # по замовчанню - негідне
    OUT_NozzleOuterStatus: str = '' #  по замовчанню - негідне

    beamR: int = 255
    beamG: int = 255
    beamB: int = 255

    results = ResultsQueue(8)  # Черга для збору даних по оцінці сопла
    res_contours = []

    @property
    def JSON(self):
        return str(self.__dict__)   # Збирає все в dictionary у вигляді рядка

    def reset(self):                # Скидаємо в нуль
        self.__init__()




def circularity(contour):
    area = cv2.contourArea(contour)
    length = cv2.arcLength(contour, True)
    if length!=0:   return round(4 * np.pi * area / (length ** 2),3)
    else:           return 0


def ExtractPixelHSV(frame,x,y):
    imghsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

    # Нам треба зробити виборку пікселей -4, +4
    crop=imghsv[y-2:y+2,x-2:x+2]  #croping y axis, x axis
    res=np.mean(crop, axis=(0,1)).astype(int)   #with numpy
    #res=crop.mean(axis=(0,1))                 #without numpy

    #print(f'RGB: {frame[y,x]}')
    cfg.conf['beam.hue'] = sts.beamH = int(res[0]) #HUE is first value
    #(sts.beamR,sts.beamG,sts.beamB) = hsv2rgb(sts.beamH, 255, 255)

    color = frame[y,x] #RGB
    (sts.beamR, sts.beamG, sts.beamB) = hsv2rgb(sts.beamH, 255, 255, 0)
    #(sts.beamR, sts.beamG, sts.beamB) = (int(color[0]),int(color[1]),int(color[2]))
    #return imghsv[y,x]
    return res

def hsv2rgb(h,s,v, hdelta):
    h = (h + hdelta) % 180
    h = h/180
    s = s/255
    v = v/255
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))


def FindLaserBeam(frame, delta = 10):
    im = frame # making a copy of incoming frame
    imghsv  = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

    #For HSV, hue range is [0,179], saturation range is [0,255], and value range is [0,255]
    #For conversion from
    #hue, sat, val = cv2.split(imghsv) #h=248 paint.net 350
    lower = np.array([cfg('beam.hue')-delta,96,96])
    upper = np.array([cfg('beam.hue')+delta,255,255])
    mask = cv2.inRange(imghsv, lower, upper)


    (sts.OUT_BeamDX, sts.OUT_BeamDY) = (0, 0)

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours)>0:
        cnt = sorted(contours, key=cv2.contourArea, reverse=True)[0] #вибираємо найбільший контур
        if 16<cv2.contourArea(cnt)<cfg('beam.xysize')**2: # мінімальна і максімальна площа в пікселях
            #cv2.drawContours(frame, contours, i, (255,0,0), 1)
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            center = (int(x),int(y))
            radius = int(radius)
            (dx ,dy) = (int(x-cfg('nozzle.x0')+cfg('crop.left')),int(y-cfg('nozzle.y0')+cfg('crop.top'))) #

            (sts.OUT_BeamDX, sts.OUT_BeamDY) = (dx, dy)
            sts.OUT_NozzleDelta = int(math.sqrt(dx**2+dy**2))

            #відзначаємо чи попав центр проміня в ідеальний центр. Якщо попадає - ставимо в центр проміня
            #зелене коло, не попадає - чисто червоне
            #cv2.circle(im, center, radius, (hsv2rgb(cfg('beam.hue'), 255, 255, 30)), 2)
            if sts.OUT_NozzleDelta < cfg("nozzle.zonesize"):
                color = (0, 255, 0)
                width = 4
                sts.OUT_BeamCentered = True
            else:
                color = (255, 0, 0)
                width = 2
                sts.OUT_BeamCentered = False

            cv2.circle(im, (center[0],center[1]), int(cfg("nozzle.zonesize")/4), color, 8)
            #cv2.circle(im, (cfg('nozzle.x0'),cfg('nozzle.y0')), 2, (0, 0, 0), 2)
            #cv2.circle(im, (center[0],center[1]), radius, color, width)

            #cv2.line(im, (center[0]-radius,center[1]), (center[0]+radius,center[1]), hsv2rgb(cfg('beam.hue'), 255, 255, 30), 4)
            #cv2.line(im, (center[0],center[1]-radius), (center[0],center[1]+radius), hsv2rgb(cfg('beam.hue'), 255, 255, 30), 4)
            #cv2.putText(im, f"({dx},{dy})", (cfg('nozzle.x0')+8, cfg('nozzle.y0') + 8), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)


    #if job.Request==job.RequestAUTO:
    if sts.GuiNoWait and job.isWork():
        job.setReady()    # Одразу виставляємо готовність, якщо в режимі без GUI
    return im



def ExtractContours(frame):
    #global smoothened #нам потрібні контури навіть після заповнення черги
    color=((0, 0, 255), (0, 255, 0))
    im1 = frame

    if sts.results.isFull() and job.isWork(): #Черга заповнена, робимо підрахунки результата
        res = sts.results.jsonresult()
        # ЯКОСЬ ВСЕ НЕ ДУЖЕ ПОДОБАЄТЬСЯ
        print(f'result = {res}')
        sts.OUT_NozzleOuterCircularity = sts.results.lastavg[0]
        sts.OUT_NozzleInnerCircularity = sts.results.lastavg[1]
        sts.OUT_NozzleDelta            = sts.results.lastavg[2]
        sts.OUT_NozzleOuterDiameterPX  = sts.results.lastavg[3]*2
        sts.OUT_NozzleInnerDiameterPX  = sts.results.lastavg[4]*2
        sts.OUT_NozzleInnerX0          = sts.results.lastavg[5]
        sts.OUT_NozzleInnerY0          = sts.results.lastavg[6]

        print(f'sts.OUT_NozzleOuterDiameterPX={sts.OUT_NozzleOuterDiameterPX} frame_x={frame.shape[0]}')
        outer_index=sts.OUT_NozzleOuterDiameterPX / frame.shape[0]
        if max(sts.OUT_NozzleInnerCircularity, sts.OUT_NozzleOuterCircularity)<0.2 or \
            outer_index>0.95:
            print('OuterDiameter =', int(outer_index*100),'% of frame')
            sts.OUT_NozzleExists = False
        else:
            sts.OUT_NozzleExists = True
            sts.IN_CameraCapture = True

        job.setReady()

    if job.isReady():
        cv2.drawContours(im1, sts.res_contours, 0, color[0], 2)
        cv2.drawContours(im1, sts.res_contours, 1, color[1], 2)
        return im1

    #hsv нам неогбхідне щоб потім можна було розібрати який колір сопла
    hsv  = cv2.cvtColor(im1, cv2.COLOR_BGR2HSV_FULL) #перетворюємо в модель HSV (тон насиченість яскравість)
    h, s, v = cv2.split(hsv)                        #розділяємо на три матриці

    imgray = v
    #imgray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)

    # ЗАДАЄМО ПАРАМЕТРИ ПОШУКУ
    ret, thresh = cv2.threshold(imgray, 150, 200, cv2.THRESH_BINARY)
    #ret, thresh = cv2.threshold(imgray, 150, 200, cv2.THRESH_BINARY_INV)
    #ret, thresh = cv2.adaptiveThreshold(imgray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)

    #imgray = cv2.equalizeHist(thresh)

    # ЗНАХОДИМО КОНТУРИ
    #cv2.RETR_TREE - дерево усіх, RETR_EXTERNAL - тільки зовнішні
    #contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)

    # ВІДМАЛЬОВКА ВСІХ ЗНАЙДЕНИХ СИРИХ КОНТУРІВ
    #im1=cv2.cvtColor(imgray1, cv2.COLOR_GRAY2RGB)
    #cv2.drawContours(im1, contours, -1, (0,255,0), 1)


    # ВИБОРКА КОНТУРІВ З ПЛОЩЕЮ БІЛЬШЕ НІЖ ЗНАЧЕННЯ В НОВИЙ СПИСОК
    # І ОТРИМАННЯ ІНДЕКСУ НАЙБІЛЬШОГО, ЩОБ ПОТІМ ВИТЯГТИ ВСІ ДОЧІРНІ
    MaxIndex=-1
    MaxArea=0
    contours_new=[]
    for i,contour in enumerate(contours):
        area = cv2.contourArea(contour)
        #length = cv2.arcLength(contour, True)
        if area>8*8:
            contours_new.append(contour)
            if area>MaxArea:
                #MaxIndex=i
                MaxIndex+=1
                MaxArea=area

    if MaxIndex==-1: #немає жодного контору
        CycleNozzleAnalyzer(sts.results.zero) #пусте значення
        return frame #вивалюємся

    ## Вимкнуто, бо з ієархіями у нас проблеми
    ##MaxContour=contours_new[MaxIndex]
    ##    sub_contours=[MaxContour] #Загоняємо найбільший контур першим
    ##    Next=hierarchy[0][MaxIndex][2] # getting first child
    ##    while Next!=-1:
    ##        sub_contours.append(contours[Next])
    ##        Next = hierarchy[0][Next][0]

    (max_x, max_y),max_radius = cv2.minEnclosingCircle(contours_new[MaxIndex]) #!!! не знаю що це робить

    # ЗГЛАДЖУВАННЯ КОНТУРІВ
    smoothened = []
    #for cnt in sub_contours:
    for cnt in contours_new:
        # define main island contour approx. and hull
        perimeter = cv2.arcLength(cnt,True)
        epsilon = 0.002*cv2.arcLength(cnt,True)
        smoothened.append(cv2.approxPolyDP(cnt,epsilon,True))

    # СОРТУЄМО ОТРИМАНІ КОНТУРИ ПО ЗМЕНШЕННЮ ПЛОЩІ
    smoothened.sort(key=cv2.contourArea, reverse=True)

    cxy={}
    results=[0, 0, 0, 0, 0, 0, 0]
    if len(smoothened)>0:
        for i, cnt in enumerate(smoothened):
            if i in (0,1): # ВІДМАЛЬОВУЄМО ДВА НАЙБІЛЬШІ КОНТУРИ ОСОБЛИВИМИ КОЛЬОРАМИ
                #clr = color[i]
                results[i] = circularity(smoothened[i])
                (x,y),radius = cv2.minEnclosingCircle(smoothened[i])
                center = (int(x),int(y))
                cxy[i]=center
                radius = int(radius)
                results[i+3]=radius #i = 3,4 - радіус для зовнішнього і внутрішнього контурів
                #cv2.circle(im1,center,radius, clr, 1)


    if len(smoothened)>=2:
        results[5] = cxy[1][0] #x0-меньшого контура
        results[6] = cxy[1][1] #y0-меньшого контуру
        d=math.dist(cxy[0],cxy[1])
        results[2]=d
        sts.res_contours=[smoothened[0],smoothened[1]]

    CycleNozzleAnalyzer(results) # Запис результатів в чергу для отримання середнього значення
    return frame


def ExtractScale():
    # На вході беремо або готовий останній фрейм??, або зчитуємо примусово і робимо йому обрізку окремою функцією
    # Запускаємо ф-цію, яка витягує 2 найбільші контури (нова, бо треба розділити формування контурів і формування картинки)
    pass



def CycleNozzleAnalyzer(results):
    sts.results.enqueue(results)

    # Заміряєм параметри в абсолютних значення, якщо хоч 1 з 3х  не відповідає True, то фіксуємо їх.
    # Витягуємо середні значення
    tmp = sts.results.average()
    if tmp[0]>sts.results.max[0]: sts.results.max[0]=tmp[0]
    if tmp[1]>sts.results.max[1]: sts.results.max[1]=tmp[1]
    if tmp[2]<sts.results.max[2]: sts.results.max[2]=tmp[2]

    if CheckValues()[0]==False:
        # prepair next iteration
        pass




# Перевірка набору значень відносно критерія. Беремо масив трьох значень, повертаємо масив трьох логічних значень
# Можливо треба засунути всередину класа
def CheckValues():
    result=[False]*3
    tmp = sts.results.lastavg
    if tmp[0]>0.8  : result[0] = True
    if tmp[1]>0.85 : result[1] = True
    if tmp[2]<10   : result[2] = True
    return math.prod(result), result


# Перетворення словаря в клас
class Dict2Class(object):
    def __init__(self, my_dict):
        for key in my_dict:
            setattr(self, key, my_dict[key])




def showparams(frame):
    cv2.putText(frame, sts.JSON, (600, 600), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    return frame


def NozzleAnalyzeStart(material: int, nozzletype: int):
    ErrorStr=""
    if material not in (1, 2, None):
            ErrorStr+="Material must be 1 (nickel), 2 (copper) or null. "
    if nozzletype not in (1, 2, None):
            ErrorStr+="Nozzletype must be 1, 2 or null. "
    if len(ErrorStr)>0:
        return False, ErrorStr


    sts.res_contours.clear()
    vid.LoadParamsFromFile('CONF\CamNozzle.json') #setting cam settings
    job.setStart(job.RequestNozzle,4)
    return True, job.statejson



#Auto - знаходити промінь і підсвічувати його зеленим чи червоним колом навколо
#BeamAuto - знаходити промінь і підсвічувати його зеленим чи червоним коло навколо
#Show - показувати морду чи ні
def BeamAnalyzeStart(Auto : bool = None, Show : bool = True):
    ErrorStr=""
    if Auto not in (False, True, None):
            ErrorStr+="'auto' must be Boolean.\n"
    #if Grid not in (False, True, None):
    #        ErrorStr+="'grid' must be Boolean.\n"
    if Show not in (False, True, None):
            ErrorStr+="'show' must be Boolean.\n"
    if len(ErrorStr)>0:
        return False, ErrorStr
        #return InvalidParams(ErrorStr)

    vid.LoadParamsFromFile('CONF\CamBeam.json')
    if Auto:        sts.IN_BeamAuto=True
    else:           sts.IN_BeamAuto=False

    if Show:
        sts.GuiNoWait = False
        queue1.put('GuiShow')
        job.setStart(job.RequestBeamMANUAL,60)
    else:
        sts.GuiNoWait = True
        job.setStart(job.RequestBeamAUTO, 1)
    return True, job.statejson






def GetNozzleStatus(CircNewMin : float, CircGoodMin: float, value: float):
    if value >= CircNewMin:
        return 'NEW',  4
    elif value >= CircGoodMin:
        return 'GOOD', 2
    elif value >= 0.1:
        return 'BAD',  1
    else:
        return 'NOT FOUND', 0


def snapshot(manual = False, name = None, readyframe = None, bwframe = None):
    if not manual and not cfg('autoshots'):
        return

    ret, frame = vid.get_frame(True) #getting new one. Need when no Gui Active
    prefix = "Snapshots/"
    if name!=None:
        print(f"Camera capture to: {path}")
        prefix += name
    else:
        prefix += time.strftime("%d-%m-%Y-%H-%M-%S")

    if ret: #OK
        cv2.imwrite(prefix + "-rawframe.jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        #saving threshed
        imgray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(imgray, 150, 200, cv2.THRESH_BINARY)
        if ret:
            cv2.imwrite(prefix + "-bw.png", thresh)



    if readyframe is not None:
        cv2.imwrite(prefix + '-artframe.jpg', cv2.cvtColor(readyframe, cv2.COLOR_RGB2BGR))





def CreateOSD(image, data, keys, left, top, right, bottom, align="center"):
    current_datetime = datetime.datetime.now()

    # Format it as a string
    text = current_datetime.strftime('%d.%m.%Y %H:%M') + '. \n'


    #data = json.loads(json_data) #string->dictionary
    text += ", ".join([f"{key}={value}" for key, value in data.items() if key in keys])


    # Convert coordinates from fractions to absolute values
    height, width, _ = image.shape
    left, top, right, bottom = int(left * width), int(top * height), int(right * width), int(bottom * height)


    # Box Around
    cv2.rectangle(image, (left,top), (right,bottom), (255,255,255), 1, lineType=cv2.LINE_AA)

    # New box for text with indent
    indent = 4
    left+=indent
    top+=indent
    right-=indent
    bottom-=indent

    # Define font properties
    #font = cv2.FONT_HERSHEY_SIMPLEX
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 0.75
    font_thickness = 1

    line_spacing = int(2 * cv2.getTextSize(text, font, font_scale, font_thickness)[0][1])
    color = (200, 200, 200)

    # Split text into lines and wrap to fit within rectangle
    words = text.split()
    lines = []
    line = ""
    for word in words:
        if '\n' in word: #шось не дуже працює
            line += word.split('\n')[0]
            lines.append(line)
            line = word.split('\n')[1] + " "
        elif cv2.getTextSize(line + word, font, font_scale, font_thickness)[0][0] > right - left:
            lines.append(line)
            line = word + " "
        else:
            line += word + " "
    lines.append(line)

    # Draw text onto image, adding line spacing between lines
    y = top + int(0.5 * (bottom - top - line_spacing * (len(lines) - 1)))
    for line in lines:
        (w, h), _ = cv2.getTextSize(line, font, font_scale, font_thickness)

        if align == "center":
            x = int(0.5 * (left + right - w))
        elif align == "left":
            x = left
        elif align == "right":
            x = right - w

        cv2.putText(image, line, (x, y), font, font_scale, color, font_thickness, cv2.LINE_AA)
        y += line_spacing


##    # Create a transparent overlay image
##    overlay = image.copy()
##    cv2.rectangle(overlay, (0, 0), (overlay.shape[1], overlay.shape[0]), (0, 0, 0, 128), -1)
##    # Add the text to the overlay image
##    cv2.putText(overlay, 'Text over frame', (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)
##    # Blend the overlay image with the loaded image
##    result = cv2.addWeighted(overlay, 1, image, 1, 0)
##    return result
    return image


def main():
    pass




# Set up logging configuration
logging.basicConfig(filename='NozzleAnalyzer.log', level=logging.INFO, format='%(asctime)s %(message)s')

font = cv2.FONT_HERSHEY_SIMPLEX
queue1 = queue.Queue()
cfg = Config() #створюємо налаштування
sts = Status() #створюємо поточні дані
job = CommandStatus() #статус останньої операції

# open video source (trying to open the computer webcam)
# створюємо і запускаємо відео (клас роботи з вебкамерою)
vid = MyVideoCapture(cfg('cam.selected'))

# Global flag to signal threads to stop
stop_threads = False

if __name__ == '__main__':
    main()




