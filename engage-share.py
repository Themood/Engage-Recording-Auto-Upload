import json
import getpass
from os import name, path, listdir
CURR_VERSION = 0.1

def initalize(settingPath="settings.json",forceRegen=False):
    if path.exists(settingPath) and not forceRegen:
        with open(settingPath,"r") as fp:
            userData = json.load(fp)
    else:
        userData = generate_settings()
        with open(settingPath,"w") as fp:
            json.dump(userData,fp,indent=1)
    return userData


def generate_settings(mobile=False,platform="PC", user=getpass.getuser(), **kwargs):
    if "path" not in kwargs:
        if mobile == False:
            userPath = findPCPath(user)
        else:
            raise Exception("Cannot auto find recording path for mobile platforms, \
                        please specifiy where your recordings are saved")
    else:
        userPath = kwargs["path"]
    uploadList = [] if "upload-list" not in kwargs else  kwargs["upload-list"]
    userData = {"user" : user, "Recording-Path" : userPath, "isMobilePlatform" : mobile, 
                "platformName" : platform, "upload-list" : uploadList}
    return userData


def findPCPath(user):
    if path.exists(path.join("C:\\","Users",user,"Documents","ENGAGE","MyRecordings")):
        return path.join("C:\\","Users",user,"Documents","ENGAGE","MyRecordings")
    elif path.exists(path.join("C:\\","Documents","ENGAGE","MyRecordings")):
        return path.join("C:\\","Documents","ENGAGE","MyRecordings")
    else:
        raise Exception("MyRecordings folder not found in its default locations, please \
                        specifiy where your recordings are saved")

def main():
    userSettings = initalize(forceRegen=True);
    for fileName in listdir(userSettings["Recording-Path"]):
        if fileName not in userSettings["upload-list"]:
            if input(fileName + " has been detected but not uploaded \
                \nWould you like to upload? (y/n)") == "y":
                if uploadFile(fileName): userSettings["Recording-Path"].append(fileName) 



# api intergration to be decided
def uploadFile(fileName):
    return False

if __name__ == "__main__":
    # execute only if run as a script
    main()