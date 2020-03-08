import requests as req
from requests.exceptions import HTTPError, RequestException, ConnectionError

import json
from enum import Enum

from .exceptions import ApiException
from .status import Statuses

class MessageType(Enum):
    TEXT  = 1
    VOICE = 2
    
class MessageIDType(Enum):
    MESSAGE_ID = 1
    CHECK_ID   = 2

class Ghasedak:
    """A class used to implement Ghasedak REST API

    Attributes
    ----------
    apikey : str
        The api key used to communicate with the Ghasedak server

    Methods
    -------
    make_request(endpoint, data=None, method='Post')
        Makes a request to the specified endpoint
    """

    def __init__(self, apikey):
        """
        Parameters
        ----------
        apikey : str
            Initilizes apikey for later uses
        """

        self.apikey = apikey
        self.url = 'https://api.ghasedak.io/v2'
      
    def makeRequest(self, endpoint, data = None, method = 'POST'):
        """Make a Request to the specified API endpoint with the given data
            
        Parameters
        ----------
        endpoint : str
            Endpoint used to deliver data to and receive a response
        data : dict, list, tuple, Optional
            Initilizes apikey for later uses (default None)
        method : str, Optional
            Method used to make a request (default POST)

        Raises
        ------
        ApiException: when the api opration has been failed

        Returns
        -------
        json
            The response json which the server gives us
        """

        headers = {
			'Accept': "application/json",
			"Content-Type": "application/x-www-form-urlencoded",
			'charset': "utf-8",
			'apikey': self.apikey
		}


        try:
            response = req.request(method = method,
             url= self.url + endpoint,
             data=data if data is not None else {},
             headers = headers)

            response.raise_for_status() # Check for HTTP request errors
        except ConnectionError as connection_error:
            print(f"[Requests] Connection ERROR: {connection_error}")
            return None
        except HTTPError as http_error:
            print(f"[Requests] HTTP ERROR: {http_error}")
        except RequestException as request_exception:
            print(f"[Requests] Request Exception: {request_exception}")
            return None
        
        res_json = response.json()

        if res_json['result']['code'] == 200:
            return res_json['items']
            
        raise ApiException(res_json['result']['code'], res_json['result']['message'])

    def sendMessage(self, message, receptor, linenumber=None, senddate=None, checkid=None):
        """Send a message to a receptor
            
        Parameters
        ----------
        message : str
            Message to send
        receptor : str
            Receptor of the message 
        linenumber : str, Optional
            Linenumber from which the message will be sent (default first Linenumber from the Ghasedak profile)
        senddate : unixtime, int, str, Optional
            Date in unixtime which the message should be sent
        checkid: str, int, Optional
            Id of the sms for later use with `getSMSStatus` method
        
        Returns
        -------
        boolean
            On failure returns False
        json
            On Success returns the id of message
        """

        data = {}
        data['message'] = str(message)
        data['receptor'] = str(receptor)
        if linenumber is not None: data['linenumber'] = str(linenumber)
        if senddate is not None: data['senddate'] = str(senddate)
        if checkid is not None: data['checkid'] = str(checkid)

        try:
            res = self.makeRequest(endpoint="/sms/send/simple", data=data)
        except ApiException as api_error:
            print(f"[Ghasedak] {api_error}")
            return False

        return res[1]

    def sendOtpVerification(self, otp, receptor, template, type=MessageType.TEXT, checkid=None, **params):
        """Send an OTP message to a receptor
            
        Parameters
        ----------
        otp : str
            one-time-password
        receptor : str, str_list
            Receptor of the message, can be sudo list by seperating Id's with ","
        template : str
            otp template name which is created in the Ghasedak panel
        type : MessageType, Optional
            type of the message can be either `TEXT` or `VOICE` (default `TEXT`)
        checkid: str, int, Optional
            Give the message ID of later use with `getSMSStatus` method
        **params: (str:str)
            Additional parameters passed to the endpoint,
             note that the key names should be like: `param1` all the way to `param10`
             for this method `param1` is reserved and yor key value pair for that will be ignored
        
        Returns
        -------
        boolean
            On failure returns False
        json
            On Success returns json array containing the message id for each receptor
        """

        data = {}
        data['receptor'] = str(receptor)
        data['template'] = str(template)
        data['type'] = type.value
        if checkid is not None: data['checkid'] = str(checkid)
        
        for param, value in params.items():
            data[param] = str(value)

        data['param1'] = str(otp)

        try:
            res = self.makeRequest(endpoint="/verification/send/simple", data=data)
        except ApiException as api_error:
            print(f"[Ghasedak] {api_error}")
            return False
        
        return res

    def getSMSStatus(self, id, type=MessageIDType.CHECK_ID):
        """Retrieve status of a sent message
            
        Parameters
        ----------
        id : str, str_list
            Id of the message, can be sudo list by seperating Id's with ","
        type : str, Optional
            SMS type can be either `MESSAGE_ID` or `CHECK_ID` (default `CHECK_ID`)

        Returns
        -------
        boolean
            On failure returns False
        json
            On Success returns an json array containing status for each sms
        """

        data = {}
        data['id'] = str(id)
        data['type'] = type.value

        try:
            res = self.makeRequest(endpoint="/sms/status", data=data, method="GET")
        except ApiException as api_error:
            print(f"[Ghasedak] {api_error}")
            return False

        # Translate status code to text
        for item in res:
            item['status'] = Statuses.get(item['status'])

        return res

    def getAccountInfo(self):
        """Retrieve account information
     
        Returns
        -------
        json
            Response json containint the remaining balance and the expire date of the account
        """

        try:
            res = self.makeRequest(endpoint="/account/info")
        except ApiException as api_error:
            print(f"[Ghasedak] {api_error}")
            return None
        
        return res
    