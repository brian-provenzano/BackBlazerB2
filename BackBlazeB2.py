'''
Personal fun creating a BackBlaze B2 library using the B2 API

only supports basic bucket operations at this point; minimally tested - WIP

B2 API here:
https://www.backblaze.com/b2/docs/

'''

#--3rd party - see readme for pip install
import requests

#--std mod/libs
#import base64
import os
import json
import time
from enum import Enum

class BackBlazeB2(object):

    def __init__(self,accountId=None,applicationKey=None,debug=False):
        #look for env variables if they exist
        if accountId is None or applicationKey is None:
            accountId = os.environ.get('B2_ACCOUNTID', None)
            applicationKey = os.environ.get('B2_APPLICATIONKEY', None)

        if accountId is None:
            raise ValueError
        if applicationKey is None:
            raise ValueError

        self.accountId = accountId
        self.applicationKey = applicationKey
        self.connection = Connection(accountId,applicationKey,debug)
        self.debug = debug


    def IsAuthorized(self):
        if self.connection.IsAuthorized == True:
            return True
        else:
            return False

    @property
    def Buckets(self):
        return B2Buckets(self.connection)


class B2Bucket(object):
    '''
    A Backblaze B2 bucket
    '''

    def __init__(self, connection, bucketId, name, b2type, revision, size=0, sizeHumanReadable=""):
        self.bucketId = bucketId
        self.connection = connection
        self.name = name
        self.b2type = b2type
        self.revision = revision
        self.size = size
        self.sizeHumanReadable = sizeHumanReadable


    def Delete(self):
        '''
        delete the specified b2 bucket
        '''
        print("deleting bucket :{0}".format(self.bucketId))
        #TODO - delete from our local bucket cache (Buckets )
        try:
            headers = { 'Authorization' : self.connection.authorizationToken }
            body = json.dumps({ 'bucketId' : self.bucketId, 'accountId' : self.connection.accountId })
            response = requests.post("{0}/b2api/v1/b2_delete_bucket".format(self.connection.apiUrl), data=body, headers=headers)
            response.raise_for_status()
            jsonResult = response.json()
            if response.status_code == 200:
                Message.Show(MessageType.INFO, "Bucket [{0}] deleted".format(self.bucketId))

                if self.connection.debug:
                    print(jsonResult)
            elif response.status_code == 400:
                 Message.Show(MessageType.ERROR, jsonResult)
            else:
                Message.Show(MessageType.ERROR,
                        "Server did not return status 200 - returned [{0}] ".format(response.status_code))

        #throw the base request ex so we can continue on any error from requests module
        except requests.exceptions.RequestException as re:
            Message.Show(MessageType.ERROR, "Trying to delete b2 bucket", re)


class B2Buckets(object):

    def __init__(self,connection):
        self._bucketNames = {}
        self._bucketIds = {}
        self.connection = connection
        self.buckets = []
        self.__bucketsBytesTotal = 0
        #self.__RefreshUsage()


    #TODO - hack for now to convert - move this to util class; handle more elgantly
    def __SizeHumanReadable(self,nbytes):
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        i = 0
        while nbytes >= 1024 and i < len(suffixes)-1:
            nbytes /= 1024.
            i += 1
        f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
        return '%s %s' % (f, suffixes[i])


    def GetUsage(self, bucketName=None, bucketId=None, humanReadable=False):
        """ 
        Get total storage usage of all, or specific bucket
        """
        if humanReadable:
            return self.__SizeHumanReadable(self.__RefreshUsage(bucketName,bucketId))
        else:
            return self.__RefreshUsage(bucketName,bucketId)


    def All(self):
        '''
        return collection of buckets
        '''
        self.__RefreshBuckets()
        return self.buckets


    def Get(self, bucketName=None,bucketId=None):
        ''' 
        return a specific B2Bucket identified by id or name
        '''
        self.__RefreshBuckets()
        if bucketName is not None:
            return self._bucketNames.get(bucketName,"no such bucket name")
        elif bucketId is not None:
            return self._bucketIds.get(bucketId, "no such bucket id")
        else:
            raise ValueError("Must specify bucket name or bucket id")


    def __RefreshUsage(self, bucketName=None, bucketId=None, fullRefresh=True):

        if fullRefresh:
            self.__RefreshBuckets()

        #TODO - lookup usage for individual bucketName/Id

        bucketsBytesTotal = 0
        for key in self._bucketIds.keys():
            try:
                headers = { 'Authorization' : self.connection.authorizationToken }
                body = json.dumps({ 'bucketId' : key, 'maxFileCount' : 999 })
                response = requests.post("{0}/b2api/v1/b2_list_file_names".format(self.connection.apiUrl), data=body, headers=headers)
                response.raise_for_status()
                if response.status_code == 200:
                    jsonResult = response.json()
                    filesTotal = 0
                    for count,item in enumerate(jsonResult["files"], start=0):
                        bucketsBytesTotal += item["contentLength"]
                        if self.connection.debug:
                            print("{0} - {1} [{2}]".format(item["fileName"],item["contentLength"],self.__SizeHumanReadable(item["contentLength"])))
                            filesTotal += count
                    if self.connection.debug:
                        print("---------\n{0}\n---------".format(jsonResult))
                        print("number of files: {0}".format(filesTotal))
                else:
                    Message.Show(MessageType.ERROR,
                            "Server did not return status 200 - returned [{0}] ".format(response.status_code))

            #throw the base request ex so we can continue on any error from requests module
            except requests.exceptions.RequestException as re:
                Message.Show(MessageType.ERROR, "Trying to list files at b2", re)

            if self.connection.debug:
                print("DEBUG: Bytes total : {0}".format(bucketsBytesTotal))

            self.__bucketsBytesTotal = bucketsBytesTotal
            (self._bucketIds[key]).size = bucketsBytesTotal
            (self._bucketNames[(self._bucketIds[key]).name]).size = bucketsBytesTotal
            (self._bucketIds[key]).sizeHumanReadable = self.__SizeHumanReadable(bucketsBytesTotal)
            (self._bucketNames[(self._bucketIds[key]).name]).sizeHumanReadable = self.__SizeHumanReadable(bucketsBytesTotal)
        
        return self.__bucketsBytesTotal 

    def __RefreshBuckets(self):
        try:
            headers = { 'Authorization' : self.connection.authorizationToken }
            body = json.dumps({ 'accountId' : self.connection.accountId  })
            response = requests.post("{0}/b2api/v1/b2_list_buckets".format(self.connection.apiUrl), data=body, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                jsonResult = response.json()
                if self.connection.debug:
                    print(jsonResult)
                self.buckets.clear()
                self._bucketIds.clear()
                self._bucketNames.clear()
                for item in jsonResult["buckets"]:
                    bucket = B2Bucket(self.connection, item["bucketId"], item["bucketName"], item["bucketType"], item["revision"])
                    self.buckets.append(bucket)
                    self._bucketNames[item["bucketName"]] = bucket
                    self._bucketIds[item["bucketId"]] = bucket
            else:
                Message.Show(MessageType.ERROR,
                        "Server did not return status 200 - returned [{0}] ".format(response.status_code))

        #throw the base request ex so we can continue on any error from requests module
        except requests.exceptions.RequestException as re:
            Message.Show(MessageType.ERROR, "Trying to list buckets at b2", re)

        self.__RefreshUsage(fullRefresh=False)


class B2File(object):
    '''
    A Backblaze B2 file
    '''
    def __init__(self, recId, name, contentType, contentSha1, uploadTimestamp):
        self.recId = recId
        self.name = name
        self.contentType = contentType
        self.contentSha1 = contentSha1
        self.uploadTimestamp = uploadTimestamp

    def Delete(self):
        '''
        delete the b2 file
        '''
        pass

class B2Exception(object):
    #TODO - custom execptions for B2
    pass


class Connection(object):

    authorizationToken = ""
    apiUrl = ""
    downloadUrl = ""
    recommendedPartSize = ""
    absoluteMinimumPartSize = ""
    __isAuthorized = False
    b2AuthUrl = "https://api.backblazeb2.com/b2api/v1/b2_authorize_account"
   
    def __init__(self,accountId,applicationKey,debug):
        self.accountId = accountId
        self.applicationKey = applicationKey
        self.debug = debug
        self.__AuthorizeAccount()
    
    def IsAuthorized(self):
        if self._isAuthorized == True:
            return True
        else:
            return False


    def __AuthorizeAccount(self):
        try:
            # acctString = "{0}:{1}".format(self.accountId, self.applicationKey)
            # acctStringB64Encoded = base64.b64encode(acctString.encode())
            # basicAuthString = "Basic {0}".format(acctStringB64Encoded.decode())
            # headers = { 'Authorization' : basicAuthString }
            #response = requests.get(self.b2AuthUrl,headers=headers)
            response = requests.get(self.b2AuthUrl,auth=(self.accountId,self.applicationKey))
            response.raise_for_status()
            if response.status_code == 200:
                jsonResult = response.json()
                if self.debug:
                    print(jsonResult)
                self.authorizationToken = jsonResult["authorizationToken"]
                self.apiUrl = jsonResult["apiUrl"]
                self.downloadUrl = jsonResult["downloadUrl"]
                self.recommendedPartSize  = jsonResult["recommendedPartSize"]
                self.absoluteMinimumPartSize = jsonResult["absoluteMinimumPartSize"]
                self._isAuthorized = True
            else:
                Message.Show(MessageType.ERROR,
                        "Server did not return status 200 - returned [{0}] ".format(response.status_code))

        #throw the base request ex so we can continue on any error from requests module
        except requests.exceptions.RequestException as re:
            Message.Show(MessageType.ERROR, "Trying to request authorization token from b2", re)


    def MakeRequest(self, authToken):
        #-TODO - maybe wrap up requests module for DRY and easy use ...
        pass


#-- UTILS ----------------------------------------------------------------------------------------------

class MessageType(Enum):
    """ Message type """
    INVALID = 0
    DEBUG = 1
    INFO = 2
    ERROR = 3


class Message(object):

    @staticmethod
    def Show(messageType,friendlyMessage,detailMessage="None"):
        """ prints messages in format we want """
        if messageType == messageType.DEBUG:
            color = fg.YELLOW
            coloroff = style.RESET_ALL
        elif messageType == messageType.INFO:
            color = fg.GREEN
            coloroff = style.RESET_ALL
        elif messageType == messageType.ERROR:
            color = fg.RED
            coloroff = style.RESET_ALL
        else:
            color = ""
            coloroff = ""

        print("{3}[{0}] - {1} - More Details [{2}]{4}".format(str(messageType.name),friendlyMessage,detailMessage,color,coloroff))


# Terminal color definitions - cheap and easy colors for this application
class fg:
    BLACK   = '\033[30m'
    RED     = '\033[31m'
    GREEN   = '\033[32m'
    YELLOW  = '\033[33m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    WHITE   = '\033[37m'
    RESET   = '\033[39m'

class bg:
    BLACK   = '\033[40m'
    RED     = '\033[41m'
    GREEN   = '\033[42m'
    YELLOW  = '\033[43m'
    BLUE    = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN    = '\033[46m'
    WHITE   = '\033[47m'
    RESET   = '\033[49m'

class style:
    BRIGHT    = '\033[1m'
    DIM       = '\033[2m'
    NORMAL    = '\033[22m'
    RESET_ALL = '\033[0m'


def TimeFromFloat(f):
    return time.strftime("%H:%M:%S", time.gmtime(f))


class SimpleTimer(object):
    """ simple timer for util purposes """
    import time
    startTime = 0.0
    StopTime = 0.0
    elapsed = 0.0

    def __init__(self):
        self.startTime = time.time()

    def Stop(self):
        self.StopTime = time.time()

    def GetElapsed(self):
        self.StopTime = time.time()
        self.elapsed = (self.StopTime - self.startTime)
        return self.elapsed

    def PrintSummary(self, doingWhat="do something"):
        return "[ {0} ] Time elapsed {1}".format(TimeFromFloat(self.elapsed),doingWhat)

