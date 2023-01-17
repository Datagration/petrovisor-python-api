from typing import Any, Optional, Union, List, Dict, Callable
#import json

import os
import copy
import io
import re
from enum import Enum, auto
from uuid import UUID
import pickle
import requests
import pandas as pd
import numpy as np
from datetime import datetime

from petrovisor.api.login import PetroVisorLogin
from petrovisor.api.requests import PetroVisorApiRequest

# Signal types
class SignalType(Enum):
    """
    PetroVisor signal types
    """
    # Static signal type specifies signals which value is a numeric constant over a time or depth
    Static = 0
    # Time-dependent type specifies signals which are functions of time
    TimeDependent = 1
    # Depth-dependent type specifies signals which are functions of depth
    DepthDependent = 2
    # String signal type specifies signals which value is a string constant over a time or depth
    String = 3
    # PVT signal type specifies signals which are functions of pressure and temperature
    PVT = 4
    # String time-dependent signal type specifies signals which value is a string constant over a time or depth
    StringTimeDependent = 5

# Time increment for aggregation
class TimeIncrement(Enum):
    """
    PetroVisor time increments
    """
    # Every second
    EverySecond = auto()
    # Every minute
    EveryMinute = auto()
    # Every five minute
    EveryFiveMinutes = auto()
    # Every fifteen minute
    EveryFifteenMinutes = auto()
    # Every hour
    Hourly = auto()
    # Every day
    Daily = auto()
    # Every month
    Monthly = auto()
    # Every quarter
    Quarterly = auto()
    # Every year
    Yearly = auto()

# Depth increment for aggregation
class DepthIncrement(Enum):
    """
    PetroVisor depth increments
    """
    # 0.1 m (Every tenth of meter)
    TenthMeter = 0
    # 0.125 m (Every eighth of meter)
    EighthMeter = 1
    # 0.1524 m (Every half of foot)
    HalfFoot = 2
    # 0.3048 m (Every foot)
    Foot = 3
    # 0.5 m (Every half of meter)
    HalfMeter = 4
    # 1 m (Every meter)
    Meter = 5

# PetroVisor Machine Learning model types
class MLModelType(Enum):
    # Regression
    Regression = 0
    # Binary classification
    BinaryClassification = auto()
    # Multiple classification
    MultipleClassification = auto()
    # Clustering
    Clustering = auto()
    # Naive Bayes
    NaiveBayes = auto()
    # Naive Bayes (categorical data)
    NaiveBayesCategorical = auto()

# PetroVisor Machine Learning normalization types
class MLNormalizationType(Enum):
    # ML engine will automatically pick a normalization method
    Auto = auto()
    # MinMax
    MinMax = auto()
    # MeanVariance
    MeanVariance = auto()
    # LogMeanVariance
    LogMeanVariance = auto()
    # Binning
    Binning = auto()
    # SupervisedBinning
    SupervisedBinning = auto()
    # RobustScaling
    RobustScaling = auto()
    # LpNorm
    LpNorm = auto()
    # GlobalContrast
    GlobalContrast = auto()

# PetroVisor API calls
class PetroVisor:
    """
    PetroVisor API class
    """

    @property
    def Api(self):
        """
        Api url
        """
        return self.__api
    
    @property
    def Token(self):
        """
        Access token
        """
        return self.__access_token

    @property
    def RefreshToken(self):
        """
        Refresh token
        """
        return self.__refresh_token

    @property
    def TokenEndpoint(self):
        """
        Token endpoint
        """
        return self.__token_enpoint

    @property
    def Key(self):
        """
        Authorization key
        """
        return self.__key

    @property
    def Workspace(self):
        """
        Workspace name
        """
        return self.__workspace

    @property
    def DiscoveryUrl(self):
        """
        Dicscovery url
        """
        return self.__discovery_url

    # api route
    @property
    def Route(self):
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
        Routes to items with PetroVisor object info
        """
        return self.__petrovisor_item_routes

    # 'InfoItem' routes
    @property
    def InfoItemRoutes(self):
        """
        Routes to items with custom Iinfo
        """
        return self.__info_item_routes

    def __init__(self, workspace: Optional[str] = '', api: Optional[str] = '', token: Optional[str] = '', discovery_url: Optional[str] = '', key: Optional[str] = '', username: Optional[str] = '', password: Optional[str] = '', **kwargs ):
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
        if( api and token ):
            # api endpoint
            self.__api = api
            # access token
            self.__access_token = token
            self.__refresh_token = ''
            self.__key = ''
            self.__discovery_url = ''
            self.__token_enpoint = ''
        else:
            if( not discovery_url ):
                default_discovery_url = PetroVisorHelper.get_discovery_urls()
                urls = [f"'{url}'" for url in default_discovery_url]
                msg = f"Use one of the discovery urls: {urls}"
                raise NameError("PetroVisor::__init__(): 'discovery_url' is undefined!" + " " + msg)
            # api endpoint
            self.__api = api if(api) else PetroVisor.get_web_api_endpoint(discovery_url)
            
            # access token
            if ( token ):
                self.__access_token = token
                self.__refresh_token = ''
                self.__key = ''
                self.__token_enpoint = ''
            else:
                # get key
                if( not key ):
                    key = PetroVisor.generate_credentials_key(username = username, password = password)
                # get access token
                if( not key ):
                    raise NameError("PetroVisor::__init__(): neither 'token', nor 'key', nor 'username' and 'password' are defined!")
                access_response = PetroVisorLogin.get_access_token(key = key, discovery_url = discovery_url)
                self.__access_token = access_response['access_token']
                self.__refresh_token = access_response['refresh_token'] if('refresh_token' in access_response) else ''
                self.__key = key
                self.__discovery_url = discovery_url
                self.__token_enpoint = PetroVisor.get_token_endpoint(discovery_url)
        
        # 'NamedItem' routes
        self.__item_routes = PetroVisorHelper.get_item_routes()
        # 'PetroVisorItem' routes
        self.__petrovisor_item_routes = PetroVisorHelper.get_petrovisor_item_routes()
        # 'InfoItem' routes
        self.__info_item_routes = PetroVisorHelper.get_info_item_routes()

    # get access token
    # @staticmethod
    # def get_access_token( key: str = '', username: str = '', password: str = '', refresh_token: str = '', discovery_url: str = '', token_endpoint: str = '', **kwargs ) -> Dict:
    #     return PetroVisorLogin.get_access_token( key = key, username = username, password = password, refresh_token = refresh_token, discovery_url = discovery_url, token_endpoint = token_endpoint, **kwargs )
    
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
        return PetroVisorLogin.get_web_api_endpoint(discovery_url = discovery_url)
    
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
        return PetroVisorLogin.get_token_endpoint(discovery_url = discovery_url)

    # generate credentials key
    @staticmethod
    def generate_credentials_key( username: Optional[str] = '', password: Optional[str] = '') -> str:
        """
        Generate credientials key from username  and password.
        If either of username or password is not provided, the dialog is lanched

        Parameters
        ----------
        username : str, default empty str
            Username
        password : str, default empty str
            Password
        """
        if(username and password):
            return PetroVisorLogin.generate_credentials_key(username = username, password = password)
        else:
            from getpass import getpass
            if(username):
                return PetroVisorLogin.generate_credentials_key(username = username, password = getpass(prompt='Password: '))
            elif(password):
                return PetroVisorLogin.generate_credentials_key(username = input('Username: '), password = password)
            return PetroVisorLogin.generate_credentials_key(username = input('Username: '), password = getpass(prompt='Password: '))

    # 'GET' request
    def get( self, rqst: str, data: Optional[Any] = None, query: Optional[Any] = None, files: Optional[Any] = None, format: Optional[str] = 'json', **kwargs ) -> Any:
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
        response = PetroVisorApiRequest.get( self.Api, rqst, workspace = self.Workspace, data = data, query = query, files = files, format = format, route = self.Route, token = self.Token, refresh_token = self.RefreshToken, key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        if(PetroVisorHelper.has_field(response,'status_code') and response.status_code == requests.codes.unauthorized):
            self.__reset_token(**kwargs)
            response = PetroVisorApiRequest.get( self.Api, rqst, workspace = self.Workspace, data = data, query = query, files = files, format = format, route = self.Route, token = self.Token, refresh_token = self.RefreshToken, key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        return response

    # 'POST' request
    def post( self, rqst: str, data: Optional[Any] = None, query: Optional[Any] = None, files: Optional[Any] = None, format = 'json', **kwargs ) -> Any:
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
        response = PetroVisorApiRequest.post( self.Api, rqst, workspace = self.Workspace, data = data, query = query, files = files, format = format, route = self.Route, token = self.Token, refresh_token = self.RefreshToken, key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        if(PetroVisorHelper.has_field(response,'status_code') and response.status_code == requests.codes.unauthorized):
            self.__reset_token(**kwargs)
            response = PetroVisorApiRequest.post( self.Api, rqst, workspace = self.Workspace, data = data, query = query, files = files, format = format, route = self.Route, token = self.Token, refresh_token = self.RefreshToken, key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        return response

    # 'PUT' request
    def put( self, rqst: str, data: Optional[Any] = None, query: Optional[Any] = None, files: Optional[Any] = None, format = 'json', **kwargs ) -> Any:
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
        response = PetroVisorApiRequest.put( self.Api, rqst, workspace = self.Workspace, data = data, query = query, files = files, format = format, route = self.Route, token = self.Token, refresh_token = self.RefreshToken, key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        if(PetroVisorHelper.has_field(response,'status_code') and response.status_code == requests.codes.unauthorized):
            self.__reset_token(**kwargs)
            response = PetroVisorApiRequest.put( self.Api, rqst, workspace = self.Workspace, data = data, query = query, files = files, format = format, route = self.Route, token = self.Token, refresh_token = self.RefreshToken, key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        return response

    # 'DELETE' request
    def delete( self, rqst: str, data: Optional[Any] = None, query: Optional[Any] = None, files: Optional[Any] = None, format = 'json', **kwargs ) -> Any:
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
        response = PetroVisorApiRequest.delete( self.Api, rqst, workspace = self.Workspace, data = data, query = query, files = files, format = format, route = self.Route, token = self.Token, refresh_token = self.RefreshToken, key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        if(PetroVisorHelper.has_field(response,'status_code') and response.status_code == requests.codes.unauthorized):
            self.__reset_token(**kwargs)
            response = PetroVisorApiRequest.delete( self.Api, rqst, workspace = self.Workspace, data = data, query = query, files = files, format = format, route = self.Route, token = self.Token, refresh_token = self.RefreshToken, key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        return response
    
    # add log entry
    def add_log_entry(self, message: str, **kwargs):
        """
        Add log entry message.
        Use keywords arguments to pass other information.
        Known fields are:
            'message','timestamp'(utc),'category','username',
            'severity','workspace','schedule','workflow',
            'starttime','endtime','script','entity','signal','unit',
            'tag','numberofitems','valuebefore','valueafter',
            'elapsedtime','messagedetails','directory'
        Parameters
        ----------
        message : str
        """
        log_entry = {
            'Timestamp': None,
            'Message': message,
            'Category': None,
            'UserName': None,
            'Severity': None,
            'Workspace': None,
            'Schedule': None,
            'Workflow': None,
            'StartTime': None,
            'EndTime': None,
            'Script': None,
            'Entity': None,
            'Signal': None,
            'Unit': None,
            'Tag': None,
            'NumberOfItems': None,
            'ValueBefore': None,
            'ValueAfter': None,
            'ElapsedTime': None,
            'MessageDetails': None,
            'Directory': None
        }
        log_entry = PetroVisorHelper.update_dict(log_entry,**kwargs)
        return self.post('LogEntries', data = PetroVisorHelper.get_non_empty_fields(log_entry), **kwargs)

    # get item types
    def get_item_types(self, **kwargs):
        """
        Get all known item types

        Returns
        -------
        All know item types
        """
        return PetroVisorHelper.get_item_types()
    
    # get item
    def get_item( self, item_type: str, name: str, **kwargs ) -> Any:
        """
        Get item

        Parameters
        ----------
        item_type : str
            Item type
        name : str
            Item name
        """
        route = self.get_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::get_item(): unknown item type: '{item_type}'. Known item types: {list(self.ItemRoutes.keys())}" )
        if(route == 'Units' and name == ' '):
            name = '_'
        return self.get(f'{route}/{name}', **kwargs)

    # delete item
    def delete_item( self, item_type: str, item: Union[str,Dict], **kwargs ) -> Any:
        """
        Delete item

        Parameters
        ----------
        item_type : str
            Item type
        item : str, dict
            Item object or Item name
        """
        route = self.get_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::delete_item(): unknown item type: '{item_type}'. Known item types: {list(self.ItemRoutes.keys())}" )
        name = self.get_item_name(item,**kwargs)
        return self.delete(f'{route}/{name}', **kwargs)

    # add or edit item
    def add_item( self, item_type: str, item: Dict, **kwargs ) -> Any:
        """
        Add or edit item

        Parameters
        ----------
        item_type : str
            Item type
        item : dict
            Item object
        """
        route = self.get_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::add_item(): unknown item type: '{item_type}'. Known item types: {list(self.ItemRoutes.keys())}" )
        name = self.get_item_name(item,**kwargs)
        return self.put(f'{route}/{name}', data = item, **kwargs)

    # update item metadata
    def update_item_metadata( self, item_type: str, item: Dict, **kwargs ) -> Any:
        """
        Update item metadata

        Parameters
        ----------
        item_type : str
            Item type
        item : dict
            Item object
        """
        route = self.get_petrovisor_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::update_item_metadata(): unknown 'PetroVisor' item type: '{item_type}'. Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}" )
        name = self.get_item_name(item,**kwargs)
        return self.put(f'{route}/{name}/Metadata', data = item, **kwargs)

    # get items
    def get_items( self, item_type: str, **kwargs ) -> List:
        """
        Get items of given type

        Parameters
        ----------
        item_type : str
            Item type
        """
        route = self.get_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::get_items(): unknown item type: '{item_type}'. Known item types: {list(self.ItemRoutes.keys())}" )
        return self.get(f'{route}/All', **kwargs)

    # get item paged
    def get_items_paged( self, item_type: str, page: int = 1, page_size: int = 10, **kwargs ) -> List:
        """
        Get items of given type in paged format

        Parameters
        ----------
        item_type : str
            Item type
        page : int, default 1
            Page number
        page_size : int, default 10
            Page size
        """
        route = self.get_petrovisor_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::get_items_paged(): unknown 'PetroVisor' item type: '{item_type}'. Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}" )
        return self.get(f'{route}/Paged', query = {'Page': page, 'PageSize': page_size}, **kwargs)

    # get item names
    def get_item_names( self, item_type: str, **kwargs ) -> List[str]:
        """
        Get item names of given type

        Parameters
        ----------
        item_type : str
            Item type
        """
        route = self.get_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::get_item_names(): unknown item type: '{item_type}'. Known item types: {list(self.ItemRoutes.keys())}" )
        return self.get(f'{route}', **kwargs)

    # get item labels
    def get_item_labels( self, item_type: str, **kwargs ) -> List[str]:
        """
        Get item labels of given type

        Parameters
        ----------
        item_type : str
            Item type
        """
        route = self.get_petrovisor_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::get_item_labels(): unknown 'PetroVisor' item type: '{item_type}'. Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}" )
        return self.get(f'{route}/Labels', **kwargs)

    # get item infos
    def get_item_infos( self, item_type: str, **kwargs ) -> List:
        """
        Get item infos of given type

        Parameters
        ----------
        item_type : str
            Item type
        """
        route = self.get_info_item_route( item_type, **kwargs )
        if(not route):
            raise NameError( f"PetroVisor::get_item_infos(): unknown 'PetroVisor' item type: '{item_type}'. Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}" )
        if(self.is_info_item(item_type, **kwargs )):
            return self.get(f'{route}/Info', **kwargs)
        return self.get(f'{route}/PetroVisorItems', **kwargs)

    # get item name
    def get_item_name( self, item: Union[str,Dict], **kwargs) -> str:
        """
        Get item name

        Parameters
        ----------
        item : dict
            Item object
        """
        return PetroVisorHelper.get_object_name(item)

    # get item field
    def get_item_field( self, item_type: Optional[str], item: Union[str,Dict], field_name: str, **kwargs) -> SignalType:
        """
        Get item field value

        Parameters
        ----------
        item_type : str
            Item type
        item : str, dict
            Item object or Item name
        field_name : str
            Field name
        """
        if(isinstance(item,str) and item_type):
            item_name = PetroVisorHelper.get_object_name(item)
            item = self.get_item(item_type,item_name,**kwargs)
        if(not item):
            raise RuntimeError(f"PetroVisor::get_item_field(): Item '{item}' cannot be found!")
        elif(not PetroVisorHelper.has_field(item,field_name)):
            raise RuntimeError(f"PetroVisor::get_item_field(): Item '{item}' doesn't not have '{field_name}' field!")
        return item[field_name]

    # get signal type
    def get_signal_type( self, signal: Union[str,Dict], **kwargs) -> str:
        """
        Get signal type

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        return self.get_item_field( 'Signal', signal, 'SignalType', **kwargs)

    # get signal 'MeasurementName'
    def get_signal_measurement_name( self, signal: Union[str,Dict], **kwargs) -> Any:
        """
        Get signal measurement name

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        field_name = 'MeasurementName'
        if(isinstance(signal,str)):
            signal_name = PetroVisorHelper.get_object_name(signal)
            signal = self.get_item('Signal',signal_name,**kwargs)
        if(not signal):
            raise RuntimeError(f"PetroVisor::get_signal_measurement_name(): Signal '{signal}' cannot be found!")
        elif(not PetroVisorHelper.has_field(signal,field_name)):
            raise RuntimeError(f"PetroVisor::get_signal_measurement_name(): Signal '{signal}' doesn not have '{field_name}' field!")
        return signal[field_name]

    # get signal storage 'Unit'
    def get_signal_unit( self, signal: Union[str,Dict], **kwargs) -> Any:
        """
        Get signal unit

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        return self.get_item_field( 'Signal', signal, 'StorageUnitName', **kwargs)

    # get signal 'Units'
    def get_signal_units( self, signal: Union[str,Dict], **kwargs) -> Any:
        """
        Get all units of signal measurement

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        measurement_name = self.get_signal_measurement_name(signal, **kwargs)
        return self.get_measurement_units(measurement_name,**kwargs)

    # get signal 'Unit' names
    def get_signal_unit_names( self, signal: Union[str,Dict], **kwargs) -> Any:
        """
        Get all unit names of signal measurement

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        measurement_name = self.get_signal_measurement_name(signal, **kwargs)
        return self.get_measurement_unit_names(measurement_name,**kwargs)

    # get measurement 'Units'
    def get_measurement_units( self, measurement: str, **kwargs) -> Any:
        """
        Get measurement units

        Parameters
        ----------
        measurement : str
            Measurement name
        """
        route = self.get_item_route('Unit')
        return self.get(f'{route}/{measurement}/Units', **kwargs)

    # get measurement 'Unit' names
    def get_measurement_unit_names( self, measurement: str, **kwargs) -> Any:
        """
        Get measurement unit names

        Parameters
        ----------
        measurement : str
            Measurement name
        """
        units = self.get_measurement_units(measurement, **kwargs)
        return [unit['Name'] for unit in units]

    # rename 'EntityType'
    def rename_entity_type( self, old_name: str, new_name: str, **kwargs) -> Any:
        """
        Rename entity type

        Parameters
        ----------
        old_name : str
            Old name
        new_name : str
            New name
        """
        route = self.get_item_route('EntityType')
        return self.post(f'{route}/Rename', query = {'OldName': old_name, 'NewName': new_name}, **kwargs)

    # rename 'Entity'
    def rename_entity( self, old_name: str, new_name: str, **kwargs) -> Any:
        """
        Rename entity

        Parameters
        ----------
        old_name : str
            Old name
        new_name : str
            New name
        """
        route = self.get_item_route('Entity')
        return self.post(f'{route}/Rename', query = {'OldName': old_name, 'NewName': new_name}, **kwargs)

    # get 'Entity'
    def get_entity( self, name: str, alias: Optional[str] = '', **kwargs) -> Dict:
        """
        Get entity

        Parameters
        ----------
        name : str
            Entity name
        alias : str
            Entity alias
        """
        route = self.get_item_route('Entity')
        if(alias):
            return self.get(f'{route}/{alias}/Entity',**kwargs)
        return self.get(f'{route}/{name}',**kwargs)

    # get 'Entities'
    def get_entities( self, entity_type: Optional[str] = '', signal: Optional[str] = '', **kwargs) -> List[Dict]:
        """
        Get entities. Filter optionally by entity type and signal

        Parameters
        ----------
        entity_type : str, default ''
            Entity type
        signal : str, default ''
            Signal object or Signal name
        """
        route = self.get_item_route('Entity')
        # get entities by 'Entity' type
        if(entity_type):
            entities = self.get(f'{route}/{entity_type}/Entities', **kwargs)
        # get all entities
        else:
            entities = self.get(f'{route}/All', **kwargs)
        # get entities by 'Signal' name
        if(signal):
            entity_names = self.get_entity_names( signal_type = None, signal = signal, **kwargs)
            if(entity_names):
                return [e for e in entities if(e['Name'] in entity_names)]
        return entities if(entities is not None) else []

    # get 'Entity' names
    def get_entity_names( self, entity_type: Optional[str] = '', signal: Optional[str] = '', **kwargs) -> List[str]:
        """
        Get entity names. Filter optionally by entity type and signal

        Parameters
        ----------
        entity_type : str, default ''
            Entity type
        signal : str, default ''
            Signal object or Signal name
        """
        route = self.get_item_route('Entity')
        # get entities by 'Signal' name
        if(signal):
            signals_route = self.get_item_route('Signal')
            signal_name = PetroVisorHelper.get_object_name(signal)
            entity_names = self.get(f'{signals_route}/{signal_name}/Entities', **kwargs)
            if(entity_type and entity_names is not None):
                entity_type_names = self.get_entity_names(entity_type = entity_type, signal = None, **kwargs)
                if(entity_type_names):
                    return [e for e in entity_names if(e in entity_type_names)]
        # get entities by 'Entity' type
        elif(entity_type):
            entities = self.get_entities( entity_type = entity_type, signal = None, **kwargs)
            return [ e['Name'] for e in entities]
        # get all entities
        else:
            entity_names = self.get(f'{route}', **kwargs)
        return entity_names if(entity_names is not None) else []

    # add 'Entities'
    def add_entities( self, entities: List, **kwargs) -> Any:
        """
        Add multiple entities

        Parameters
        ----------
        entities : list
            List of entities
        """
        route = self.get_item_route('Entity')
        return self.post(f'{route}/AddOrEdit', data = entities, **kwargs)

    # delete 'Entities'
    def delete_entities( self, entities: List, **kwargs) -> Any:
        """
        Delete multiple entities

        Parameters
        ----------
        entities : list
            List of entities
        """
        route = self.get_item_route('Entity')
        return self.post(f'{route}/Delete', data = entities, **kwargs)

    # get 'Signal'
    def get_signal( self, name: str, short_name: Optional[str] = '', **kwargs) -> Dict:
        """
        Get signal by name or short name

        Parameters
        ----------
        name : str
            Signal name
        short_name : str
            Signal short name
        """
        route = self.get_item_route('Signal')
        if(short_name):
            signal = self.get(f'{route}/{short_name}/Signal',**kwargs)
        else:
            signal = None
        if(signal is None):
            return self.get(f'{route}/{name}',**kwargs)
        return None

    # get 'Signals'
    def get_signals( self, signal_type: Optional[str] = '', entity: Optional[Union[Any,str]] = None, **kwargs) -> List[Dict]:
        """
        Get signals. Filter optionally by signal type and entity

        Parameters
        ----------
        short_type : str
            Signal type
        entity : str
            Entity object or Entity name
        """
        route = self.get_item_route('Signal')
        # get signals by signal type
        if(signal_type):
            signal_type = self.get_signal_type_enum(signal_type,**kwargs).name
            signals = self.get(f'{route}/{signal_type}/Signals', **kwargs)
        # get all signals
        else:
            signals = self.get(f'{route}/All', **kwargs)
        # get signals by 'Entity' name
        if(entity):
            signal_names = self.get_signal_names( signal_type=None, entity = entity, **kwargs)
            if(signal_names):
                return [s for s in signals if(s['Name'] in signal_names)]
        return signals if(signals is not None) else []

    # get 'Signal' names
    def get_signal_names( self, signal_type: Optional[str] = '', entity: Optional[Union[Any,str]] = None, **kwargs) -> List[str]:
        """
        Get signal names. Filter optionally by signal type and entity

        Parameters
        ----------
        short_type : str
            Signal type
        entity : str
            Entity object or Entity name
        """
        route = self.get_item_route('Signal')
        # get signals by 'Entity' name
        if(entity):
            entities_route = self.get_item_route('Entity')
            entity_name = PetroVisorHelper.get_object_name(entity)
            signal_names = self.get(f'{entities_route}/{entity_name}/Signals', **kwargs )
            if(signal_type and signal_names is not None):
                signal_type_names = self.get_signal_names(signal_type = signal_type, entity = None, **kwargs)
                if(signal_type_names):
                    return [s for s in signal_names if(s in signal_type_names)]
        # get signals by 'Signal' type
        elif(signal_type):
            signals = self.get_signals( signal_type = signal_type, entity = None, **kwargs)
            return [ e['Name'] for e in signals]
        # get all signals
        else:
            signal_names = self.get(f'{route}', **kwargs)
        return signal_names if(signal_names is not None) else []

    # add 'Signals'
    def add_signals( self, signals: List, **kwargs) -> Any:
        """
        Add multiple signals

        Parameters
        ----------
        signals : list
            List of entities
        """
        route = self.get_item_route('Signal')
        return self.post(f'{route}/Add', data = signals, **kwargs)

    # deelete 'Signals'
    def delete_signals( self, signals: List, **kwargs) -> Any:
        """
        Delete multiple signals

        Parameters
        ----------
        signals : list
            List of entities
        """
        route = self.get_item_route('Signal')
        for signal_name in signals:
            self.delete(f'{route}/{signal_name}', **kwargs)

    # get file names
    def get_file_names( self, **kwargs) -> List[str]:
        """
        Get file names
        """
        return self.get('Files',**kwargs)

    # get file by name
    def get_file( self, filename: str, format: str = 'bytes', **kwargs) -> Any:
        """
        Get file

        Parameters
        ----------
        filename : str
            File name
        format : str, default 'bytes'
            File format
        """
        return self.get(f'Files/{filename}', format = format, **kwargs)

    # get file by name
    def delete_file( self, filename: str, **kwargs) -> Any:
        """
        Delete file

        Parameters
        ----------
        filename : str
            File name
        """
        return self.delete(f'Files/{filename}',**kwargs)

    # upload file
    def upload_file( self, file: Any, **kwargs) -> Any:
        """
        Upload file

        Parameters
        ----------
        file : Any
            file object
        """
        return self.post('Files/Upload', files = {'file': open(file,'rb') if(isinstance(file,str)) else file}, **kwargs)

    # get object by name
    def get_object( self, objectname: str, func : Optional[Callable], **kwargs) -> Any:
        """
        Load object from blob storage using pickle.loads()

        Parameters
        ----------
        objectname : str
            Object name
        func : Optional[Callable], default None
            Function to be called to prepare object after load. If None, then pickle.loads() is used
        """
        file_obj = self.get_file(objectname, format = 'bytes', **kwargs)
        if(func and hasattr(func, '__call__')):
            return func(file_obj,**kwargs)
        return pickle.loads(file_obj)

    # upload object
    def upload_object( self, obj: Any, name: str, func : Optional[Callable], **kwargs) -> Any:
        """
        Upload object to blob storage using pickle.dumps()

        Parameters
        ----------
        obj : Any
            Object
        name : str
            Object name
        func : Optional[Callable], default None
            Function to be called to prepare object for upload. If None, then pickle.dumps() is used
        """
        # upload file by full path
        if(func and hasattr(func, '__call__')):
            file = func(obj,**kwargs)
        else:
            file = pickle.dumps(obj)
        file_obj = io.BytesIO(file)
        file_obj.name = name
        return self.upload_file(file = file_obj, **kwargs)

    # get data range
    def get_data_range( self, signal_type: str, signal: Optional[str] = None, entity: Optional[str] = None, **kwargs ) -> Any:
        """
        Upload object

        Parameters
        ----------
        data_type : str
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        signal : str
            Object name
        """
        route = self.get_signal_type_route(type=signal_type,**kwargs)
        if(signal and entity):
            signal_name = PetroVisorHelper.get_object_name(signal)
            entity_name = PetroVisorHelper.get_object_name(entity)
            return self.get(f'{route}/Range/{signal_name}/{entity_name}', **kwargs)
        elif(signal):
            signal_name = PetroVisorHelper.get_object_name(signal)
            return self.get(f'{route}/Range/{signal_name}', **kwargs)
        return self.get(f'{route}/Range', **kwargs)

    # cleanse data
    def cleanse_data( self, data_type: Union[str,SignalType], value: float, timestamp: Optional[Union[datetime,str]], signal: Union[Dict,str], unit: Union[Dict,str], entity: Union[Dict,str], cleansing_script: str, **kwargs ) -> Any:
        """
        Cleanse data

        Parameters
        ----------
        data_type : str, SignalType
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        value : float
            Value
        timestamp : datetime,str
            Date
        signal : str, dict
            Signal object or Signal name
        unit : str, dict
            Unit object or UNit name
        entity : str, dict
            Entity object or Entity name
        cleansing_script : str
            Cleansing script
        """
        data_type = self.get_signal_type_enum( data_type, **kwargs )
        route = self.get_signal_type_route(type=data_type,**kwargs)
        if( data_type != SignalType.TimeDependent and data_type != SignalType.Static ):
            raise Warning("PetroVisor::cleanse_data(): Cleansing is only supported for 'Static' and 'TimeNumeric' data.")
        options = {
            'UseDefaultCleansingScripts': True,
            'CleansingScript': cleansing_script,
            'TreatCleansingScriptAsCleansingScriptName': True,
            'IsPreview': True
        }
        options = PetroVisorHelper.update_dict(options,**kwargs)
        entity_name = PetroVisorHelper.get_object_name(entity,**kwargs)
        signal_name = PetroVisorHelper.get_object_name(signal,**kwargs)
        unit_name = PetroVisorHelper.get_object_name(unit,**kwargs)
        data_with_options = {
            'Entity': entity_name,
            'Signal': signal_name,
            'Unit': unit_name,
            'Value': value,
            'Options': options
        }
        if(data_type == SignalType.TimeDependent):
            data_with_options['Timestamp'] = self.get_json_valid_value(timestamp,'time',**kwargs)
        return self.post(f'{route}/Cleanse', data = data_with_options, **kwargs)

    # load data
    def load_data( self, data_type: Union[str,SignalType], data: List, start: Optional[Union[datetime,float]] = None, end: Optional[Union[datetime,float]] = None, step: Optional[Union[str,TimeIncrement,DepthIncrement]] = None, hierarchy: Optional[str] = None, num_values: Optional[int] = None, gap_value: Optional[float] = None, interpolated: Optional[bool] = False,  with_logs: bool = False, pressure_unit: str = 'Pa', temperature_unit: str = 'K', **kwargs ) -> Any:
        """
        Load data

        Parameters
        ----------
        data_type : str, SignalType
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        data : list
            Data
        start : datetime, float, None, default None
            Start of time/depth range
        end : datetime, float, default None
            End of time/depth range
        step : str, TimeIncrement, DepthIncrement, None, default None
            Step of time/depth range
        hierarchy : str, None, default None
            Hierarchy name
        num_values : int, None, default None
            Number of values ot load
        gap_value : float, None, default None
            Gap filling value to use
        interpolated : bool, default False
            Whether to get interpolated value (depth dependent data)
        with_logs : bool, default False
            Load data and return logs
        pressure_unit : str, default 'Pa'
            Pressure unit (PVT data)
        temperature_unit : str, default 'K'
            Temperature unit (PVT data)
        """
        data_type = self.get_signal_type_enum( data_type, **kwargs )
        route = self.get_signal_type_route(type=data_type,**kwargs)
        # load 'Time' or 'Depth' data
        if(data_type == SignalType.TimeDependent or data_type == SignalType.StringTimeDependent or data_type == SignalType.DepthDependent):
            # first/last values only
            if(num_values is not None):
                # first values only
                if(num_values > 0):
                    return self.post(f'{route}/First', data = data, query = {'NumberOfValues': num_values}, **kwargs)
                # last  values only
                elif(num_values < 0 ):
                    return self.post(f'{route}/Last', data = data, query = {'NumberOfValues': abs(num_values)}, **kwargs)
            # get data defined on range
            if(start is not None and end is not None):
                if(step is not None or (start == end and data_type == SignalType.StringTimeDependent) ):
                    if(step is not None):
                        range_step = self.get_increment_enum(step,data_type)
                    else:
                        range_step = TimeIncrement.EverySecond
                    if(not PetroVisorHelper.has_field(range_step,'name')):
                        raise ValueError(f"PetroVisor::load_data(): Invalid increment value: '{step}'")
                    range_step = str(range_step.name)
                    is_time_dependent = (data_type == SignalType.TimeDependent or data_type == SignalType.StringTimeDependent)
                    range_type = 'time' if(is_time_dependent) else 'numeric'
                    data_range = {
                        'Start': self.get_json_valid_value(start,range_type,**kwargs),
                        'End': self.get_json_valid_value(end,range_type,**kwargs),
                        'Increment': range_step}
                    if(hierarchy is not None and hierarchy and (data_type == SignalType.TimeDependent or data_type == SignalType.StringTimeDependent)):
                        data_range['Hierarchy'] = hierarchy
                    # load with filling gaps
                    if(gap_value is not None):
                        gap_value = self.get_json_valid_value(gap_value,data_type,**kwargs)
                        return self.post(f'{route}/Load/{gap_value}', data = data, query = data_range, **kwargs)
                    # load data in specified range
                    if(with_logs and PetroVisorHelper.has_field(data,'Data')):
                        return self.post(f'{route}/AquireWithLogs', data = data, query = data_range, **kwargs)
                    elif(PetroVisorHelper.has_field(data,'Requests')):
                        return self.post(f'{route}/Retrieve', data = data, query = data_range, **kwargs)
                    return self.post(f'{route}/Load', data = data, query = data_range, **kwargs)
                elif(start == end):
                    load_point = self.get_json_valid_value(start,data_type,**kwargs)
                    # get data at single point
                    if(data_type == SignalType.TimeDependent):
                        return self.post(f'{route}/Saved', data = data, query = {'Date': load_point}, **kwargs)                    
                    elif(data_type == SignalType.DepthDependent):
                        # load interpolated data
                        if(interpolated and data_type == SignalType.DepthDependent):
                            return self.post(f'{route}/Interpolated', data = data, query = {'Depth': load_point}, **kwargs)
                        return self.post(f'{route}/Saved', data = data, query = {'Depth': load_point}, **kwargs)
            else:
                raise ValueError(f"PetroVisor::load_data(): 'start', 'end' and 'step' should be provided! 'step' can be avoided if 'start' == 'end'.")
        # load 'Static' and 'PVT' data
        if(with_logs  and PetroVisorHelper.has_field(data,'Data') and data_type == SignalType.Static):
            return self.post(f'{route}/AquireWithLogs', data = data, **kwargs)
        elif(PetroVisorHelper.has_field(data,'Requests')):
            return self.post(f'{route}/Retrieve', data = data, **kwargs)
        if(data_type == SignalType.PVT):
            return self.post(f'{route}/Load', data = data, query = {'PressureUnit': pressure_unit, 'TemperatureUnit': temperature_unit}, **kwargs)
        return self.post(f'{route}/Load', data = data, **kwargs)

    # save data
    def save_data( self, data_type: Union[str,SignalType], data: List, with_logs = False, pressure_unit: str = 'Pa', temperature_unit: str = 'K', **kwargs ) -> Any:
        """
        Save data

        Parameters
        ----------
        data_type : str, SignalType
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        data : list
            Data
        with_logs : bool, default False
            Load data and return logs
        pressure_unit : str, default 'Pa'
            Pressure unit (PVT data)
        temperature_unit : str, default 'K'
            Temperature unit (PVT data)
        """
        route = self.get_signal_type_route(type=data_type,**kwargs)
        if(data_type == SignalType.PVT):
            if(with_logs):
                return self.post(f'{route}/SaveWithLogs', data = data, query = {'PressureUnit': pressure_unit, 'TemperatureUnit': temperature_unit}, **kwargs)
            return self.post(f'{route}/Load', data = data, query = {'PressureUnit': pressure_unit, 'TemperatureUnit': temperature_unit}, **kwargs)
        if(with_logs):
            return self.post(f'{route}/SaveWithLogs', data = data, **kwargs)
        return self.post(f'{route}/Save', data = data, **kwargs)

    # delete data
    def delete_data( self, data_type: Union[str,SignalType], data: List, start: Optional[Union[datetime,float]] = None, end: Optional[Union[datetime,float]] = None, **kwargs ) -> Any:
        """
        Delete data

        Parameters
        ----------
        data_type : str, SignalType
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        data : list
            Data
        start : datetime, float, None, default None
            Start of time/depth range
        end : datetime, float, default None
            End of time/depth range
        step : str, TimeIncrement, DepthIncrement, None, default None
            Step of time/depth range
        """
        data_type = self.get_signal_type_enum( data_type, **kwargs )
        route = self.get_signal_type_route(type=data_type,**kwargs)
        if(data_type == SignalType.TimeDependent or data_type == SignalType.StringTimeDependent or data_type == SignalType.DepthDependent):
            is_time_dependent = (data_type == SignalType.TimeDependent or data_type == SignalType.StringTimeDependent)
            range_type = 'time' if(is_time_dependent) else 'numeric'
            data_range = {
                'Start': self.get_json_valid_value(start,range_type,**kwargs),
                'End': self.get_json_valid_value(end,range_type,**kwargs)}
            self.post(f'{route}/Delete', data = data, query = data_range, **kwargs)
        return self.post(f'{route}/Delete', data = data, **kwargs)

    # load reference table info
    def get_ref_table_data_info( self, name: str, **kwargs ) -> Any:
        """
        Get reference table data info

        Parameters
        ----------
        name : str
            Reference table name
        """
        route = 'ReferenceTables'
        return self.get(f'{route}/{name}/ExistingData', **kwargs)

    # load reference table data
    def load_ref_table_data( self, name: str, entity: Union[str,Dict], date: Optional[Union[datetime,str]], **kwargs ) -> Any:
        """
        Load reference table data

        Parameters
        ----------
        name : str
            Reference table name
        entity : str, dict
            Entity object or Entity name
        date : str, datetime, None
            Date or None
        """
        route = 'ReferenceTables'
        entity_name = PetroVisorHelper.get_object_name(entity)
        date_str = self.get_json_valid_value(date,'time',**kwargs)
        if(date_str is None):
            date_str = ''
        return self.get(f'{route}/{name}/Data/{entity_name}/{date_str}', **kwargs)

    # save reference table data
    def save_ref_table_data( self, name: str, entity: Union[str,Dict], date: Optional[Union[datetime,float]], data: Union[Dict[float,float],List,pd.DataFrame], **kwargs ) -> Any:
        """
        Save reference table data

        Parameters
        ----------
        name : str
            Reference table name
        entity : str, dict
            Entity object or Entity name
        date : str, datetime, None
            Date or None
        """
        route = 'ReferenceTables'
        entity_name = PetroVisorHelper.get_object_name(entity)
        date_str = self.get_json_valid_value(date,'time',**kwargs)
        if(date_str is None):
           date_str = ''
        # prepare data
        if(isinstance(data,dict)):
            return self.put(f'{route}/{name}/Data/{entity_name}/{date_str}', data = data, **kwargs)
        else:
            # convert list to dictionary
            def __list_to_dict(x,num_cols,**kwargs):
                if(num_cols == 0):
                    return { self.get_json_valid_value(idx,'numeric',**kwargs): self.get_json_valid_value(row,'numeric',**kwargs) for idx,row in enumerate(x)}
                elif(num_cols == 1):
                    return { self.get_json_valid_value(idx,'numeric',**kwargs): self.get_json_valid_value(row[0],'numeric',**kwargs) for idx,row in enumerate(x)}
                elif(num_cols > 1):
                    return { self.get_json_valid_value(row[0],'numeric',**kwargs): self.get_json_valid_value(row[1],'numeric',**kwargs) for row in x}
                return {}
            if(isinstance(data,(list,np.ndarray,pd.DataFrame,pd.Series))):
                num_cols = PetroVisorHelper.get_num_cols(data)
                if(num_cols is None):
                    raise ValueError(f"PetroVisor::save_ref_table_data(): number of columns in the list should be either 2 or 1.")
                ref_table = __list_to_dict(PetroVisorHelper.to_list(data,**kwargs),num_cols,**kwargs)
            else:
                raise ValueError(f"PetroVisor::save_ref_table_data(): invalid data format '{type(data)}'. Should be either dict[float,float], list of iteratables, DataFrame, Series or array.")
            return self.put(f'{route}/{name}/Data/{entity_name}/{date_str}', data = ref_table, **kwargs)
    # delete reference table data
    def delete_ref_table_data( self, name: str, entity: Union[str,Dict], date: Optional[Union[datetime,float]], **kwargs ) -> Any:
        """
        Delete reference table data

        Parameters
        ----------
        name : str
            Reference table name
        entity : str, dict
            Entity object or Entity name
        date : str, datetime, None
            Date or None
        """
        route = 'ReferenceTables'
        entity_name = PetroVisorHelper.get_object_name(entity)
        date_str = self.get_json_valid_value(date,'time',**kwargs)
        if(date_str is None):
            date_str = ''
        return self.delete(f'{route}/{name}/Data/{entity_name}/{date_str}', **kwargs)

    # load pivot table data
    def load_pivot_table_data( self, name: str, entity_set: Optional[Union[str,Dict]] = None, scope: Optional[Union[str,Dict]] = None, num_rows: Optional[int] = 0, generate: bool = False, groupby_entity: bool = False, **kwargs ) -> Any:
        """
        Load PivotTable and return DataFrame

        Parameters
        ----------
        name : str
            Reference table name
        entity_set : str, dict
            EntitySet object or EntitySet name
        scope : str, dict
            Scope object or Scope name
        num_rows : int, default 0
            Number of rows to load
        generate : bool, default False
            Generate pivot table, otherwise load saved
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        route = 'PivotTables'
        if(entity_set or scope):
            options = {}
            if(entity_set):
                options['OverrideEntitySet'] = PetroVisorHelper.get_object_name(entity_set,**kwargs)
            if(scope):
                options['OverrideScope'] = PetroVisorHelper.get_object_name(scope,**kwargs)
            pivot_table_data = self.get(f'{route}/{name}/Generated/Options', data = options, **kwargs)
        elif(generate):
            pivot_table_data = self.get(f'{route}/{name}/Generated', **kwargs)
        else:
            pivot_table_data =  self.get(f'{route}/{name}/Saved', query = {'RowCount': self.get_json_valid_value(num_rows,'numeric')},**kwargs)
        if(pivot_table_data):
            return self.convert_pivot_table_to_dataframe(pivot_table_data, groupby_entity = groupby_entity, **kwargs)
        return None

    # save pivot table data
    def save_pivot_table_data( self, name: str, entity_set: Optional[str] = None, scope: Optional[str] = None, **kwargs ) -> Any:
        """
        Save PivotTable data

        Parameters
        ----------
        name : str
            Reference table name
        entity_set : str, dict
            EntitySet object or EntitySet name
        scope : str, dict
            Scope object or Scope name
        """
        route = 'PivotTables'
        if(entity_set or scope):
            options = {}
            if(entity_set):
                options['OverrideEntitySet'] = PetroVisorHelper.get_object_name(entity_set,**kwargs)
            if(scope):
                options['OverrideScope'] = PetroVisorHelper.get_object_name(scope,**kwargs)
            self.post(f'{route}/{name}/Save/Options', data = options, **kwargs)
        return self.get(f'{route}/{name}/Save', **kwargs)

    # delete pivot table data
    def delete_pivot_table_data( self, name: str, **kwargs ) -> Any:
        """
        Delete PivotTable data

        Parameters
        ----------
        name : str
            Reference table name
        """
        route = 'PivotTables'
        return self.get(f'{route}/{name}/Delete', **kwargs)

    # save database table
    def save_table_to_database( self, df: pd.DataFrame, name: str, delete_existing: Optional[bool] = False, **kwargs ) -> Any:
        """
        Save table directly to database

        Parameters
        ----------
        df : DataFrame
            Table
        name : str
            Table name
        delete_existing : bool, default False
            Whether to delete existing table in database
        """
        route = 'Configuration/SaveDataTable'
        data = df.to_json(orient='records')
        return self.post(f'{route}', query = {'DeleteExisting':delete_existing,'TableName': name}, data = data, **kwargs)

    # get ML models
    def ml_models( self, **kwargs) -> Any:
        """
        Get ML Models
        """
        return self.get_items('MLModel',**kwargs)

    # get ML models
    def ml_model_names( self, **kwargs) -> Any:
        """
        Get ML Model names
        """
        return self.get_item_names('MLModel',**kwargs)

    # get ML model
    def ml_model( self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        return self.get_item('MLModel',model_name,**kwargs)

    # get ML model attribute
    def ml_model_attribute( self, model_name: str, attribute: str, **kwargs) -> Any:
        """
        Get ML Model type

        Parameters
        ----------
        model_name : str
            ML Model name
        attribute : str
            ML Model attribute
        """
        ml_model = self.ml_model(model_name,**kwargs)
        if(ml_model is None or not ml_model):
            raise RuntimeError(f"PetroVisor::ml_model_attribute(): ML Model '{model_name}' cannot be found! ")
        if(attribute in ml_model):
            return ml_model[attribute]
        raise RuntimeError(f"PetroVisor::ml_model_attribute(): Unknown ML Model attribute '{attribute}'! ")

    # get ML model type
    def ml_model_type( self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model type

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        return self.ml_model_attribute(model_name, 'Type', **kwargs)

    # get ML model features and label
    def ml_model_features_and_label( self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model features and label

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        features = {}
        features_script = self.ml_model_attribute(model_name, 'TableFormula', **kwargs)
        feature_tables = self.get_psharp_script_columns_and_signals(features_script,**kwargs)
        if(feature_tables):
            for table_name,table in feature_tables.items():
                if(table):
                    return table
        return features

    # get ML model features
    def ml_model_features( self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model features

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        features = self.ml_model_features_and_label(model_name,**kwargs)
        label = self.ml_model_attribute(model_name, 'LabelColumnName', **kwargs)
        return { k: v for k,v in features.items() if k != label}

    # get ML model feature names
    def ml_model_feature_names( self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model feature names

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        features = self.ml_model_features(model_name,**kwargs)
        return list(features.keys())

    # get ML model label
    def ml_model_label( self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model label

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        label = self.ml_model_attribute(model_name, 'LabelColumnName', **kwargs)
        features = self.ml_model_features_and_label(model_name,**kwargs)
        for k,v in features.items():
            if k == label:
                return label, v
        return label, None

    # get ML model label name
    def ml_model_label_name( self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model label name

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        return self.ml_model_attribute(model_name, 'LabelColumnName', **kwargs)

    # get ML trainers and metrics
    def ml_trainers_and_metrics( self, model_type: Union[str,MLModelType], **kwargs) -> Any:
        """
        Get ML trainers and metrics

        Parameters
        ----------
        model_type : str, MLModelType
            ML Model type: 'Regression', 'BinaryClassification', 'MultipleClassification', 'Clustering', 'NaiveBayes', 'NaiveBayesCategorical'
        """
        route = 'MLModels/TrainersAndMetrics'
        model_type = self.get_ml_model_type_enum(model_type,**kwargs).name
        return self.get(route,query={'ModelType':model_type},**kwargs)

    # get ML trainers
    def ml_trainers( self, model_type: Union[str,MLModelType], **kwargs) -> Any:
        """
        Get ML trainers

        Parameters
        ----------
        model_type : str, MLModelType
            ML Model type: 'Regression', 'BinaryClassification', 'MultipleClassification', 'Clustering', 'NaiveBayes', 'NaiveBayesCategorical'
        """
        model_type = self.get_ml_model_type_enum(model_type,**kwargs).name
        ml_trainers_and_metrics = self.ml_trainers_and_metrics(model_type, **kwargs)
        if(ml_trainers_and_metrics is not None and ml_trainers_and_metrics):
            return ml_trainers_and_metrics['Trainers']
        raise RuntimeError(f"PetroVisor::ml_trainers(): Unknown ML Model type: '{model_type}'!")

    # get ML metrics
    def ml_metrics( self, model_type: Union[str,MLModelType], **kwargs) -> Any:
        """
        Get ML metrics

        Parameters
        ----------
        model_type : str, MLModelType
            ML Model type: 'Regression', 'BinaryClassification', 'MultipleClassification', 'Clustering', 'NaiveBayes', 'NaiveBayesCategorical'
        """
        model_type = self.get_ml_model_type_enum(model_type,**kwargs).name
        ml_trainers_and_metrics = self.ml_trainers_and_metrics(model_type, **kwargs)
        if(ml_trainers_and_metrics is not None and ml_trainers_and_metrics):
            return ml_trainers_and_metrics['Metrics']
        raise RuntimeError(f"PetroVisor::ml_trainers(): Unknown ML Model type: '{model_type}'!")

    # get ML pre-training statistics
    def ml_pre_training_statistics( self, model_name: str, **kwargs) -> Any:
        """
        Get ML pre-training statistics

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        route = 'MLModels/PreTrainingStatistics'
        return self.get(route,query={'ModelName':model_name},**kwargs)

    # get ML post-training statistics
    def ml_post_training_statistics( self, model_name: str, entity: Union[str,dict] = None, **kwargs) -> Any:
        """
        Get ML post-training statistics

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        route = 'MLModels/PostTrainingStatistics'
        if(entity):
            request = {
                'ModelName': model_name
            }
            entity_name = PetroVisorHelper.get_object_name(entity)
            request['EntityName'] = entity_name
            return self.post(route,data=request,**kwargs)
        return self.get(route,query={'ModelName':model_name},**kwargs)

    # predict ML model
    def ml_predict( self, model_name: str, entity: Union[str,dict], data: dict, **kwargs) -> Any:
        """
        Get ML post-training statistics

        Parameters
        ----------
        model_name : str
            ML Model name
        entity : str, dict
            Entity object or Entitx name
        data : dict
            ML Model data
        """
        route = 'MLModels/Predict'
        entity_name = PetroVisorHelper.get_object_name(entity)
        request = {
            'ModelName': model_name,
            'EntityName': entity_name,
            'SourceData': data,
        }
        request = PetroVisorHelper.update_dict(request,**kwargs)
        return self.post(route,data=request,**kwargs)

    # train ML model
    def ml_train( self,
            model_name: str,
            time_to_train: int = 5,
            complete_case_only: bool = True,
            per_entity: bool = False,
            normalization: str = 'Auto',
            trainers: Optional[Union[str,List[str]]] = None,
            optimization_metric: str = '',
            validation_fraction: float = 0.1,
            cross_folds: int = 0,
            clusters: int = 0,
            test_fraction: float = 0.0,
            test_latin_hypercube: bool = True,
            entity_set: Optional[Union[str,dict]] = None,
            scope: Optional[Union[str,dict]] = None,
            as_request: bool = False,
            request_source: Optional[str] = 'manually by user',
            activity: Optional[str] = None,
            **kwargs) -> Any:
        """
        Get ML post-training statistics

        Parameters
        ----------
        model_name : str
            ML Model name
        time_to_train : int, default 5
            Time to train in seconds
        complete_case_only : bool, default True
            Train only on complete case data (all features, no nulls)
        per_entity : bool, default False
            Whether training model should be produced per entity
        trainers : str, list[str], default None
            Trainer or trainers to be used. If Nonem all available traibers will be used
        optimization_metric : str
            Optimization metrics
        cross_folds : int, default 0
            Number of cross folds
        clusters : int, default 0
            Number of clusters, only for clustering approach
        normalization : str, default 'Auto'
            Normalization type
        validation_fraction : float, default 0.1
            Validation set fraction from training data
        test_fraction : float, default 0.0
            Test set fraction from training data
        test_latin_hypercube : bool, default True
            Select test set using latin hypercube
        as_request : bool, default True
            Send train request
        request_source : str, default 'manually by user'
            Source of request
        activity : str
            Name of workflow activity to select best ML Model
        """
        route = 'MLModels/Train'
        request = {
            'ModelName': model_name,
            'Options': {
                'EntitySet': None,
                'Scope': None,
                'TestFraction': test_fraction,
                'TestLatinHypercube': test_latin_hypercube,
                'ValidationFraction': validation_fraction,
                'OptimizationMetric': optimization_metric,
                'TimeToTrain': time_to_train,
                'NumberOfClusters': clusters,
                'NumberOfCrossValidationFolds': cross_folds,
                'TrainersToExclude': [],
                'NormalizationType': self.get_ml_normalization_type_enum(normalization,**kwargs).name,
                'CompleteCasesOnly': complete_case_only,
            },
            'IsModelPerEntity': per_entity
        }
        # define trainers
        if(trainers):
            # get trainers for current model type
            ml_model_type = self.ml_model_type(model_name,**kwargs)
            ml_trainers = self.ml_trainers(ml_model_type,**kwargs)
            # define trainers to exclude
            if(not isinstance(trainers,list)):
                trainers = PetroVisorHelper.to_list(trainers)
            request['TrainersToExclude'] = [t for t in ml_trainers if t in trainers]
        # define training 'EntitySet'
        if(entity_set):
            if(isinstance(entity_set,str)):
                entity_set = self.get_item('EntitySet',entity_set,**kwargs)
            request['EntitySet'] = entity_set
        # define training 'Scope'
        if(scope):
            if(isinstance(scope,str)):
                scope = self.get_item('Scope',scope,**kwargs)
            request['Scope'] = scope
        # update options
        request['Options'] = PetroVisorHelper.update_dict(request['Options'],**kwargs)
        if(as_request):
            request['WorkspaceName'] = self.Workspace
            request['Source'] = request_source
            if(activity):
                request['Activity'] = activity
            self.post(f'{route}/AddRequest',data=request,**kwargs)
        return self.post(route,data=request,**kwargs)

    # check whether ML service is idle
    def ml_is_service_idle( self, **kwargs) -> Any:
        """
        Is ML service idle

        Parameters
        ----------
        """
        route = 'ModelTraining/Idle'
        return self.get(route, **kwargs)

    # get ML model training states
    def ml_get_model_training_states( self, exclude_processed: bool = False, **kwargs) -> Any:
        """
        Get ML model training states

        Parameters
        ----------
        exclude_processed : bool, default False
            Exclude processed states
        """
        route = 'ModelTraining'
        if(exclude_processed):
            self.get(f"{route}/NoProcessed", **kwargs)
        return self.get(route, **kwargs)

    # get ML model id
    def ml_get_model_training_id( self, model_name_or_id: Union[str,UUID], **kwargs) -> Any:
        """
        Get ML model training id

        Parameters
        ----------
        model_name_or_id : str, UUId
            ML Model name or ML Model Traning Process UUID
        """
        id = model_name_or_id
        if(isinstance(model_name_or_id,str)):
            ml_training_states = self.ml_get_model_training_states(exclude_processed=False, **kwargs)
            for state in ml_training_states:
                if(state['ModelName'].lower() == model_name_or_id.lower()):
                    id = state['Id']
        if(id is None):
            raise RuntimeError(f"PetroVisor::ml_get_model_training_id(): cannot find '{model_name_or_id}' in the training list!")
        return PetroVisorHelper.get_uuid(id)

    # get ML model training state
    def ml_get_model_training_state( self, model_name_or_id: Union[str,UUID], **kwargs) -> Any:
        """
        Get ML model training state

        Parameters
        ----------
        model_name_or_id : str, UUId
            ML Model name or ML Model Traning Process UUID
        """
        route = 'ModelTraining'
        uuid = self.ml_get_model_training_id(model_name_or_id,**kwargs)
        return self.get(f"{route}/{uuid}", **kwargs)

    # get ML model training results
    def ml_get_model_training_results( self, model_name_or_id: Union[str,UUID], **kwargs) -> Any:
        """
        Get ML model training results

        Parameters
        ----------
        model_name_or_id : str, UUId
            ML Model name or ML Model Traning Process UUID
        """
        route = 'ModelTraining/Results'
        uuid = self.ml_get_model_training_id(model_name_or_id,**kwargs)
        return self.get(f"{route}/{uuid}", **kwargs)

    # # update ML model training state
    # def ml_update_model_training_state( self, model_name_or_id: Union[str,UUID], status: Any, output = '', **kwargs) -> Any:
    #     """
    #     Update ML model training state

    #     Parameters
    #     ----------
    #     model_name_or_id : str, UUId
    #         ML Model name or ML Model Traning Process UUID
    #     status : Any
    #         ML Training State
    #     """
    #     route = 'ModelTraining/UpdateState'
    #     uuid = self.ml_get_model_training_id(model_name_or_id,**kwargs)
    #     query_string = {
    #         'Status': status
    #     }
    #     if(output):
    #         query_string['Output'] = output
    #     return self.post(f"{route}/{uuid}", query = query_string, **kwargs)

    # # update ML model training results
    # def ml_update_model_training_results( self, model_name_or_id: Union[str,UUID], results: Any, **kwargs) -> Any:
    #     """
    #     Update ML model training results

    #     Parameters
    #     ----------
    #     model_name_or_id : str, UUId
    #         ML Model name or ML Model Traning Process UUID
    #     """
    #     route = 'ModelTraining/UpdateResults'
    #     uuid = self.ml_get_model_training_id(model_name_or_id,**kwargs)
    #     return self.get(f"{route}/{uuid}", data = results, **kwargs)

    # run 'Workflow'
    def run_workflow( self, workflow: str, contexts: List[str] = [], scope: str = None, entity_set: str = None, schedule_name: str = 'Now', source: str = 'by Activity service', **kwargs) -> Any:
        """
        Run workflow

        Parameters
        ----------
        workflow : str
            Workflow name
        contexts : list[str], deafult []
            Contexts
        scope : str, default None
            Scope
        entity_set : str, default None
            EntitySet name
        schedule_name : str, default 'Now'
            Schedule name
        source : str, default 'by Activity service'
            Source name
        """
        data = {'WorkflowName': workflow,
            'WorkspaceName': self.Workspace,
            'Source': source,
            'ScheduleName': schedule_name,
            'ProcessingContexts': contexts,
        }
        if(scope):
            data['ProcessingScopeName'] = scope
        if(entity_set):
            data['ProcessingEntitySet'] = entity_set
        return self.post('WorkflowExecution/AddRequest', data=data, **kwargs)

    # get 'Workflow' execution state
    def get_workflow_execution_state( self, id: UUID, **kwargs ):
        """
        Get workflow execution state

        Parameters
        ----------
        id : UUID
            Workflow id
        """
        uuid = PetroVisorHelper.get_uuid(id)
        return self.get(f"WorkflowExecution/{uuid}", **kwargs)

    # get P# script names
    def get_psharp_script_names( self, **kwargs) -> List[str]:
        """
        Get P# script names
        """
        return self.get(f'Configuration/PSharpFunctions', **kwargs )

    # get P# script
    def get_psharp_script( self, name: str, **kwargs) -> Dict:
        """
        Get P# script

        Parameters
        ----------
        name : str
            P# script name
        """
        return self.get(f'PSharpScripts/{name}', **kwargs )

    # get P# script content
    def get_psharp_script_content( self, script: Union[str,Dict], **kwargs) -> str:
        """
        Get P# script content

        Parameters
        ----------
        script : str, dict
            P# script object or P# script name
        """
        # get P# script content
        if(isinstance(script,str)):
            script_content = script
            script = self.get_psharp_script( script, **kwargs)
        if(script is None and script_content):
            pass
        elif('Content' in script):
            script_content = script['Content']
        else:
            raise RuntimeError(f"PetroVisor::parse_psharp_script_content(): Couldn't get content of P# script '{script}'.")
        return script_content

    # parse P# script
    def parse_psharp_script( self, script: Union[str,Dict], options: Optional[Dict] = None, **kwargs) -> Dict:
        """
        Parse P# script

        Parameters
        ----------
        script : str, dict
            P# script object or P# script name
        options : dict, default None
            P# script parse options
        """
        # get P# script content
        script_content = self.get_psharp_script_content(script, **kwargs)
        # define options
        if(not options):
            options = {
                'TreatScriptContentAsScriptName': False,
                'NoMissedObjects': True
            }
            options = PetroVisorHelper.update_dict(options,**kwargs)
        return self.post(f'Parsing/Parsed', data = {'ScriptContent': script_content, 'Options': options }, **kwargs )

    # get P# script table names
    def get_psharp_script_table_names( self, script: Union[str,Dict], options: Optional[Dict] = None, **kwargs) -> List[str]:
        """
        Get P# script table names

        Parameters
        ----------
        script : str, dict
            P# script object or P# script name
        options : dict, default None
            P# script parse options
        """
        if(isinstance(script,str) or 'TableCalculations' not in script):
            psharp_script_parsed = self.parse_psharp_script(script, options = options, **kwargs )
        else:
            psharp_script_parsed = script
        if('TableCalculations' in psharp_script_parsed):
            table_names = [ t['Name'] for t in psharp_script_parsed['TableCalculations']]
        else:
            table_names = []
        return table_names

    # get P# script tables, columns and siganls
    def get_psharp_script_columns_and_signals( self, script: Union[str,Dict], options: Optional[Dict] = None, **kwargs) -> Dict:
        """
        Get P# script columns and signals

        Parameters
        ----------
        script : str, dict
            P# script object or P# script name
        options : dict, default None
            P# script parse options
        """
        if(isinstance(script,str) or 'TableCalculations' not in script):
            psharp_script_parsed = self.parse_psharp_script(script, options = options, **kwargs )
        else:
            psharp_script_parsed = script
        # get psharp script signals
        table_signals = {}
        if('TableCalculations' in psharp_script_parsed):
            for t in psharp_script_parsed['TableCalculations']:
                table_name = t['Name']
                table_columns = t['Columns']
                table_signals[table_name] = {}
                for col in table_columns:
                    col_name = col['Name']
                    unit_name = col['Unit']['Name']
                    full_column_name = col_name + ' ' + '[' + unit_name + ']'
                    col_formula = col['Formula']
                    col_signal = col_formula.split('"')
                    signal_name = col_signal[1]
                    signal_unit_name = col_signal[3]
                    #table_signals[table_name][full_column_name] = {'Signal': signal_name, 'Unit': signal_unit_name}
                    table_signals[table_name][col_name] = {'Unit': unit_name, 'Signal': signal_name, 'SignalUnit': signal_unit_name}
        return table_signals

    # load P# table
    def load_psharp_table( self, script_name: str, table: Optional[str] = None, with_entity_column: bool = True, groupby_entity: bool = False, load_full_table_info: bool = False, **kwargs) -> Union[pd.DataFrame,List[pd.DataFrame]]:
        """
        Load P# table and return DataFrame

        Parameters
        ----------
        script_name : str
            P# script name
        table : str, default None
            Table name or id. 0 is first table, -1 is last table.
            If None, all tables will be loaded and dictionary with table name as key will be returned
        with_entity_column : bool, default True
            Load table with entity column, otherwise columns will be named as "EntityName : ColumnName"
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        load_full_table_info : bool, default False
            Load table using api call with full table content
        """
        # define whether table should contain entity column
        #is_entity_table = groupby_entity or with_entity_column
        is_entity_table = with_entity_column
        
        # get table names
        if(table is None or not isinstance(table,str) ):
            
            # get table id
            if(table is not None):
                try:
                    table_id = int(table)
                except:
                    raise RuntimeError(f"PetroVisor::load_table_from_psharp(): {table} should be either 'string'(table name), 'integer'(table id) or 'None'(all tables) !")
            else:
                table_id = None

            # get table name
            if(is_entity_table or table_id != 0):
                # get table names
                table_names = self.get_psharp_script_table_names( script_name, **kwargs )
                # get table name
                if(table_id is not None):
                    num_tables = len(table_names)
                    # if( table_id >= num_tables ):
                    #     table_id = num_tables - 1
                    # elif( table_id < 0 and (num_tables + table_id) < 0 ):
                    #     table_id = 0
                    if( table_id >= num_tables or (num_tables + table_id) < 0 ):
                        return None
                    table_name = table_names[table_id]
                else:
                    table_name = None
            else:
                table_names = []
                table_name = ''
            
        elif(isinstance(table,str)):
            table_id = None
            table_name = table
            table_names = []
        
        # get table from P# script
        psharp_table = None
        psharp_tables = None
        if(is_entity_table and table_name):
            psharp_table = self.get(f'PSharpScripts/{script_name}/ExecuteAsBITable', query = {'Table': table_name}, **kwargs )
        elif(not is_entity_table and ( table_name or table_id == 0 ) ):
            if(table_id == 0):
                psharp_table = self.get(f'PSharpScripts/{script_name}/ExecuteAsTable', **kwargs )
            else:
                psharp_table = self.get(f'PSharpScripts/{script_name}/ExecuteAsTable', query = {'Table': table_name}, **kwargs )
        else:
            # if(is_entity_table):
            #     psharp_tables = [ self.get(f'PSharpScripts/{script_name}/ExecuteAsBITable', query = {'Table': table_name}, **kwargs ) for table_name in table_names]
            # else:
            #     psharp_tables = [ self.get(f'PSharpScripts/{script_name}/ExecuteAsTable', query = {'Table': table_name}, **kwargs ) for table_name in table_names]

            script_content = self.get_psharp_script_content(script_name, **kwargs)
            if(load_full_table_info):
                psharp_tables = self.post(f'PSharpScripts/ExecuteScript', data = {'ScriptContent': script_content}, **kwargs )
            else:
                psharp_tables = self.post(f'PSharpScripts/Execute', data = {'ScriptContent': script_content}, **kwargs )
        
        # convert tables
        if(psharp_tables is not None):
            return { table_name: self.convert_psharp_table_to_dataframe(t, groupby_entity = groupby_entity, **kwargs) for table_name,t in zip(table_names,psharp_tables)}
        if(psharp_table is not None):
            return self.convert_psharp_table_to_dataframe(psharp_table, groupby_entity = groupby_entity, **kwargs)
        return None

    # save data from table to PetroVisor
    def save_table_data( self, df: pd.DataFrame, delimiter: str = '\t', signals: Optional[Dict] = None, chunksize = 10000, only_existing_entities: bool = True, entity_type: str = '', entities: Optional[Dict] = None, **kwargs) -> None:
        """
        Save DataFrame data to corresponding signals

        Parameters
        ----------
        df : DataFrame, str
            Table or filename
        delimiter : str, default '\t'
            Delimiter used while reading table from file
        signals : dict, default None
            Dictionary map from 'table column name' to 'workspace signal name'
        chunksize : int, default 10000
            Save data by splitting it into several chunks of specified size and performing separate requests
        entities : dict, default None
            Dictionary map from 'table entity name' to 'workspace entity name'
        only_existing_entities : bool, deafult True
            Save data only if entity exist in workspace
        entity_type : str, default None
            Save data only for specified entity type
        """
        # read table
        if (isinstance(df,str)):
            ext = PetroVisorHelper.get_file_extension(df,**kwargs)
            if(ext.lower() in ['.xlsx','.xls']):
                df = pd.read_excel(df)
            else: #elif(ext.lower() in ['.csv']):
                df = pd.read_csv(df, delimiter = delimiter)
        if (df is not None):
            if (chunksize and (df.shape[0] > chunksize) ):
                for start in range(0,df.shape[0],chunksize):
                    end = min(start + chunksize, df.shape[0])
                    self.save_table_data(df[start:end], delimiter = delimiter, signals = signals, chunksize = chunksize, only_existing_entities = only_existing_entities, entity_type = entity_type, entities = entities, **kwargs)
                return None
            # get PetroVisor data from DataFrame
            data_to_save = self.get_signal_data_from_dataframe( df, signals = signals, only_existing_entities = only_existing_entities, entity_type = entity_type, entities = entities, **kwargs)
            # save data
            for data_type, data in data_to_save.items():
                if(data):
                    self.post(f'{self.get_signal_type_route(data_type)}/Save', data = data, **kwargs)
        return None

    # convert PivotTable to DataFrame
    def convert_pivot_table_to_dataframe( self, data: List, groupby_entity: bool = False, **kwargs):
        """
        Convert PivotTable to DataFrame

        Parameters
        ----------
        data : list
            PivotTable data
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        try:
            if(data):
                # get columns
                cols = data[0]
                if(len(data)>1):
                    df = pd.DataFrame(data=data[1:],columns=cols)
                else:
                    df = pd.DataFrame(columns=cols)
            else:
                df = pd.DataFrame()

            # assign column types
            columns = df.columns
            columns_dtype = { col: 'Numeric' for col in columns}
            entity_col = self.get_entity_column_name(**kwargs)
            entity_type_col = self.get_entity_type_column_name(**kwargs)
            alias_col = self.get_alias_column_name(**kwargs)
            is_opportunity_col = self.get_opportunity_column_name(**kwargs)
            date_col = self.get_date_column_name(**kwargs)
            time_col = self.get_time_column_name(**kwargs)
            for col in [date_col,time_col]:
                columns_dtype[col] = 'Time'
            for col in [entity_col,alias_col,entity_type_col]:
                columns_dtype[col] = 'String'
            columns_dtype[is_opportunity_col] = 'Bool'
            df = self.assign_dataframe_column_types(df, columns_dtype, **kwargs)

            # group by entity
            if(groupby_entity):
                df = { e: df_group for e, df_group in df.groupby(entity_col) }
        except:
            raise RuntimeError(f"PetroVisor::convert_pivot_table_to_dataframe(): Couldn't convert PivotTable to DataFrame")
        return df

    # convert P# table to DataFrame
    def convert_psharp_table_to_dataframe( self, psharp_table: Union[Dict,List], groupby_entity: bool = False, **kwargs) -> pd.DataFrame:
        """
        Convert P# table to DataFrame

        Parameters
        ----------
        psharp_table : dict, list
            P# table data
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        if(psharp_table is None):
            return None
        
        # standard columns
        entity_col = self.get_entity_column_name()
        alias_col = self.get_alias_column_name()
        is_opportunity_col = self.get_opportunity_column_name(**kwargs)
        entity_type_col = self.get_entity_type_column_name(**kwargs)
        date_col = self.get_date_column_name()
        depth_col = self.get_depth_column_name()

        if( isinstance(psharp_table, list) ):
            rows = len(psharp_table) - 1
            columns = psharp_table[0].split('\t') if(len(psharp_table) > 0) else []
            num_cols = len(columns)

            # define type of table
            with_entity_col = entity_col in columns
            is_static = date_col not in columns

            # create DataFrame
            if( not with_entity_col and groupby_entity ):
                col_entities = []
                col_names = []
                # process columns and collect entities
                for i,col in enumerate(columns):
                    c = col.split(':')
                    if(len(c) > 1):
                        centity = c[0].strip()
                        cname = c[1].strip()
                    else:
                        centity = ''
                        cname = col
                    col_entities.append(centity)
                    col_names.append(cname)
                # list of entities
                entities = list(set([ e for e in col_entities if e]))
                # data
                data = { e: [] for e in entities }       
                columns = { e: [cname for centity,cname in zip(col_entities,col_names) if not centity or centity == e] for e in entities}
                # group data by entity
                if(rows > 0):
                    for i,s in enumerate(psharp_table[1:]):
                        row = s.split('\t')
                        for e in entities:
                            data[e].append([cv for cv,ce in zip(row,col_entities) if not ce or ce == e])

                # create DataFrame
                df = { e: pd.DataFrame(data[e],columns=columns[e]) for e in entities }

                # assign column types
                columns_short_dtype = {
                    entity_col: 'String',
                    alias_col: 'String',
                    date_col: 'Time',
                    depth_col: 'Numeric',
                }
                for e in entities:
                    df[e] = self.assign_dataframe_column_types(df[e], columns_short_dtype, **kwargs)
            else:
                data = []
                if(rows > 0):
                    for i,s in enumerate(psharp_table[1:]):
                        row = s.split('\t')
                        data.append(row)
                
                # create DataFrame
                df = pd.DataFrame(data,columns=columns)

                # assign column types
                columns_short_dtype = {
                    entity_col: 'String',
                    alias_col: 'String',
                    date_col: 'Time',
                    depth_col: 'Numeric',
                }
                df = self.assign_dataframe_column_types(df, columns_short_dtype, **kwargs)

                # group by entity
                if(groupby_entity):
                    df = { e: df_group for e, df_group in df.groupby(entity_col) }
        
        elif(psharp_table is not None and 'TableName' in psharp_table and 'ResultsOrder' in psharp_table):
            columns_short = psharp_table['ResultsOrder']
            columns_order = { c: idx for idx,c in enumerate(columns_short) }
            columns_short_units = { c: None for c in columns_short }
            columns_short_dtype = { c: None for c in columns_short }
            num_cols = len(columns_short)
            data = {}
            depths = {}
            dates = {}
            date_depth_pair = {}
            entities = set()
            if('Columns' in psharp_table or 'Data' in psharp_table):
                # get column data
                def _get_column_data(col, dtype = None):
                    if('ResultName' in col):
                        col_entity_name = col['EntityName']
                        col_dtype = dtype if(dtype) else 'Numeric'
                        col_name = col['ResultName']
                        col_signal_name = ''
                        col_unit_name = col['UnitName']
                        col_data = col['Data']
                    else:
                        col_entity_name = col['Entity']
                        result = col['Result']
                        col_name = result['Name']
                        col_dtype = dtype if(dtype) else 'Numeric'
                        # col_dtype = result['ResultType'] # 'Numeric', 'String', 'Time', 'Boolean', 'Unknown'
                        col_formula = result['Formula']
                        col_unit = result['Unit']
                        col_signal_name = col['Signal']
                        col_unit_name = col['Unit']
                        col_data = col['Data']
                    return col_entity_name, col_name, col_unit_name, col_data, col_dtype
                for col_type in ['Columns','ColumnsDepth','ColumnsString','ColumnsTime','ColumnsBool','Data','DataDepth','DataString','DataTime','DataBool']:
                    dtype = 'String' if ('String' in col_type) else 'Time' if('Time' in col_type) else 'Bool' if('Bool' in col_type) else 'Numeric'
                    if(col_type in psharp_table):
                        for col in psharp_table[col_type]:
                            col_entity_name, col_name, col_unit_name, col_data, col_dtype = _get_column_data(col, dtype = dtype)
                            # add entity
                            entities.add(col_entity_name)
                            # get column index
                            col_idx = columns_order[col_name]
                            # asiign column dtype
                            if(columns_short_dtype[col_name] is None):
                                columns_short_dtype[col_name] = col_dtype
                            # asiign column unit
                            if(columns_short_units[col_name] is None):
                                columns_short_units[col_name] = col_unit_name
                            # assign data
                            if(col_entity_name not in dates):
                                dates[col_entity_name] = set()
                            if(col_entity_name not in depths):
                                depths[col_entity_name] = set()
                            if(col_entity_name not in date_depth_pair):
                                date_depth_pair[col_entity_name] = set()
                            if(col_entity_name not in data):
                                data[col_entity_name] = [ None for _ in columns_short ]
                            if(data[col_entity_name][col_idx] is None):
                                data[col_entity_name][col_idx] = []
                            for d in col_data:
                                # time numeric data
                                if('Date' in d and 'Value' in d):
                                    dates[col_entity_name].add(d['Date'])
                                    # dates_depths[col_entity_name].add(d['Date'],None))
                                    data[col_entity_name][col_idx].append({'Date': d['Date'], 'Depth': None, 'Value': d['Value']})
                                # depth numeric data
                                elif('Depth' in d and 'Value' in d):
                                    depths[col_entity_name].add(d['Depth'])
                                    # dates_depths[col_entity_name].add((None,d['Depth']))
                                    data[col_entity_name][col_idx].append({'Date': None, 'Depth': d['Depth'], 'Value': d['Value']})
                                # static value
                                elif('Value' in d):
                                    # dates_depths[col_entity_name].add((None,None))
                                    data[col_entity_name][col_idx].append({'Date': None, 'Depth': None, 'Value': d['Value']})
                                # unknown value
                                else:
                                    pass
                # collect columns
                columns = [ col_name + ' ' + f'[{columns_short_units[col_name]}]' for col_name in columns_short]
                columns_dtype = { col_name: columns_short_dtype[col_name_short] for col_name_short,col_name in zip(columns_short,columns)}
                columns_dtype[date_col] = 'Time'
                columns_dtype[depth_col] = 'Numeric'
                columns_dtype[entity_col] = 'String'
                # columns_dtype[alias_col] = 'String'
                # columns_dtype[entity_type_col] = 'String'
                # columns_dtype[is_opportunity_col] = 'Bool'

                # get 'Entity' column
                entities = sorted(list(entities))

                # check for 'Date' column
                has_dates = False
                for e,d in dates.items():
                    if(len(d)>0):
                        has_dates = True
                        break
                if(has_dates):
                    dates = { e: sorted(list(d)) if (len(d) > 0) else [None] for e,d in dates.items()}
                else:
                    dates = {}
                # check for 'Depth' column
                has_depths = False
                for e,d in depths.items():
                    if(len(d)>0):
                        has_depths = True
                        break
                if(has_depths):
                    depths = { e: sorted(list(d)) if (len(d) > 0) else [None] for e,d in depths.items()}
                else:
                    depths = {}
                # check for 'Date' and 'Depth' column
                has_date_depth_pairs = False
                for e,d in date_depth_pair.items():
                    if(len(d)>0):
                        has_date_depth_pairs = True
                        break
                if(has_date_depth_pairs):
                    date_depth_pair = { e: sorted(list(d)) if (len(d) > 0) else [(None,None)] for e,d in date_depth_pair.items()}
                else:
                    date_depth_pair = {}

                # add index columns (order is important): 1-'Entity',2-'Date',3-'Depth'
                if(has_depths):
                    columns.insert(0, depth_col)
                if(has_dates):
                    columns.insert(0, date_col)
                columns.insert(0, entity_col)

                # set index
                def _get_value(entity,col_idx):
                    return data[entity][col_idx]
                def _get_date_value(entity,col_idx,date):
                    for d in data[entity][col_idx]:
                        if(d['Date'] == date):
                            return d['Value']
                    return None
                def _get_depth_value(entity,col_idx,depth):
                    for d in data[entity][col_idx]:
                        if(d['Depth'] == depth):
                            return d['Value']
                    return None
                def _get_date_depth_value(entity,col_idx,date,depth):
                    # time-depth data
                    if(date is not None and depth is not None):
                        for d in data[entity][col_idx]:
                            if(d['Date'] == date or d['Depth'] == depth):
                                return d['Value']
                    # time data
                    elif(date is not None):
                        return _get_date_value(entity,col_idx,date)
                    # depth data
                    elif(depth is not None):
                        return _get_depth_value(entity,col_idx,date)
                    return None
                if(has_dates and has_depths and has_date_depth_pairs):
                    index_tuples = [ (e, dt, dh) for e in entities for dt in [None,*dates[e]] for dh in [None,*depths[e]] if( (dt is None) or (dh is None) or (len(date_depth_pair[e]) > 0 and ((dt,dh) in date_depth_pair[e])))]
                    index = pd.MultiIndex.from_tuples(index_tuples, names=[entity_col, date_col, depth_col])
                    data = [ [e, dt, dh, *[_get_date_depth_value(e,col_idx,dt,dh) for col_idx in range(0,num_cols)]] for e in entities for dt in [None,*dates[e]] for dh in [None,*depths[e]] if( (dt is None) or (dh is None) or (len(date_depth_pair[e]) > 0 and ((dt,dh) in date_depth_pair[e]))) ]
                elif(has_dates and has_depths):
                    # index_tuples = [ (e, dt, dh) for e in entities for dt in dates[e] for dh in depths[e]]
                    # index = pd.MultiIndex.from_tuples(index_tuples, names=[entity_col, date_col, depth_col])
                    # data = [ [e, dt, dh, *[_get_date_depth_value(e,col_idx,dt,dh) for col_idx in range(0,num_cols)]] for e in entities for dt in dates[e] for dh in depths[e] ]
                    index_tuples = [ (e, dt, dh) for e in entities for dt in [None,*dates[e]] for dh in [None,*depths[e]] if( (dt is None) or (dh is None) )]
                    index = pd.MultiIndex.from_tuples(index_tuples, names=[entity_col, date_col, depth_col])
                    data = [ [e, dt, dh, *[_get_date_depth_value(e,col_idx,dt,dh) for col_idx in range(0,num_cols)]] for e in entities for dt in [None,*dates[e]] for dh in [None,*depths[e]] if( (dt is None) or (dh is None) ) ]
                elif(has_dates):
                    index_tuples = [ (e, dt) for e in entities for dt in dates[e]]
                    index = pd.MultiIndex.from_tuples(index_tuples, names=[entity_col, date_col])
                    data = [ [e, dt, *[_get_date_value(e,col_idx,dt) for col_idx in range(0,num_cols)]] for e in entities for dt in dates[e] ]
                elif(has_depths):
                    index_tuples = [ (e, dh) for e in entities for dh in depths[e]]
                    index = pd.MultiIndex.from_tuples(index_tuples, names=[entity_col, depth_col])
                    data = [ [e, dh, *[_get_depth_value(e,col_idx,dh) for col_idx in range(0,num_cols)]] for e in entities for dh in depths[e] ]
                else:
                    index_tuples = [ e for e in entities]
                    index = pd.Index(index_tuples, name=entity_col)
                    data = [ [e, [_get_value(e,col_idx) for col_idx in range(0,num_cols)]] for e in entities ]

                # create DataFrame
                # df_dtype = [ (c,self.convert_to_dtype_name(columns_dtype[c])) for c in columns]
                # df = pd.DataFrame(data,columns=columns,dtype=df_dtype)
                df = pd.DataFrame(data,columns=columns)
                
                # assign column types
                df = self.assign_dataframe_column_types(df, columns_dtype, **kwargs)

                # set index
                # df.set_index(index)
                # df = df.reset_index(drop=False)

                # group by entity
                if(groupby_entity):
                    df = { e: df_group for e, df_group in df.groupby(entity_col) }
            else:
                raise RuntimeError("PetroVisor::convert_psharp_table_to_dataframe(): unknown P# table type!")
        else:
            raise RuntimeError("PetroVisor::convert_psharp_table_to_dataframe(): unknown P# table type!")

        return df

    # convert DataFrame to P# table
    def get_signal_data_from_dataframe( self, df: pd.DataFrame, signals: Optional[Dict] = None, only_existing_entities: bool = True, entity_type: bool = '', entities: Optional[Dict] = None, **kwargs ) -> List:
        """
        Get signal data from DataFrame

        Parameters
        ----------
        df : DataFrame
            Table
        signals : dict, default None
            Dictionary map from 'table column name' to 'workspace signal name'
        entities : dict, default None
            Dictionary map from 'table entity name' to 'workspace entity name'
        only_existing_entities : bool, deafult True
            Save data only if entity exist in workspace
        entity_type : str, default None
            Save data only for specified entity type
        """
        # get columns
        columns = df.columns
        num_cols = len(columns)

        # standard columns
        entity_col = self.get_entity_column_name()
        alias_col = self.get_alias_column_name()
        date_col = self.get_date_column_name()
        depth_col = self.get_depth_column_name()

        # entities map
        entities_map = copy.deepcopy(entities) if(entities) else {}

        # filter out undefined entities
        select_entities = self.get_entity_names( entity_type = entity_type, **kwargs) if(only_existing_entities) else None
        if(select_entities and entities_map):
            entities_map_rev = {v: k for k,v in entities_map.items()}
            select_entities = [entities_map_rev[e] if(e in entities_map_rev) else e for e in select_entities]

        # data containers
        data_to_save = {s.name: [] for s in SignalType}

        # collect data info
        with_entity_col = entity_col in columns
        if(not with_entity_col):

            # collect entities and column names
            col_entities = []
            col_names = []
            
            # process columns and collect entities
            for i,col in enumerate(columns):
                c = col.split(':')
                if(len(c) > 1):
                    centity = c[0].strip()
                    column_name = c[1].strip()
                else:
                    centity = ''
                    column_name = col.strip()
                col_entities.append(centity)
                col_names.append(column_name)
            # list of entities
            entities = list(set([ e for e in col_entities if e]))
            # get column data info
            col_data = { e: [(cname,cidx) for cidx,(centity,cname) in enumerate(zip(col_entities,col_names)) if centity == e] for e in entities if (select_entities is None) or (e in select_entities) }
        else:
            # get column names
            col_names = columns
            # get list of entities
            entities = list(set(df[entity_col].values.tolist())) if(entity_col in columns) else []
            # get column data info
            col_data = { e: [ (cname,cidx) for cidx,cname in enumerate(columns)] for e in entities if (select_entities is None) or (e in select_entities) }

        # remap entities data
        if(entities_map):
            col_data = { entities_map[e] if(e in entities_map) else e: d for e,d in col_data.items()}

        # 'Date' column
        date_index = None
        for i,column_name in enumerate(col_names):
            if( column_name == date_col ):
                date_index = i
                break

        # 'Depth' column
        depth_index = None
        for i,column_name in enumerate(col_names):
            if( column_name == depth_col ):
                depth_index = i
                break

        # get signal info
        def _get_signal_info( column_name: str, signals: Optional[Dict] = None):
            column_name_without_unit = self.get_column_name_without_unit(column_name)
            column_unit_name = self.get_column_unit(column_name)
            if(signals):
                signal = signals[column_name] if(column_name in signals) else signals[column_name_without_unit] if(column_name_without_unit in signals) else None
            else:
                signal = None
            if(not signal):
                signal_name = column_name_without_unit
                signal_unit = column_unit_name
            elif(isinstance(signal,str)):
                signal_name_without_unit = self.get_column_name_without_unit(signal)
                signal_unit_name = self.get_column_unit(signal)
                signal_name = signal_name_without_unit
                signal_unit = signal_unit_name if(signal_unit_name) else column_unit_name
            elif(isinstance(signal,tuple) or isinstance(signal,list) and len(signal) > 0 ):
                signal_name = signal[0]
                signal_unit = signal[1] if(len(signal) > 1) else column_unit_name
            else:
                signal_name = self.get_column_name_without_unit(column_name)
                signal_unit = self.get_column_unit(column_name)
                for fname in ['Signal','Name','SignalName']:
                    if(fname in signal):
                        signal_name = signal[fname]
                        break
                    elif(fname.lower() in signal):
                        signal_name = signal[fname.lower()]
                        break
                for fname in ['Unit','UnitName','SignalUnit']:
                    if(fname in signal):
                        signal_unit = signal[fname]
                        break
                    elif(fname.lower() in signal):
                        signal_unit = signal[fname.lower()]
                        break
            # get signal
            signal_obj = self.get_signal(signal_name, **kwargs)
            if(signal_obj):
                if(not signal_unit and 'StorageUnitName' in signal_obj):
                    signal_unit = signal_obj['StorageUnitName']
                signal_type = signal_obj['SignalType'] if('SignalType' in signal_obj) else None
                return {
                    'Signal': signal_name,
                    'Unit': signal_unit,
                    'SignalType': signal_type }
            return None

        # check whether non index column
        def _is_index_column( column_name: str ) -> bool:
            return ( column_name == date_col ) or ( column_name == depth_col ) or ( column_name == entity_col ) or ( column_name == alias_col )
        # get column data
        def _get_column_data(column_index: int, entity_name: str) -> List:
            if (not with_entity_col):
                return df.iloc[:,column_index].to_list()
            return df[ df[entity_col] == entity_name ].iloc[:,column_index].to_list()

        # get signals
        col_names = list(set(col_names))
        column_signals = { cname: _get_signal_info(cname, signals = signals) for cname in col_names if not _is_index_column(cname) }
        
        # collect signals data
        for entity_name, d in col_data.items():
            # collect signals data
            for col in d:
                # column name
                column_name = col[0]
                # column index
                column_index = col[1]
                if(column_name in column_signals and column_signals[column_name]):
                    
                    signal = column_signals[column_name]
                    signal_name = signal['Signal']
                    signal_unit_name = signal['Unit']
                    signal_type = signal['SignalType']

                    # static signal
                    if( signal_type == SignalType.Static.name or signal_type == SignalType.String.name ):
                        dtype = 'Numeric' if(signal_type == 'Static') else 'String'
                        static_data = _get_column_data(column_index,entity_name)
                        if(static_data and len(static_data) > 0):
                            value = static_data[0] if(signal_type == 'Static') else static_data[0]
                            data_to_save[signal_type].append({
                                'Entity': entity_name,
                                'Signal': signal_name,
                                'Unit': signal_unit_name,
                                'Data': self.get_json_valid_value(value,dtype=dtype,**kwargs)
                            })
                    # time signal
                    elif( signal_type == SignalType.TimeDependent.name or signal_type == SignalType.StringTimeDependent.name ):
                        dtype = 'Numeric' if(signal_type == 'TimeDependent') else 'String'
                        data_to_save[signal_type].append({
                            'Entity': entity_name,
                            'Signal': signal_name,
                            'Unit': signal_unit_name,
                            'Data': [{ 'Date': self.get_json_valid_value(dvalue,dtype='Time',**kwargs), 'Value': self.get_json_valid_value(value,dtype=dtype,**kwargs)} for dvalue, value in zip(_get_column_data(date_index,entity_name),_get_column_data(column_index,entity_name))]
                        })
                    # depth signal
                    elif( signal_type == SignalType.DepthDependent.name ):
                        dtype = 'Numeric'
                        data_to_save[signal_type].append({
                            'Entity': entity_name,
                            'Signal': signal_name,
                            'Unit': signal_unit_name,
                            'Data': [{ 'Depth': self.get_json_valid_value(dvalue,dtype='Numeric',**kwargs), 'Value': self.get_json_valid_value(value,dtype=dtype,**kwargs)} for dvalue, value in zip(_get_column_data(depth_index,entity_name),_get_column_data(column_index,entity_name))]
                        })
                    else:
                        print(f'Column signals: {column_signals}')
                        print(f'Signal: {signal}')
                        raise RuntimeError(f"PetroVisor::get_signal_data_from_dataframe(): Signal type: '{signal_type}' is not supported yet.")
        return data_to_save


    # get column name without unit
    def get_column_name_without_unit( self, column_name: str, **kwargs ) -> str:
        """
        Get column name without unit from column name

        Parameters
        ----------
        column_name : str
            Column name
        """
        cname = column_name.split('[')[0].strip()
        return cname

    # get column unit
    def get_column_unit( self, column_name: str, **kwargs ) -> str:
        """
        Get column unit from column name

        Parameters
        ----------
        column_name : str
            Column name
        """
        column_name = column_name.strip()
        cunit = re.findall('\[(.*?)\]',column_name)
        if(cunit and len(cunit) > 0):
            return cunit[0]
        return ''

    # get column name and unit
    def get_column_name_and_unit( self, column_name: str, **kwargs ) -> str:
        """
        Get column name and unit from column name

        Parameters
        ----------
        column_name : str
            Column name
        """
        column_name = column_name.strip()
        cname = self.get_column_name_without_unit(column_name, **kwargs)
        cunit = self.get_column_unit( column_name, **kwargs )
        return cname, cunit

    # get valid json
    def get_json_valid_value( self, value: Any, dtype: Optional[str] = 'unknown', **kwargs ) -> Any:
        """
        Convert value to json accepted format

        Parameters
        ----------
        value : Any
            Value
        dtype : str, default 'unknown'
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        is_null = pd.isnull(value)
        dtype = dtype.lower()
        if(dtype == 'numeric' or dtype == 'float64'):
            return None if(is_null) else None if(isinstance(value, str) and not value.strip()) else value
        elif(dtype == 'time' or dtype == 'datetime64[ns]'):
            return None if(is_null) else None if(isinstance(value, str) and not value.strip()) else self.datetime_to_string(value,**kwargs)
        elif(dtype == 'string' or dtype == 'str'):
            return '' if(is_null) else value
        elif(dtype == 'bool' or dtype == 'boolean'):
            return None if(is_null) else None if(isinstance(value, str) and not value.strip()) else value
        elif(dtype == 'unknown'or dtype == 'object'):
            return None if(is_null) else None if(isinstance(value, str) and not value.strip()) else value
        return None if(is_null) else value

    # assign DataFrame column to corresponding types
    def assign_dataframe_column_types(self, df: pd.DataFrame, columns_dtype: Dict, default_dtype: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """
        Convert DataFrame columns to column types

        Parameters
        ----------
        df : DataFrame
            Table
        columns_dtype : dict
            Dictionary {"column name" : "type"}
        default_dtype : str, default None
            Default type to use: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        columns = df.columns
        for c in columns:
            if(c in columns_dtype):
                df[c] = self.column_to_dtype(df,c,columns_dtype[c],**kwargs)
            elif(default_dtype):
                df[c] = self.column_to_dtype(df,c,default_dtype,**kwargs)
        return df

    # get DataFrame data type name
    def convert_to_dtype_name( self, dtype: str, **kwargs) -> str:
        """
        Convert type name to DataFrame accepted type name

        Parameters
        ----------
        dtype : str
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        dtype = dtype.lower()
        if( dtype == 'numeric' or dtype == 'float64'):
            return 'float64'
        elif( dtype == 'time' or dtype == 'datetime64[ns]'):
            return 'datetime64[ns]'
        elif( dtype == 'string' ):
            return 'string'
        elif( dtype == 'boolean' or dtype == 'bool' ):
            return 'bool'
        elif( dtype == 'unknown' or dtype == 'object' ):
            return 'object'
        return 'object'

    # convert DataFrame column to bool
    def column_to_dtype( self, df: pd.DataFrame, column: str, dtype: str, **kwargs) -> pd.DataFrame:
        """
        Convert DataFrame column to specified type

        Parameters
        ----------
        df : DataFrame
            Table
        column: str
            Column name
        dtype : str
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        dtype = dtype.lower()
        if(dtype == 'numeric' or dtype == 'float64'):
            df[column] = self.column_to_numeric(df,column,**kwargs)
        elif(dtype == 'time' or dtype == 'datetime64[ns]'):
            df[column] = self.column_to_datetime(df,column,**kwargs)
        elif(dtype == 'string' or dtype == 'str'):
            df[column] = self.column_to_string(df,column,**kwargs)
        elif(dtype == 'bool' or dtype == 'boolean'):
            df[column] = self.column_to_bool(df,column,**kwargs)
        elif(dtype == 'unknown' or dtype == 'object'):
            df[column] = self.column_to_object(df,column,**kwargs)
        return df[column]
    
    # convert DataFrame column to 'object'
    def column_to_object( self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'object' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype('object')

    # convert DataFrame column to 'bool'
    def column_to_bool( self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'bool' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype('bool')

    # convert DataFrame column to 'string'
    def column_to_string( self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'string' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype('string')

    # convert DataFrame column to 'numeric'
    def column_to_numeric( self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'numeric' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        # return df[column].astype('float64')
        return pd.to_numeric(df[column])

    # convert DataFrame column to 'datetime'
    def column_to_datetime( self, df: pd.DataFrame, column, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'datetime' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        # return df[column].astype('datetime64[ns]')
        # return pd.to_datetime(df[column], infer_datetime_format=False)
        # return pd.to_datetime(df[column], infer_datetime_format=True)
        # return pd.to_datetime(df[column], format=format)
        # return pd.to_datetime(df[column])
        datetime_args = { arg: kwargs[arg] for arg in ['errors','dayfirst','yearfirst','utc','format','exact','unit','infer_datetime_format','origin','cache'] if(arg in kwargs)}
        if(datetime_args):
            return pd.to_datetime(df[column],**datetime_args)
        return pd.to_datetime(df[column])

    # convert datetime to string
    def datetime_to_string( self, d: Union[datetime,str], format: Optional[str] = '%Y-%m-%dT%H:%M:%S.%f', **kwargs) -> str:
        """
        Convert datetime object to string representation

        Parameters
        ----------
        d : datetime
            Date
        format : str, default '%Y-%m-%dT%H:%M:%S.%f'
            Time format
        """
        return '' if(pd.isnull(d)) else d.strftime(format) if(isinstance(d,datetime)) else str(d)
   
    # convert string to datetime
    def string_to_datetime( self, d: Union[datetime,str], format: Optional[str] = '%Y-%m-%d %H:%M:%S', **kwargs) -> datetime:
        """
        Convert date from string representation to datetime object

        Parameters
        ----------
        d : str
            Date
        format : str, default '%Y-%m-%dT%H:%M:%S.%f'
            Time format
        """
        return datetime.strptime(d,format)

    # get time or depth increment name
    def get_increment_enum( self, increment: Union[str,TimeIncrement,DepthIncrement], signal_type: Union[str,SignalType], **kwargs ) -> Union[TimeIncrement,DepthIncrement]:
        """
        Get TimeIncrement or DepthIncrement enum

        Parameters
        ----------
        increment : str, TimeIncrement, DepthIncrement
            Increment
        signal_type : str, SignalType
            Signal type
        """
        signal_type = self.get_signal_type_enum(signal_type,**kwargs)
        if( signal_type == SignalType.TimeDependent or signal_type == SignalType.StringTimeDependent ):
            return self.get_time_increment_enum(increment,**kwargs)
        elif( signal_type == SignalType.DepthDependent ):
            return self.get_depth_increment_enum(increment,**kwargs)
        return None

    # get time increment name
    def get_time_increment_enum( self, type: Union[str,TimeIncrement], **kwargs ) -> TimeIncrement:
        """
        Get TimeIncrement enum

        Parameters
        ----------
        type : str, TimeIncrement
            Increment
        """
        if( isinstance(type,TimeIncrement) ):
            return type
        # prepare name for comparison
        type = PetroVisorHelper.get_comparison_string(type, **kwargs)
        if( type in ['hourly','h','hr','hour','1h','1hr','1hour'] ):
            return TimeIncrement.Hourly
        elif( type in ['daily','d','day','1d','1day'] ):
            return TimeIncrement.Daily
        elif( type in ['monthly','m','month','1m','1month'] ):
            return TimeIncrement.Monthly
        elif( type in ['yearly','y','year','1y','1year'] ):
            return TimeIncrement.Yearly
        elif( type in ['quarterly','q','3m','3month','quarter'] ):
            return TimeIncrement.Quarterly
        elif( type in ['everyminute','min','minute','1min','1minute'] ):
            return TimeIncrement.EveryMinute
        elif( type in ['everysecond','s','sec','second','1s','1sec','1second'] ):
            return TimeIncrement.EverySecond
        elif( type in ['everyfiveminute','5min','5minutes'] ):
            return TimeIncrement.EveryFiveMinutes
        elif( type in ['everyfifteenminutes','15min','15minutes'] ):
            return TimeIncrement.EveryFifteenMinutes
        raise RuntimeError(f"PetroVisor::get_time_increment_enum(): Unknown time increment: '{type}'! Should be one of: {[inc.name for inc in TimeIncrement]}")

    # get depth increment name
    def get_depth_increment_enum( self, type: Union[str,DepthIncrement], **kwargs ) -> DepthIncrement:
        """
        Get DepthIncrement enum

        Parameters
        ----------
        type : str, DepthIncrement
            Increment
        """
        if( isinstance(type,DepthIncrement) ):
            return type
        # prepare name for comparison
        type = PetroVisorHelper.get_comparison_string(type, **kwargs)
        if( type in ['meter','m','1meter','1m'] ):
            return DepthIncrement.Meter
        elif( type in ['halfmeter','halfm','.5meter','.5m','0.5meter','0.5m'] ):
            return DepthIncrement.HalfMeter
        elif( type in ['tenthmeter','.1meter','.1m','0.1meter','0.1m'] ):
            return DepthIncrement.TenthMeter
        elif( type in ['eightmeter','.125meter','.125m','0.125meter','0.125m'] ):
            return DepthIncrement.EighthMeter
        elif( type in ['foot','ft','1foot','1ft'] ):
            return DepthIncrement.Foot
        elif( type in ['halffoot','halfft','.5foot','.5feet','.5ft','0.5foot','0.5feet','0.5ft'] ):
            return DepthIncrement.HalfFoot
        raise RuntimeError(f"PetroVisor::get_depth_increment_enum(): Unknown depth increment: '{type}'! Should be one of: {[inc.name for inc in DepthIncrement]}")

    # get valid signal type name
    def get_signal_type_enum( self, type: Union[str,SignalType], **kwargs ) -> SignalType:
        """
        Get SignalType enum

        Parameters
        ----------
        type : str, SignalType
            Signal type
        """
        if( isinstance(type,SignalType) ):
            return type
        # prepare name for comparison
        type = PetroVisorHelper.get_comparison_string(type, **kwargs)
        if( type in ['static','staticnumeric']):
            return SignalType.Static
        elif( type in ['time','timenumeric','timedependent']):
            return SignalType.TimeDependent
        elif( type in ['depth','depthnumeric','depthdependent']):
            return SignalType.DepthDependent
        elif( type in ['string','staticstring']):
            return SignalType.String
        elif( type in ['stringtime','timestring','stringtimedependent']):
            return SignalType.StringTimeDependent
        elif( type in ['pvt','pvtnumeric'] ):
            return SignalType.PVT
        raise RuntimeError(f"PetroVisor::get_signal_type_name(): Unknown data type: '{type}'! Should be one of: {[t.name for t in SignalType]}")

    # get signal type route
    def get_signal_type_route( self, type: Union[str,SignalType], **kwargs ) -> str:
        """
        Get route of corresponsing signal type

        Parameters
        ----------
        type : str, SignalType
            Signal type
        """
        if( isinstance(type,str) ):
            type = self.get_signal_type_enum( type, **kwargs )
        elif( not isinstance(type,SignalType) ):
            raise RuntimeError(f"PetroVisor::get_data_type_route(): 'signal_type' should be either one of {[t.name for t in SignalType]} or {SignalType.__name__} enum.")
        if( type == SignalType.Static ):
            return 'Data/Static'
        elif( type == SignalType.DepthDependent ):
            return 'Data/Depth'
        elif( type == SignalType.TimeDependent ):
            return 'Data/Time'
        elif( type == SignalType.String ):
            return 'Data/String'
        elif( type == SignalType.StringTimeDependent ):
            return 'Data/StringTime'
        elif( type == SignalType.PVT ):
            return 'Data/PVT'
        raise RuntimeError(f"PetroVisor::get_signal_type_route(): '{type}' is not supported yet.")

    # get signal data type name
    def get_signal_data_type_name( self, type: Union[str,SignalType], **kwargs ) -> str:
        """
        Get data type name for corresponsing signal type

        Parameters
        ----------
        type : str, SignalType
            Signal type
        """
        if( isinstance(type,str) ):
            type = self.get_signal_type_enum( type, **kwargs )
        elif( not isinstance(type,SignalType) ):
            raise RuntimeError(f"PetroVisor::get_signal_data_type_name(): 'signal_type' should be either one of {[t.name for t in SignalType]} or {SignalType.__name__} enum.")
        if( type == SignalType.Static ):
            return 'numeric'
        elif( type == SignalType.DepthDependent ):
            return 'numeric'
        elif( type == SignalType.TimeDependent ):
            return 'numeric'
        elif( type == SignalType.String ):
            return 'string'
        elif( type == SignalType.StringTimeDependent ):
            return 'string'
        elif( type == SignalType.PVT ):
            return 'numeric'
        raise RuntimeError(f"PetroVisor::get_signal_data_type_name(): '{type}' is not supported yet.")

    # get signal range name
    def get_signal_range_type_name( self, type: Union[str,SignalType], **kwargs ) -> str:
        """
        Get data range type name for corresponsing signal type

        Parameters
        ----------
        type : str, SignalType
            Signal type
        """
        if( isinstance(type,str) ):
            type = self.get_signal_type_enum( type, **kwargs )
        elif( not isinstance(type,SignalType) ):
            raise RuntimeError(f"PetroVisor::get_signal_range_type_name(): 'signal_type' should be either one of {[t.name for t in SignalType]} or {SignalType.__name__} enum.")
        if( type == SignalType.Static ):
            return ''
        elif( type == SignalType.DepthDependent ):
            return 'numeric'
        elif( type == SignalType.TimeDependent ):
            return 'time'
        elif( type == SignalType.String ):
            return ''
        elif( type == SignalType.StringTimeDependent ):
            return 'time'
        elif( type == SignalType.PVT ):
            return ''
        raise RuntimeError(f"PetroVisor::get_signal_range_type_name(): '{type}' is not supported yet.")

    # get ML Model Type enum 
    def get_ml_model_type_enum(self, type: Union[str,MLModelType], **kwargs ) -> str:
        """
        Get ML Model Type

        Parameters
        ----------
        type : str, MLModelType
            ML Model type
        """
        if( isinstance(type,MLModelType) ):
            return type
        # prepare name for comparison
        type = PetroVisorHelper.get_comparison_string(type, **kwargs)
        if( type in ['regression', 'reg']):
            return MLModelType.Regression
        elif( type in ['binaryclassification','binaryclass','binclass','bin']):
            return MLModelType.BinaryClassification
        elif( type in ['multipleclassification','multiclassification','multipleclass','multiclass','multiple','multi']):
            return MLModelType.MultipleClassification
        elif( type in ['clustering','cluster']):
            return MLModelType.Clustering
        elif( type in ['naivebayes','bayes']):
            return MLModelType.NaiveBayes
        elif( type in ['naivebayescategorical','bayescategorical']):
            return MLModelType.NaiveBayesCategorical
        raise RuntimeError(f"PetroVisor::get_ml_model_enum(): Unknown data type: '{type}'! Should be one of: {[t.name for t in MLModelType]}")

    # get ML Normalization Type enum
    def get_ml_normalization_type_enum(self, type: Union[str,MLNormalizationType], **kwargs ) -> str:
        """
        Get ML Normalization Type

        Parameters
        ----------
        type : str, MLNormalizationType
            ML Normalization type
        """
        if( isinstance(type,MLNormalizationType) ):
            return type
        # prepare name for comparison
        type = PetroVisorHelper.get_comparison_string(type, **kwargs)
        if( type in ['auto', 'automatic']):
            return MLNormalizationType.Auto
        elif( type in ['minmax']):
            return MLNormalizationType.MinMax
        elif( type in ['meanvariance','meanvar']):
            return MLNormalizationType.MeanVariance
        elif( type in ['logmeanvariance','logmeanvar']):
            return MLNormalizationType.LogMeanVariance
        elif( type in ['binning','bin']):
            return MLNormalizationType.Binning
        elif( type in ['supervisedbinning','supervisedbin','superbin']):
            return MLNormalizationType.SupervisedBinning
        elif( type in ['robustscaling','robust']):
            return MLNormalizationType.RobustScaling
        elif( type in ['lpnorm','lp']):
            return MLNormalizationType.LpNorm
        elif( type in ['globalcontrast','contrast']):
            return MLNormalizationType.GlobalContrast
        raise RuntimeError(f"PetroVisor::get_ml_normalization_enum(): Unknown data type: '{type}'! Should be one of: {[t.name for t in MLNormalizationType]}")

    # get 'NamedItem' route
    def get_item_route( self, data_type: str, **kwargs ) -> str:
        """
        Get route for corresponding NamedItem type

        Parameters
        ----------
        data_type : str
            Item type
        """
        return PetroVisorHelper.get_dict_value( self.ItemRoutes, data_type, **kwargs)

    # get 'PetroVisorItems' route
    def get_petrovisor_item_route( self, data_type: str, **kwargs ) -> str:
        """
        Get route for corresponding PetroVisorItem type

        Parameters
        ----------
        data_type : str
            Item type
        """
        return PetroVisorHelper.get_dict_value( self.PetroVisorItemRoutes, data_type, **kwargs)

    # get 'InfoItems' route
    def get_info_item_route( self, data_type: str, **kwargs ) -> str:
        """
        Get route for corresponding InfoItem type

        Parameters
        ----------
        data_type : str
            Item type
        """
        return PetroVisorHelper.get_dict_value( self.InfoItemRoutes, data_type, **kwargs)

    # is 'NamedItem'
    def is_named_item( self, data_type: str, **kwargs ) -> str:
        """
        Check whether provided item is NamedItem

        Parameters
        ----------
        data_type : str
            Item type
        """
        return PetroVisorHelper.contains( self.ItemRoutes, data_type, **kwargs)

    # is 'PetroVisorItem'
    def is_petrovisor_item( self, data_type: str, **kwargs ) -> str:
        """
        Check whether provided item is PetroVisorItem

        Parameters
        ----------
        data_type : str
            Item type
        """
        return PetroVisorHelper.contains( self.PetroVisorItemRoutes, data_type, **kwargs)

    # is 'InfoItem'
    def is_info_item( self, data_type: str, **kwargs ) -> str:
        """
        Check whether provided item is InfoItem

        Parameters
        ----------
        data_type : str
            Item type
        """
        return PetroVisorHelper.contains( self.InfoItemRoutes, data_type, **kwargs)

    # get 'Entity' column name
    def get_entity_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Entity' column name used in return tables from api calls
        """
        return 'Entity'
    
    # get 'Alias' column name
    def get_alias_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Alias' column name used in return tables from api calls
        """
        return 'Alias'

    # get 'EntityType' column name
    def get_entity_type_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Type' column name used in return tables from api calls
        """
        return 'Type'

    # get 'Opportunity' column name
    def get_opportunity_column_name(self, **kwargs) -> str:
        """
        Get predefined 'IsOpportunity' column name used in return tables from api calls
        """
        return 'IsOpportunity'

    # get 'Date' column name
    def get_date_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Date' column name used in return tables from api calls
        """
        return 'Date'

    # get 'Time' column name
    def get_time_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Time' column name used in return tables from api calls
        """
        return 'Time'

    # get 'Depth' column name
    def get_depth_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Depth' column name used in return tables from api calls
        """
        return 'Depth'

    # update dictionary
    def update_dict( self, d: Dict, **kwargs ) -> Dict:
        """
        Update dictionary fields with keyword argument values

        Parameters
        ----------
        d : dict
            Dictionary
        """
        return PetroVisorHelper.update_dict(d,**kwargs)

    # remove dictionary fields
    def remove_from_dict( self, d: Dict ,keys : Union[str,List[str]], **kwargs):
        """
        Remove dictionary fields

        Parameters
        ----------
        d : dict
            Dictionary
        """
        return PetroVisorHelper.remove_from_dict(d,keys,**kwargs)

    # reset token
    def __reset_token( self, **kwargs ) -> Any:
        """
        Reset token
        """
        access_response = PetroVisorLogin.get_access_token(key = self.Key, discovery_url = self.DiscoveryUrl, **kwargs)
        self.__access_token = access_response['access_token'] if('access_token' in access_response) else ''


# PetroVisor Helper calss
class PetroVisorHelper:
    """
    PetroVisor helper class
    """

    # get default discovery urls
    @staticmethod
    def get_discovery_urls() -> List[str]:
        """
        Get known dicovery url's
        """
        return [
            r'https://identity-latest.eu1.petrovisor.com',
            r'https://identity.eu1.petrovisor.com',
            r'https://identity-latest.us1.petrovisor.com',
            r'https://identity.us1.petrovisor.com']

    # get item types
    @staticmethod
    def get_item_types() -> List:
        """
        Get all item types
        """
        return list(PetroVisorHelper.get_item_routes().keys())

    # get item routes
    @staticmethod
    def get_item_routes() -> Dict:
        """
        Get all item routes
        """
        return dict(**PetroVisorHelper.get_named_item_routes(),**PetroVisorHelper.get_petrovisor_item_routes())

    # get 'NamedItem' routes
    @staticmethod
    def get_named_item_routes() -> Dict:
        """
        Get routes of NamedItems
        """
        return {
            'Unit': 'Units',
            'UnitMeasurement': 'UnitMeasurements',
            'Entity': 'Entities',
            'EntityType': 'EntityTypes',
            'Signal': 'Signals',
            'ConfigurationSettingValue': 'ConfigurationSettings',
            'ConfigurationSettings': 'ConfigurationSettings',
            'Tag': 'Tags',
            'ProcessTemplate': 'ProcessTemplates',
            'MessageEntry': 'MessageEntries',
            'Ticket': 'Tickets',
            'UserSetting': 'UserSettings',
            'CustomWorkflowActivity': 'CustomWorkflowActivities',
            'WebWorkflowActivity': 'WebWorkflowActivities',
            'EventSubscription': 'EventSubscriptions',
            'WorkspacePackage': 'WorkspacePackages',
        }


    # get 'PetroVisorItem' routes
    @staticmethod
    def get_petrovisor_item_routes() -> Dict:
        """
        Get routes of PetroVisorItems
        """
        return dict(**{
            'Hierarchy': 'Hierarchies',
            'Scope': 'Scopes',
            'EntitySet': 'EntitySets',
            'Context': 'Contexts',
            'TableCalculation': 'TableCalculations',
            'EventCalculation': 'EventCalculations',
            'CleansingCalculation': 'CleansingCalculations',
            'Plot': 'Plots',
            'PSharpScript': 'PSharpScripts',
            'CleansingScript': 'CleansingScripts',
            'WorkflowSchedule': 'WorkflowSchedules',
            'RWorkflowActivity': 'RWorkflowActivities',
            'Workflow': 'Workflows',
            'FilterDefinition': 'Filters',
            'Filter': 'Filters',
            'DCA': 'DCA',
            'ChartDefinition': 'Charts',
            'Chart': 'Charts',
            'VoronoiGrid': 'VoronoiGrids',
            'GeoDataGrid': 'GeoDataGrids',
            'Polygon': 'Polygons',
            'PivotTableDefinition': 'PivotTables',
            'PivotTable': 'PivotTables',
            'DataIntegrationSet': 'DataIntegrationSets',
            'ReferenceTableDefinition': 'ReferenceTables',
            'ReferenceTable': 'ReferenceTables',
            'PowerBIItem': 'PowerBIItems',
        },**PetroVisorHelper.get_info_item_routes())

    # get 'PetroVisorItem' routes
    @staticmethod
    def get_info_item_routes() -> Dict:
        """
        Get routes of InfoItems
        """
        return {
            'MachineLearningModel': 'MLModels',
            'MLModel': 'MLModels',
            'DataGrid': 'DataGrids',
            'DataGridSet': 'DataGridSets',
            'DataConnection': 'DataConnections',
            'DataSource': 'DataSources',
            'Scenario': 'Scenarios',
            'DataIntegrationSession': 'DataIntegrationSessions',
        }

    # get object name
    @staticmethod
    def get_object_name( obj: Any, **kwargs ) -> str:
        """
        Get object name

        Parameters
        ----------
        obj : Any
            Object
        """
        if(isinstance(obj,str)):
            return obj
        elif(PetroVisorHelper.has_field(obj,'Name')):
            return obj['Name']
        return str(obj)

    # update dictionary
    @staticmethod
    def update_dict( d: Dict, **kwargs ) -> Dict:
        """
        Update dictionary fields with keyword argument values

        Parameters
        ----------
        d : dict
            Dictionary
        """
        if(kwargs):
            updated_dict = {}
            for k,v in d.items():
                val = PetroVisorHelper.get_dict_value(kwargs,k)
                updated_dict[k] = val if(val is not None) else v
            return updated_dict
        return d

    # remove dictionary fields
    @staticmethod
    def remove_from_dict( d: Dict ,keys : Union[str,List[str]], **kwargs):
        """
        Remove dictionary fields

        Parameters
        ----------
        d : dict
            Dictionary
        """
        if(not isinstance(keys,list)):
            keys = [keys]
        return { k: v for k,v in d.items() if k not in keys}

    # check if object has field/attribute
    @staticmethod
    def has_field( obj: Any, field: str, **kwargs):
        """
        Check whether object/dict has provided field/attribute

        Parameters
        ----------
        obj : Any
            Object
        field : str
            Field name
        """
        return hasattr(obj,field) or (isinstance(obj,dict) and field in obj)

    # get non-empty fileds
    @staticmethod
    def get_non_empty_fields( d: Dict ) -> Dict:
        """
        Get non-empty(is not None) fields of dictionary

        Parameters
        ----------
        d : dict
            Dictionoary
        """
        return {k: v for k,v in d.items() if(v is not None)}

    # get comparison string
    @staticmethod
    def get_comparison_string( s: str, ignore_characters: List[str] = [' ', '_', '-', '.', ','], ignore_case: bool = True, strip: bool = True, **kwargs ):
        """
        Get string preprocessed for compasion

        Parameters
        ----------
        s : str
            String
        ignore_characters : list, default [' ', '_', '-', '.', ',']
            Characters to ignore
        ignore_case: bool, default True
            Ignore case
        strip : bool, default True
            Strip/Trim string
        """
        if(ignore_characters):
            for c in ignore_characters:
                s = s.replace(c,'')
        if(ignore_case):
            s = s.lower()
        return s.strip() if(strip) else s

    # get dictionary value
    @staticmethod
    def get_dict_value( d: Dict, key: Union[str,Any], ignore_characters: List[str] = [' ', '_', '-', '.', ','], ignore_case: bool = True, strip: bool = True, **kwargs ) -> str:
        """
        Get dictionary value

        Parameters
        ----------
        s : str
            String
        ignore_characters : list, default [' ', '_', '-', '.', ',']
            Characters to ignore
        ignore_case: bool, default True
            Ignore case
        strip : bool, default True
            Strip/Trim string
        """
        if(d):
            if(not isinstance(key,str)):
                key = str(key)
            if( key in d ):
                return d[key]
            else:
                key_to_compare = PetroVisorHelper.get_comparison_string(key, ignore_characters = ignore_characters, ignore_case = ignore_case, strip = strip, **kwargs )
                for k,v in d.items():
                    k_to_compare = PetroVisorHelper.get_comparison_string(k, ignore_characters = ignore_characters, ignore_case = ignore_case, strip = strip, **kwargs )
                    if( k_to_compare == key_to_compare ):
                        return v
        return None

    # check whether dict/list contains key
    @staticmethod
    def contains( d: Union[Dict,List], key: Union[str,Any], ignore_characters: List[str] = [' ', '_', '-', '.', ','], ignore_case: bool = True, strip: bool = True, **kwargs ) -> bool:
        """
        Check whether dictionary contains field/key

        Parameters
        ----------
        s : str
            String
        ignore_characters : list, default [' ', '_', '-', '.', ',']
            Characters to ignore
        ignore_case: bool, default True
            Ignore case
        strip : bool, default True
            Strip/Trim string
        """
        if(not isinstance(key,str)):
            key = str(key)
        if( key in d ):
            return True
        else:
            key_to_compare = PetroVisorHelper.get_comparison_string(key, ignore_characters = ignore_characters, ignore_case = ignore_case, strip = strip, **kwargs )
            for k in d:
                k_to_compare = PetroVisorHelper.get_comparison_string(k, ignore_characters = ignore_characters, ignore_case = ignore_case, strip = strip, **kwargs )
                if( k_to_compare == key_to_compare ):
                    return True
        return False

    # is integer
    @staticmethod
    def is_int( value: Any, **kwargs) -> bool:
        """
        Is integer value

        Parameters
        ----------
        value : Any
            Value
        """
        try:
            val = int(value)
        except:
            return False
        return True

    # is float
    @staticmethod
    def is_float( value: Any, **kwargs) -> bool:
        """
        Is float value

        Parameters
        ----------
        value : Any
            Value
        """
        try:
            val = float(value)
        except:
            return False
        return True
   
    # get uuid
    @staticmethod
    def get_uuid( value: Any, **kwargs) -> bool:
        """
        Get UUID value

        Parameters
        ----------
        value : Any
            Value
        """
        return UUID(value) if(PetroVisorHelper.is_uuid(value)) else UUID(value['Id'])

    # is uuid
    @staticmethod
    def is_uuid( value: Any, **kwargs) -> bool:
        """
        Is UUID value

        Parameters
        ----------
        value : Any
            Value
        """
        try:
            val = UUID(value)
        except:
            return False
        return True

    # is iterable
    @staticmethod
    def is_iterable( x: Any, **kwargs) -> bool:
        """
        Is iterable object

        Parameters
        ----------
        x : Any
            Object
        """
        if(hasattr(x, '__len__')):
            return True
        return False


    # is empty
    @staticmethod
    def is_empty( x: Any, **kwargs) -> bool:
        """
        Is empty object

        Parameters
        ----------
        x : Any
            Object
        """
        if(isinstance(x,np.ndarray)):
            return False if(x.size) else True
        elif(isinstance(x,(pd.DataFrame,pd.Series))):
            return True if(x.empty) else False
        return False if(x) else True


    # get number of rows
    @staticmethod
    def get_num_rows( x: Any, **kwargs) -> bool:
        """
        Get number of rows

        Parameters
        ----------
        x : Any
            Object
        """
        if(isinstance(x,(np.ndarray,pd.DataFrame,pd.Series))):
            return x.shape[0]
        elif(hasattr(x, '__len__')):
            return len(x)
        return None

    # get number of columns
    @staticmethod
    def get_num_cols( x: Any, **kwargs) -> bool:
        """
        Get number of columns

        Parameters
        ----------
        x : Any
            Object
        """
        if(isinstance(x,pd.Series)):
            return 0
        elif(isinstance(x,(np.ndarray,pd.DataFrame))):
            return x.shape[1] if(len(x.shape) > 1) else 0
        elif(isinstance(x,list)):
            cols_set = set()
            for row in x:
                cols_set.add(len(row) if(PetroVisorHelper.is_iterable(row)) else -1)
            if(len(cols_set)==1):
                num_cols = cols_set.pop()
                return None if(num_cols==0) else 0 if(num_cols==-1) else num_cols
            return None
        return None

    # convert object to list
    # TODO: add support for other containers
    @staticmethod
    def to_list( x: Any, **kwargs) -> bool:
        """
        Convert object to list

        Parameters
        ----------
        x : Any
            Object
        """
        if(isinstance(x,list)):
            return x
        elif(isinstance(x,(pd.DataFrame,pd.Series))):
            return x.values.tolist()
        elif(isinstance(x,np.ndarray)):
            return x.tolist()
        elif(isinstance(x,(set))):
            return list(x)
        elif(isinstance(x,(dict))):
            return list(x.items())
        return [x]

    @staticmethod
    def get_file_extension(path: str, **kwargs) -> str:
        """
        Convert object to list

        Parameters
        ----------
        apth : str
            File path
        """
        _, file_extension = os.path.splitext(path)
        return file_extension

