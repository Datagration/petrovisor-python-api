from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

import requests

from petrovisor.api.utils.login import ApiLogin
from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.utils.helper import ApiHelper

from petrovisor.api.methods.items import ItemsMixinHelper

from petrovisor.api.protocols.protocols import SupportsRequests


# PetroVisor Base API calls
class RequestsMixin(SupportsRequests):
    """
    PetroVisor Base API calls
    """

    @property
    def Api(self) -> str:
        """
        Api url
        """
        return self.__api

    @property
    def Token(self) -> str:
        """
        Access token
        """
        return self.__access_token

    @property
    def RefreshToken(self) -> str:
        """
        Refresh token
        """
        return self.__refresh_token

    @property
    def TokenEndpoint(self) -> str:
        """
        Token endpoint
        """
        return self.__token_endpoint

    @property
    def Key(self) -> str:
        """
        Authorization key
        """
        return self.__key

    @property
    def Workspace(self) -> str:
        """
        Workspace name
        """
        return self.__workspace

    @property
    def DiscoveryUrl(self) -> str:
        """
        Discovery url
        """
        return self.__discovery_url

    # api route
    @property
    def Route(self) -> str:
        """
        PetroVisor api route
        """
        return self.__route

    # 'NamedItem' routes
    @property
    def ItemRoutes(self):
        """
        Routes to items
        """
        return self.__item_routes

    # 'PetroVisorItem' routes
    @property
    def PetroVisorItemRoutes(self):
        """
        Routes to items with PetroVisor item info
        """
        return self.__petrovisor_item_routes

    # 'InfoItem' routes
    @property
    def InfoItemRoutes(self):
        """
        Routes to items with custom info
        """
        return self.__info_item_routes

    def __init__(self,
                 workspace: Optional[str] = '',
                 api: Optional[str] = '',
                 token: Optional[str] = '',
                 discovery_url: Optional[str] = '',
                 key: Optional[str] = '',
                 username: Optional[str] = '',
                 password: Optional[str] = '',
                 **kwargs):
        """
        Parameters
        ----------
        workspace : str, default None
            Workspace name
        api : str, default None
            Web api endpoint
        token : str, default None
            Access Token
        discovery_url : str, default None
            Discovery url
        key : str, default None
            Access key generated from username and password
        username : str, default None
            Username
        password : str, default None
            Password
        """
        # workspace
        self.__workspace = workspace

        # route
        self.__route = 'PetroVisor/API/'

        # api and token
        if api and token:
            # api endpoint
            self.__api = api
            # access token
            self.__access_token = token
            self.__refresh_token = ''
            self.__key = ''
            self.__discovery_url = ''
            self.__token_endpoint = ''
        else:
            # discovery url (identity service)
            if not discovery_url:
                default_discovery_url = ApiHelper.get_discovery_urls()
                urls = [f"'{url}'" for url in default_discovery_url]
                msg = f"Use one of the discovery urls: {urls}"
                raise ValueError(f"PetroVisor::__init__(): "
                                 f"'discovery_url' is undefined! {msg}")
            self.__discovery_url = discovery_url

            # api endpoint
            self.__api = api if api else RequestsMixin.get_web_api_endpoint(discovery_url)

            # access token
            if token:
                self.__access_token = token
                self.__refresh_token = ''
                self.__key = ''
                self.__token_endpoint = ''
            else:
                # get key
                if not key:
                    key = RequestsMixin.generate_credentials_key(username=username, password=password)
                # get access token
                if not key:
                    raise ValueError(f"PetroVisor::__init__(): "
                                     f"neither 'token', nor 'key', "
                                     f"nor 'username' and 'password' are defined!")
                access_response = ApiLogin.get_access_token(key=key, discovery_url=discovery_url)
                self.__access_token = access_response['access_token']
                self.__refresh_token = access_response['refresh_token'] if ('refresh_token' in access_response) else ''
                self.__key = key
                self.__token_endpoint = RequestsMixin.get_token_endpoint(discovery_url)

        # 'NamedItem' routes
        self.__item_routes = ItemsMixinHelper.get_item_routes()
        # 'PetroVisorItem' routes
        self.__petrovisor_item_routes = ItemsMixinHelper.get_petrovisor_item_routes()
        # 'InfoItem' routes
        self.__info_item_routes = ItemsMixinHelper.get_info_item_routes()

        super().__init__(**kwargs)

    # 'GET' request
    def get(self, rqst: str, data: Optional[Any] = None, query: Optional[Any] = None, files: Optional[Any] = None,
            format: Optional[str] = 'json', **kwargs) -> Any:
        """
        Get request

        Parameters
        ----------
        rqst : str
            Request
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        """
        response = ApiRequests.get(self.Api, rqst, workspace=self.Workspace, data=data, query=query,
                                   files=files, format=format, route=self.Route, token=self.Token,
                                   refresh_token=self.RefreshToken, key=self.Key,
                                   discovery_url=self.DiscoveryUrl, **kwargs)
        if ApiHelper.has_field(response, 'status_code') and response.status_code == requests.codes.unauthorized:
            self.__reset_token(**kwargs)
            response = ApiRequests.get(self.Api, rqst, workspace=self.Workspace, data=data, query=query,
                                       files=files, format=format, route=self.Route, token=self.Token,
                                       refresh_token=self.RefreshToken, key=self.Key,
                                       discovery_url=self.DiscoveryUrl, **kwargs)
        return response

    # 'POST' request
    def post(self,
             rqst: str,
             data: Optional[Any] = None,
             query: Optional[Any] = None,
             files: Optional[Any] = None,
             format: str = 'json',
             **kwargs) -> Any:
        """
        Post request

        Parameters
        ----------
        rqst : str
            Request
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        """
        response = ApiRequests.post(self.Api, rqst, workspace=self.Workspace, data=data, query=query,
                                    files=files, format=format, route=self.Route, token=self.Token,
                                    refresh_token=self.RefreshToken, key=self.Key,
                                    discovery_url=self.DiscoveryUrl, **kwargs)
        if ApiHelper.has_field(response, 'status_code') and response.status_code == requests.codes.unauthorized:
            self.__reset_token(**kwargs)
            response = ApiRequests.post(self.Api, rqst, workspace=self.Workspace, data=data, query=query,
                                        files=files, format=format, route=self.Route, token=self.Token,
                                        refresh_token=self.RefreshToken, key=self.Key,
                                        discovery_url=self.DiscoveryUrl, **kwargs)
        return response

    # 'PUT' request
    def put(self,
            rqst: str,
            data: Optional[Any] = None,
            query: Optional[Any] = None,
            files: Optional[Any] = None,
            format: str = 'json',
            **kwargs) -> Any:
        """
        Put request

        Parameters
        ----------
        rqst : str
            Request
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        """
        response = ApiRequests.put(self.Api, rqst, workspace=self.Workspace, data=data, query=query,
                                   files=files, format=format, route=self.Route, token=self.Token,
                                   refresh_token=self.RefreshToken, key=self.Key,
                                   discovery_url=self.DiscoveryUrl, **kwargs)
        if ApiHelper.has_field(response, 'status_code') and response.status_code == requests.codes.unauthorized:
            self.__reset_token(**kwargs)
            response = ApiRequests.put(self.Api, rqst, workspace=self.Workspace, data=data, query=query,
                                       files=files, format=format, route=self.Route, token=self.Token,
                                       refresh_token=self.RefreshToken, key=self.Key,
                                       discovery_url=self.DiscoveryUrl, **kwargs)
        return response

    # 'DELETE' request
    def delete(self,
               rqst: str,
               data: Optional[Any] = None,
               query: Optional[Any] = None,
               files: Optional[Any] = None,
               format: str = 'json',
               **kwargs) -> Any:
        """
        Delete request

        Parameters
        ----------
        rqst : str
            Request
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        """
        response = ApiRequests.delete(self.Api, rqst, workspace=self.Workspace, data=data, query=query,
                                      files=files, format=format, route=self.Route, token=self.Token,
                                      refresh_token=self.RefreshToken, key=self.Key,
                                      discovery_url=self.DiscoveryUrl, **kwargs)
        if ApiHelper.has_field(response, 'status_code') and response.status_code == requests.codes.unauthorized:
            self.__reset_token(**kwargs)
            response = ApiRequests.delete(self.Api, rqst, workspace=self.Workspace, data=data, query=query,
                                          files=files, format=format, route=self.Route, token=self.Token,
                                          refresh_token=self.RefreshToken, key=self.Key,
                                          discovery_url=self.DiscoveryUrl, **kwargs)
        return response

    # generate credentials key
    @staticmethod
    def generate_credentials_key(username: Optional[str] = '', password: Optional[str] = '') -> str:
        """
        Generate credentials key from username  and password.
        If either of username or password is not provided, the dialog is launched

        Parameters
        ----------
        username : str, default empty str
            Username
        password : str, default empty str
            Password
        """
        if username and password:
            return ApiLogin.generate_credentials_key(username=username, password=password)
        else:
            from getpass import getpass
            if username:
                return ApiLogin.generate_credentials_key(username=username,
                                                         password=getpass(prompt='Password: '))
            elif password:
                return ApiLogin.generate_credentials_key(username=input('Username: '), password=password)
            return ApiLogin.generate_credentials_key(username=input('Username: '),
                                                     password=getpass(prompt='Password: '))

    # get web api endpoint
    @staticmethod
    def get_web_api_endpoint(discovery_url: str) -> str:
        """
        Get web api endpoint

        Parameters
        ----------
        discovery_url : str
            Discovery url
        """
        return ApiLogin.get_web_api_endpoint(discovery_url=discovery_url)

    # get token endpoint
    @staticmethod
    def get_token_endpoint(discovery_url: str) -> str:
        """
        Get token endpoint

        Parameters
        ----------
        discovery_url : str
            Discovery url
        """
        return ApiLogin.get_token_endpoint(discovery_url=discovery_url)

    # update dictionary
    def update_dict(self, d: Dict, **kwargs) -> Dict:
        """
        Update dictionary fields with keyword argument values

        Parameters
        ----------
        d : dict
            Dictionary
        """
        return ApiHelper.update_dict(d, **kwargs)

    # remove dictionary fields
    def remove_from_dict(self, d: Dict, keys: Union[str, List[str]], **kwargs):
        """
        Remove dictionary fields

        Parameters
        ----------
        d : dict
            Dictionary
        keys : str | list
            Dictionary key ot be removed
        """
        return ApiHelper.remove_from_dict(d, keys, **kwargs)

    # reset token
    def __reset_token(self, **kwargs) -> Any:
        """
        Reset token
        """
        access_response = ApiLogin.get_access_token(key=self.Key, discovery_url=self.DiscoveryUrl, **kwargs)
        self.__access_token = access_response['access_token'] if ('access_token' in access_response) else ''
