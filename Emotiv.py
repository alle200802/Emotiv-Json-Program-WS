import ssl
import json
import websocket
import time
from tkinter import *
import urllib.request
try:
    import thread
except ImportError:
    import _thread as thread
id=''
lastMes=None
read=True
token=''
recording=False
URL = "http://192.168.252.189:8000/run/?action=";
lastAct=''


##########################
#######  flow methods	######
##########################


#thismethod shows the traied proflies
def addProfile(ws):
    sendJson('queryHeadsets',{},ws)
    global id
    id=json.loads(waitingForMes())['result'][0]['id']
    sendJson('queryProfile', {'_auth': ''},ws)
    waitingForMes()
    arr=json.loads(lastMes)['result']
    names=''
    for i in arr:
        names+=i
    print('there are'+str(len(arr))+'  locally saved proflies '+names)

#this method manages the insight proflies
def profileSettings(ws):
    pName = input('write the proflie name\n')
    print('insert the mod')
    print('“create”	create new training profile\n\
    “save”	save current training data to profile\n\
    “load”	load training data from profile\n\
    “upload”	upload training profile to server\n\
    “delete”	remove training profile on the local machine')
    status = input('insert a status\n')
    sendJson('setupProfile', {'_auth': '', 'headset': id, 'profile': pName, 'status': status}, ws)
    waitingForMes()
    try:
        json.loads(lastMes)['error']
    except:
        print('we correctly did it  ' + status + ' of profile ' + pName)
    finally:
        if  not 'Y' == input('Do you want to further modify the profile ?(Y/n)\n').upper():
            return
        else:
            return profileSettings(ws)

#this is the method that we use to communicate with PI-Car 
def connect(action):
    global  lastAcrt
    if(not lastAcrt==action):
        lastAcrt=action
        print(action)
        urllib.request.urlopen(URL+action).getcode()
#this method reads stream data and creates a littlw windows to stop data stream
def startRecording(ws):
    sendJson('subscribe', {'_auth': '', "streams": {"com","fac"}}, ws)
    waitingForMes()
    global recording
    recording=True
    root = Tk()
    container = Frame(root)
    container.pack()
    def command():
        sendJson('unsubscribe', {'_auth': '', "streams": {"com","fac"}}, ws)
        root.destroy()
        global recording
        recording=False
    button = Button(container, text='close',command= lambda:command())
    button.pack()
    root.mainloop()

#this method is used to train the insatit
def startTraining(ws):
    #attiva il sys
    #mentalCommand
    list=['mentalCommand','facialExpression']
    detection=list[int(input('Do you want to train mental command(0) or factial expression(1)\n'))]
    sendJson('subscribe',{ '_auth': '', 'streams': {'sys'}} , ws)
    waitingForMes()
    #help
    sendJson('getDetectionInfo', {'detection': detection}, ws)
    print('what do you want to train?')
    for i in json.loads(waitingForMes())['result']['actions']:
        print(i)
    training = input()
    sendJson('training', {'_auth': 'abcd', 'detection': detection, 'action': training, 'status': 'start'}, ws)
    try:
        json.loads(waitingForMes())['sys']
    except:
        waitingForMes()
    print('start training for '+training)
    waitingForMes()
    value= 'accept'
    if not (input('do you want to accept this training?(Y/N)\n').upper() == 'Y'):
        value='reject'
    sendJson('training', {'_auth': 'abcd', 'detection': detection, 'action': training, 'status': value}, ws)
    waitingForMes()
    print('training '+value)
    if input('Do you want to continue training?\n').upper()=='Y':
        return startTraining(ws)

#this method creates a token and it saves it to use it when a json is sent and it automatically inserts the token in '_auth' voice and create a new session
def setup(ws):
    print('create tocken and create session')
    sendJson('authorize', {},ws)
    global token
    token = json.loads(waitingForMes() )['result']['_auth']
    sendJson('createSession',{ '_auth': '', 'status': 'open'},ws)
    id=json.loads(waitingForMes())['result']['headset']['id']

#read the method comment
def getJson(method,parameters):
    #heading
    out='{"jsonrpc": "2.0",'
    #method
    out+='"method":"'+str(method)+'",'
    #parameters
    if not parameters== None:
        out+='"params": {'
        addpar=False
        for name, value in parameters.items():
            #inserts the token values
            if not type(value)==set:
                global token
                if not (token==''):
                    if name=='_auth':
                        value=token
                addpar=True
                out+='"'+str(name)+'":"'+str(value)+'",'
            else:
                val=''
                for tmp in value:
                    val+='"'+tmp+'",'
                out+='"'+str(name)+'":['+val[:-1]+'],'
        if(addpar):
            out=out[:-1]
        out+='},'
    out+='"id": 1}'
    return out

#########################
####### ws methods #######
#########################


#It's the method called when on_open is terminated
def close(ws):
    ws.close()
    print("thread terminating...")

#It's the method called  when a message is sent
def send(string,ws):
    ws.send(string)

#It's the method called when a Json is sent
def sendJson(method,params,ws):
    send(getJson(method,params),ws)

#It's the method called when a message is received
def on_message(ws, message):
    if recording:
        print(message)
        #this comment is to send action to Pi-Car
        '''  try:
            arr=json.loads(message)['fac']
        except:
            arr=json.loads(message)['com']
            if arr[0]=='neutral' :
                connect('camready')
            elif arr[0]=='left':
                connect('camleft')
            else:
                connect('camright')
	    '''
    else:
        global lastMes,read
        read=False
        lastMes=message


#It's the method called when a message is received
def on_error(ws, error):
    print(error)
	
#It's the method called when a ws is closed
def on_close(ws):
    print("### closed ###")

##It's the method called when are waiting for a message
def waitingForMes():
    for i in range(100):
        time.sleep(0.1)
        global read,lastMes
        if not read:
            read=True
            if str(lastMes).startswith('{"error":'):
                raise Exception(lastMes)
            else:
                return lastMes

#this is the method called when ws is open 
def on_open(ws):
    def run(*args):
        setup(ws)
        while True:
            i=int(input('what do you want to do :start training (1),begin the data stream (2),manage the proflies (3), quit (4)\n'))
            try :
                if i==1:
                    startTraining(ws)
                elif i==2:
                    startRecording(ws)
                elif i == 3:
                    addProfile(ws)
                    profileSettings(ws)
                else:
                    break
            except Exception as e:
                inp=not str(input('do you want continue despite the error '+e.__str__()+'\n')).upper()=='Y'
                if inp:
                    break
        close(ws)
    thread.start_new_thread(run, ())

#the main methd
if  __name__ == "__main__":
    ws = websocket.WebSocketApp("wss://emotivcortex.com:54321",
                            on_message = on_message,
                            on_error = on_error,
                            on_close = on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
