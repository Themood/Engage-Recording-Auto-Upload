# Tutorial example. Doesn't depend on any third party GUI framework.
# Tested with CEF Python v57.0+

from logging import raiseExceptions
from cefpython3 import cefpython as cef
from os import name, listdir,remove
from os import path as p
import time
import tkinter as tk
from tkinter import filedialog
import engageShare as es
import base64
import platform
import sys
import threading
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
from pydrive.files import ApiRequestError
from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen

external = None
KEYFILE = "androidkey"
def main():
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    # To change user agent use either "product_version"
    # or "user_agent" options. Explained in Tutorial in
    # "Change user agent string" section.
    settings = {
        # "product_version": "MyProduct/10.00",
        # "user_agent": "MyAgent/20.00 MyProduct/10.00",
    }
    cef.Initialize(settings=settings)
    #set_global_handler()

    browser = cef.CreateBrowserSync(url="file:///mainlayout.html",
                                    window_title="Engage share")
    set_client_handlers(browser)
    global external
    external = External(browser)
    cef.MessageLoop()
    cef.Shutdown()

def fileBrowserPopup(startPath, js_callback=None):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askdirectory(initialdir = startPath) 
    if js_callback:
        js_callback.Call(file_path)
    else: return file_path   

def check_versions():
    ver = cef.GetVersion()
    print("[tutorial.py] CEF Python {ver}".format(ver=ver["version"]))
    print("[tutorial.py] Chromium {ver}".format(ver=ver["chrome_version"]))
    print("[tutorial.py] CEF {ver}".format(ver=ver["cef_version"]))
    print("[tutorial.py] Python {ver} {arch}".format(
           ver=platform.python_version(),
           arch=platform.architecture()[0]))
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"


def html_to_data_uri(html, js_callback=None):
    # This function is called in two ways:
    # 1. From Python: in this case value is returned
    # 2. From Javascript: in this case value cannot be returned because
    #    inter-process messaging is asynchronous, so must return value
    #    by calling js_callback.
    html = html.encode("utf-8", "replace")
    b64 = base64.b64encode(html).decode("utf-8", "replace")
    ret = "data:text/html;base64,{data}".format(data=b64)
    if js_callback:
        js_print(js_callback.GetFrame().GetBrowser(),
                 "Python", "html_to_data_uri",
                 "Called from Javascript. Will call Javascript callback now.")
        js_callback.Call(ret)
    else:
        return ret


""" def set_global_handler():
    # A global handler is a special handler for callbacks that
    # must be set before Browser is created using
    # SetGlobalClientCallback() method.
    global_handler = GlobalHandler()
    cef.SetGlobalClientCallback("OnAfterCreated",
                                global_handler.OnAfterCreated) """


def set_client_handlers(browser):
    client_handlers = [DisplayHandler()]#[LoadHandler(), DisplayHandler()]
    for handler in client_handlers:
        browser.SetClientHandler(handler)

def js_print(browser, lang, event, msg):
    # Execute Javascript function "js_print"
    if (event == "New file detected "):
        browser.ExecuteFunction("file_button",lang,event,msg)
    else:
        browser.ExecuteFunction("js_print", lang, event, msg)
        
def getFileFromDroid(directory,fileName):
    try:
        adbkey = KEYFILE
        with open(adbkey) as f:
            priv = f.read()
        with open(adbkey + '.pub') as f:
            pub = f.read()
        signer = PythonRSASigner(pub, priv)
        device2 = AdbDeviceUsb()

        device2.connect(rsa_keys=[signer], auth_timeout_s=5)
        path = directory + fileName
        device2.pull(path,fileName)
        return True
    except:
        raiseExceptions("FILE NOT ABLE TO GET")


""" class LoadHandler(object):
    def OnLoadingStateChange(self, browser, is_loading, **_):
        if not is_loading:
            # Loading is complete. DOM is ready.
            js_print(browser, "Python", "OnLoadingStateChange",
                     "Loading is complete") """


class DisplayHandler(object):
    def OnConsoleMessage(self, browser, message, **_):
        """Called to display a console message."""
        # This will intercept js errors, see comments in OnAfterCreated
        if "error" in message.lower() or "uncaught" in message.lower():
            # Prevent infinite recurrence in case something went wrong
            if "js_print is not defined" in message.lower():
                if hasattr(self, "js_print_is_not_defined"):
                    print("Python: OnConsoleMessage: "
                          "Intercepted Javascript error: "+message)
                    return
                else:
                    self.js_print_is_not_defined = True
            # Delay print by 0.5 sec, because js_print may not be
            # available yet due to DOM not ready.
            print("JS ERROR: " + message)
           

class External(object):
    def __init__(self, browser):
        self.browser = browser
        self.settings_found = True 
        self.driveAuth = None
        try:
            self.user_settings = es.initalize(forceRegen=False)
        except:
            self.user_settings = es.User_Settings.generate_empty_settings()
            self.settings_found = False
        finally:
            self.binding = self.set_javascript_bindings()

    def PCPath(self,EngagePath):
        self.user_settings = es.User_Settings.generate_default_settings(path=EngagePath)
        self.settings_found = True
        self.binding = self.set_javascript_bindings()


    def checkFolderID(self,folderID):
        if self.driveAuth == None:
            self.driveAuth = DriveInstance()
        drive = self.driveAuth.getDrive()
        folderList = drive.ListFile(
            {'q': "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        for folder in folderList:
            if folder["id"] == folderID:
                return True
        return False

    def setFolderID(self,folderID,js_callback):
        if self.checkFolderID(folderID):
            self.user_settings.setDriveFolderID(folderID)
            js_callback.Call("True")
        else: 
            js_callback.Call("False")
        

    def listFiles(self):
        if (self.user_settings.isMobile):
            self.mobileListFiles()
        else:
            for fileName in listdir(self.user_settings.recordingPath):
                if fileName not in self.user_settings.uploadList:
                    js_print(self.browser,"Python", "New file detected ",
                        fileName)
    
    def mobileInit(self,js_callback):
        adbkey = KEYFILE
        if not p.exists(adbkey):
            keygen(adbkey)
        with open(adbkey) as f:
            priv = f.read()
        with open(adbkey + '.pub') as f:
            pub = f.read()
        signer = PythonRSASigner(pub, priv)
        try:
            device2 = AdbDeviceUsb()
            device2.connect(rsa_keys=[signer], auth_timeout_s=5)
            path = (device2.shell("echo $EXTERNAL_STORAGE")).rstrip() + "/Documents/ENGAGE/MyRecordings/"
            self.user_settings.recordingPath = path
            self.user_settings.isMobile = True
            self.user_settings.platformName = "adb device"
            self.settings_found = True
            self.user_settings.save_settings()
            device2.close()
            js_callback.Call(True)
        except:
            js_callback.Call(False)


    def mobileListFiles(self):
        adbkey = KEYFILE
        with open(adbkey) as f:
            priv = f.read()
        with open(adbkey + '.pub') as f:
            pub = f.read()
        signer = PythonRSASigner(pub, priv)
        device2 = AdbDeviceUsb()

        device2.connect(rsa_keys=[signer], auth_timeout_s=5)
        path = self.user_settings.recordingPath
        IGNOREFILENAMES = [".",".."]
        for file in device2.list(path):
            fileName = (file.filename).decode('utf-8')
            if fileName not in IGNOREFILENAMES:
                js_print(self.browser,"Python", "New file detected ",
                     fileName)

    def set_javascript_bindings(self):
        bindings = cef.JavascriptBindings(
                bindToFrames=False, bindToPopups=False)
        bindings.SetProperty("settings_found",self.settings_found)
        bindings.SetProperty("user", self.user_settings.user)
        bindings.SetProperty("platformName", self.user_settings.platformName)
        bindings.SetProperty("uploadList",  self.user_settings.uploadList)
        bindings.SetFunction("findPCPathJSCall",es.findPCPathJSCall)
        bindings.SetFunction("mobileInit",self.mobileInit)
        bindings.SetFunction("fileBrowserPopup",fileBrowserPopup)
        bindings.SetObject("external", self)
        self.browser.SetJavascriptBindings(bindings)
        return bindings

    def uploadFile(self,fileName):
        # Below code does the authentication 
        # part of the code 
        if self.driveAuth == None:
            self.driveAuth = DriveInstance()
        drive = self.driveAuth.getDrive()
        folderID = self.user_settings.getDriveFolderID()
        #print(folderID)
        if (folderID == None):
            f = drive.CreateFile({'title': fileName})#, "id" : [self.user_settings.getDriveFolderID()]}) 
        else:
            f = drive.CreateFile({'title': fileName,'parents': [{'id': folderID}]})#, "id" : [self.user_settings.getDriveFolderID()]}) 
        if self.user_settings.isMobile:
            getFileFromDroid(self.user_settings.recordingPath,fileName)
            f.SetContentFile(fileName)
        else:
            filePath=self.user_settings.recordingPath
            f.SetContentFile(p.join(filePath, fileName)) 

        try:
                f.Upload() 
        except ApiRequestError as e:
            print(e)
            f = None
            self.browser
            return False
        
        # Due to a known bug in pydrive if we  
        # don't empty the variable used to 
        # upload the files to Google Drive the 
        # file stays open in memory and causes a 
        # memory leak, therefore preventing its  
        # deletion 
        f = None
        self.user_settings.updateUploadList(fileName)
        self.binding = self.set_javascript_bindings()
        self.browser.Reload()
        return True

class DriveInstance:
    def __init__(self):
        self.gauth = GoogleAuth() 
        self.gauth.LocalWebserverAuth()        
        self.drive = GoogleDrive(self.gauth) 
    def getDrive(self):
        return self.drive

if __name__ == '__main__':
    main()

