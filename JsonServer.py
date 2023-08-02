# This module create JSON-RPC Server
from jsonrpcserver import method, Result, Success, serve, dispatch, request, Error, InvalidParams
import os, sys
import concurrent.futures

from Main import main as GUI_launch
from Service import queue1, ExtractScale, sts, cfg, job, vid, NozzleAnalyzeStart, BeamAnalyzeStart, snapshot, stop_threads

import pystray
import PIL
import json
import time
import wmi

from http.server import HTTPServer #BaseHTTPRequestHandler, HTTPServer

#state = False
SCode = 'OK' #!!таке шось, треба одбудмати логіку, що нам повертати якщо це запит без аналізу


@method
def CamReady() -> Result:
    if vid.isReady():
        return Success(SCode)
    else:
        return Error(-1,"Camera not initialized", "Camera initializition error, check the USB cable") #camera is not initialized

@method
def CamReset() -> Result:
    vid.reset()
    return Success(SCode) #possibly some time change  that camera is ready


@method
def CamCapture(FileName: str = None) -> Result: #зберігаємо тільки сире зображення
    snapshot(True, FileName)
    return Success(SCode)


# Запит на аналіз і зберігання коефіцієнта градуювання "nozzle.gradescale" і точки Zero
@method
def Calibrate(nozzlesize: float)->Result:
    # коефіцієнт - це діаметр описаного кола відносно внутршнього отвору %InnerDiameterPX / %nozzlesize (кількість пікселів на мм)

    # Dispatch виконує запит всередині сервера і повертає текст відповіді
    response_str = dispatch('{"jsonrpc": "2.0", "method": "RunNozzleAnalyze", "params": [1,1],  "id": 1}')

    # Convert the JSON response string to a Python dictionary
    response_dict = json.loads(response_str)
    if "result" in response_dict:
        root = response_dict["result"]
        if root['InnerStatusId']==4: # Nozzle is NEW
            a=cfg.conf['nozzle.gradescale'] = root['InnerDiameterPX']/nozzlesize
            b=cfg.conf['nozzle.x0'] = root['InnerX0'] + cfg.conf['crop.left']
            c=cfg.conf['nozzle.y0'] = root['InnerY0'] + cfg.conf['crop.top']
            print(f'Calibrated. Scale={a}, Z0:({b},{c})')
            return Success(SCode)

    ##error = response_dict["error"]
    return Error(-16,'Scale calibration error','Scale/zero calibration error. Nozzle hole is not round enough')
    #return error


def Wait4Result(stoptime):
    i=0
    step=0.2
    timeout = False
    while not(job.isComplete()):
        time.sleep(step)
        i+=step
        if i>=stoptime:
            timeout = True # час stoptime сек. минув!!!
            if job.isWork():
                print("TimeOut happened!!!")
                job.setAbort()
                return Error(-16, "Operation timeout")

    #result=job.ResultsCreate()
    #return Success(result)
    return Success(job.result)



@method
def RunNozzleAnalyze(material: int, nozzletype: int)->Result:
    print('RunNozzleAnalyze')
    ret, error_text = CheckError()
    if ret: return error_text


    start_ok, start_result = NozzleAnalyzeStart(material, nozzletype)
    if not(start_ok):
        return Error(start_result)
    else:
        return Wait4Result(8) #і очікує і формує правильну відповідь


@method
def RunBeamAnalyze()->Result:
    ret, error_text = CheckError()
    if ret: return error_text

    print('RunBeamAnalyze')
    start_ok, start_result = BeamAnalyzeStart(Auto = True, Show = False) #!!!Треба потім з 1єї функції зробити 2!
    if start_ok:
        return Wait4Result(2) #і очікує і формує правильну відповідь
    else:
        return Error(start_result)


@method
def RunBeamCentering()->Result:
    ret, error_text = CheckError()
    if ret: return error_text

    queue1.put('ShowButtons')

    print('RunBeamAnalyze')
    start_ok, start_result = BeamAnalyzeStart(Auto = False, Show = True) #!!!Треба потім з 1єї функції зробити 2!
    if start_ok:
        return Wait4Result(60) #і очікує і формує правильну відповідь
    else:
        return Error(start_result)



# Якщо шось не так - тут створюємо помилку
def CheckError()->Result:
    err_exist = not(vid.isReady())
    if err_exist:
        return err_exist, Error(-1,"Camera not initialized", "Camera initializition error, check the USB cable") #camera is not initialized
    else:
        return False, None


@method
def ConfigShow()->Result:
    #queue1.put('ConfigShow')  #Мені дуже не подобається це, треба знайти нормальний спосіб напряму пробиватися к екземпляру об'єкта
    GuiShowConfig()
    return Success(SCode)

@method
def ConfigHide()->Result:
    queue1.put('ConfigHide')  #Мені дуже не подобається це, треба знайти нормальний спосіб напряму пробиватися к екземпляру об'єкта
    return Success(SCode)

@method
def GuiShow(Buttons: bool = None, Config: bool = None)->Result:
    print('GuiShow')
    sts.IN_CameraShow = True
    if Buttons:
        queue1.put('ShowButtons')
    else:
        queue1.put('HideButtons')
    if Config:
        queue1.put('ConfigShow')
    else:
        queue1.put('ConfigHide')

    queue1.put('GuiShow')
    return Success(SCode)

def GuiShowClick():
    GuiShow(False, False)

def GuiShowConfig():
    GuiShow(False, True)


@method
def ParamsAll()->Result:
    return Success(sts.JSON)

@method
def GuiMaximize()->Result:
    queue1.put('Maximize')  #Мені дуже не подобається це, треба знайти нормальний спосіб напряму пробиватися к екземпляру об'єкта
    return Success(SCode)

@method
def GuiStatus()->Result: #повертаємо статус вікна
    return Success(SCode)


@method
def GuiHide()->Result:
    queue1.put('GuiHide')
    return Success(SCode)


@method
def MsgBox(text: str)->Result:
    print(text)
    queue1.put('MsgBox ' + str(text))
    return Success(SCode)


@method
def StopAll()->Result:
    print('Stop GUI and Server')
    Exit()
    return Success(SCode) #never happened


##@method
##def GuiStart()->Result:
##    GUI = threading.Thread(target=GUI_launch)
##    GUI.start()
##    return Success(SCode)


def SystemExit():
    cfg.save_cfg()

    queue1.put('GuiStop')
    # To close all threads, cancel all the submitted tasks
    #GUI.cancel()
    print("Stop GUI")

    icon.stop() #Глушимо іконку
    print("Stop icon")

    #del vid #правильно видаляємо об'єкт камери, обробник всередині
    vid.shutdown() #використовуємо це, бо якщо del vid - далі не йдемо

##    # Call the garbage collector to destroy the object
##    import gc
##    gc.collect()

    # Shutdown the executor, allowing running threads to finish
    executor.shutdown(wait=True)
    print("All threads have been closed. Total shutdown")


    #sys.exit(1) #!!ПОКИ ЩО НЕ ПРАЦЮЄ, ТРЕБА РОБИТИ ЗАГЛУШЕННЯ ДОЧІРНІХ threads
    os._exit(1) # Працюємо як рубильник


@method
def ping() -> Result:
    print('ping')
    return Success(SCode)


##def on_clicked(icon, item):
##    global state
##    state = not item.checked



# Create a ThreadPoolExecutor
executor = concurrent.futures.ThreadPoolExecutor()

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    print('Frozen script')
    count=0
    if "NozzleAnalyzer.exe" in [ x.Name for x in wmi.WMI().Win32_Process() ]: #рахуємо скільки "NozzleAnalyzer.exe" у нас в системі
        count+=1
    if count>1:
        sys.exit(1) #тут
        #os._exit(1)
    application_path = os.path.dirname(os.path.realpath(sys.executable))
elif __file__:
    print('Live script')
    application_path = os.path.dirname(__file__)

SEPARATOR = pystray.MenuItem('- - - -', None)
print(os.getcwd())
image = PIL.Image.open("IMG\laser3.png")
menu = (pystray.MenuItem('Config', action=GuiShowConfig, default=False),
        pystray.MenuItem('Show GUI', action=GuiShowClick, default=True),
        pystray.MenuItem(SEPARATOR, None),
        pystray.MenuItem('Stop && Exit ', SystemExit),
        #pystray.MenuItem('On TOP', on_clicked, checked=lambda item: state)
        )
icon = pystray.Icon("test", image, "Nozzle Scope", menu)
#icon.title="New title for icon"

if __name__ == "__main__":
    icon.run_detached()

    # Submit tasks to the executor and store the returned Future objects
    GUI = executor.submit(GUI_launch) #, args1)

    # Start the JSON-RPC server
    #server = serve(port=6000) #Це не працює - метод serve не залишає посилання на об'єкт сервера!!!
    # проблема Є і внесена в Git, автор обіцяв вирішити її наступній версії
    # https://github.com/explodinglabs/jsonrpcserver/issues/264
    # Always shut down server when using serve()

    print('Starting JSON-RPC server')
    serve(port=6000)
