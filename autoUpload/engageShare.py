import json
import getpass
from os import name, path, listdir
from pyasn1.type.univ import Null
from pydrive.drive import GoogleDrive 
from pydrive.auth import GoogleAuth
from pydrive.files import ApiRequestError 
CURR_VERSION = 0.1
# This shows an example of a intergration with a possible upload api 
# In this case using google drive
def initalize(settingPath="settings.json",forceRegen=False):
    if path.exists(settingPath) and not forceRegen:
        with open(settingPath,"r") as fp:
            userData = json.load(fp)
            userClass = User_Settings.initFromMap(userData)
    elif forceRegen:
        userClass = User_Settings.generate_default_settings()
    else: 
        raise Exception("No JSON found")
    return userClass

class User_Settings:
    def __init__(self,user,recordingPath,isMobile,platformName,uploadList=[],saveLocation = "settings.json",driveFolderID=None):
        self.user = user
        self.recordingPath = recordingPath
        self.isMobile = isMobile
        self.platformName = platformName
        self.uploadList = uploadList
        self.saveLocation = saveLocation
        self.driveFolderID = driveFolderID
        self.save_settings()
    
    def getIsMobile(self):
        return self.isMobile

    def getDriveFolderID(self):
        return self.driveFolderID
    
    def setDriveFolderID(self,driveFolderID):
        self.driveFolderID = driveFolderID
        self.save_settings()
        
    @classmethod
    def initFromMap(cls,userSettings):
        return cls(userSettings["user"],userSettings["Recording-Path"],userSettings["isMobilePlatform"],userSettings["platformName"],userSettings["upload-list"],driveFolderID=userSettings["driveFolderID"])
    
    @classmethod
    def generate_default_settings(cls,mobile=False,platform="PC", user=getpass.getuser(), **kwargs):
        if "path" not in kwargs:
            if mobile == False:
                userPath = findPCPath(user)
            else:
                raise Exception("Cannot auto find recording path for mobile platforms, \
                            please specifiy where your recordings are saved")
        else:
            userPath = kwargs["path"]
        uploadList = [] if "upload-list" not in kwargs else  kwargs["upload-list"]
        return cls(user,userPath,mobile,platform,uploadList)

    @classmethod
    def generate_empty_settings(cls):
        return cls(getpass.getuser(),None,None,name)


    def returnMap(self):
        return  {"user" : self.user, "Recording-Path" : self.recordingPath, "isMobilePlatform" : self.isMobile, 
                    "platformName" : self.platformName, "upload-list" : self.uploadList, "driveFolderID" : self.driveFolderID}        
    
    def updateUploadList(self,filename):
        self.uploadList.append(filename)
        self.save_settings()

    def getUploadList(self):
        return self.uploadList

    def save_settings(self):
        with open(self.saveLocation,"w") as fp:
            json.dump(self.returnMap(),fp,indent=1)

def findPCPathJSCall(js_callbackk):
    js_callbackk.Call(findPCPath())    

def findPCPath(user=getpass.getuser()):
    if path.exists(path.join("C:\\","Users",user,"Documents","ENGAGE","MyRecordings")):
        return path.join("C:\\","Users",user,"Documents","ENGAGE","MyRecordings")
    elif path.exists(path.join("C:\\","Documents","ENGAGE","MyRecordings")):
        return path.join("C:\\","Documents","ENGAGE","MyRecordings")
    else:
        return ""

def main():
    user_class = initalize(forceRegen=True)
    userSettings = user_class.returnMap()
    for fileName in listdir(userSettings["Recording-Path"]):
        if fileName not in userSettings["upload-list"]:
            if input(fileName + " has been detected but not uploaded \
                \nWould you like to upload? (y/n)") == "y":
                if uploadFile(fileName,userSettings["Recording-Path"]): 
                    user_class.updateUploadList(fileName)
                    print(fileName + " has been uploaded!")


##DONT USE THIS FUNCTION
# api intergration to be decided
def uploadFile(fileName,filePath):
    return True
    # Below code does the authentication 
    # part of the code 
    gauth = GoogleAuth() 
    
    # Creates local webserver and auto 
    # handles authentication. 
    gauth.LocalWebserverAuth()        
    drive = GoogleDrive(gauth) 
    f = drive.CreateFile({'title': fileName}) 
    f.SetContentFile(path.join(filePath, fileName)) 
    try:
        f.Upload() 
    except ApiRequestError as e:
        print(e)
        f = None
        return False
      
    # Due to a known bug in pydrive if we  
    # don't empty the variable used to 
    # upload the files to Google Drive the 
    # file stays open in memory and causes a 
    # memory leak, therefore preventing its  
    # deletion 
    f = None
    return True

if __name__ == "__main__":
    # execute only if run as a script
    main()