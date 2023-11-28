from typing import (
    Any,
    Optional,
)
import json

import requests
from urllib.parse import quote


# requests functionality
class ApiRequests:
    """
    ApiRequest performs REST API calls
    """

    def __init__(self):
        pass

    # 'GET' request
    @staticmethod
    def get(api: str,
            rqst: str,
            workspace: str = '',
            data: Optional[Any] = None,
            query: Optional[Any] = None,
            files: Optional[Any] = None,
            token: str = '',
            route: str = 'PetroVisor/API/',
            format: str = 'json',
            **kwargs) -> Any:
        """
        Get request

        Parameters
        ----------
        api : str
            Api endpoint
        rqst : str
            Request
        workspace : str
            Workspace name
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        token : str, default None
            Token
        route : str, default 'PetroVisor/API/'
            Route
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        """
        return ApiRequests.get_response('GET', api, rqst, workspace=workspace, data=data, query=query,
                                        files=files, token=token, route=route, format=format, **kwargs)

    # 'POST' request
    @staticmethod
    def post(api: str,
             rqst: str,
             workspace: str = '',
             data: Optional[Any] = None,
             query: Optional[Any] = None,
             files: Optional[Any] = None,
             token: str = '',
             route: str = 'PetroVisor/API/',
             format: str = 'json',
             **kwargs) -> Any:
        """
        Post request

        Parameters
        ----------
        api : str
            Api endpoint
        rqst : str
            Request
        workspace : str
            Workspace name
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        token : str, default None
            Token
        route : str, default 'PetroVisor/API/'
            Route
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        """
        return ApiRequests.get_response('POST', api, rqst, workspace=workspace, data=data, query=query,
                                        files=files, token=token, route=route, format=format, **kwargs)

    # 'PUT' request
    @staticmethod
    def put(api: str,
            rqst: str,
            workspace: str = '',
            data: Optional[Any] = None,
            query: Optional[Any] = None,
            files: Optional[Any] = None,
            token: str = '',
            route: str = 'PetroVisor/API/',
            format: str = 'json',
            **kwargs) -> Any:
        """
        Put request

        Parameters
        ----------
        api : str
            Api endpoint
        rqst : str
            Request
        workspace : str
            Workspace name
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        token : str, default None
            Token
        route : str, default 'PetroVisor/API/'
            Route
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        """
        return ApiRequests.get_response('PUT', api, rqst, workspace=workspace, data=data, query=query,
                                        files=files, token=token, route=route, format=format, **kwargs)

    # 'DELETE' request
    @staticmethod
    def delete(api: str,
               rqst: str,
               workspace: str = '',
               data: Optional[Any] = None,
               query: Optional[Any] = None,
               files: Optional[Any] = None,
               token: str = '',
               route: str = 'PetroVisor/API/',
               format: str = 'json',
               **kwargs) -> Any:
        """
        Delete request

        Parameters
        ----------
        api : str
            Api endpoint
        rqst : str
            Request
        workspace : str
            Workspace name
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        token : str, default None
            Token
        route : str, default 'PetroVisor/API/'
            Route
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        """
        return ApiRequests.get_response('DELETE', api, rqst, workspace=workspace, data=data, query=query,
                                        files=files, token=token, route=route, format=format, **kwargs)

    # get REST API response
    @staticmethod
    def get_response(method: str,
                     api: str,
                     rqst: str,
                     workspace: str = '',
                     data: Optional[Any] = None,
                     query: Optional[Any] = None,
                     files: Optional[Any] = None,
                     token: str = '',
                     route: str = 'PetroVisor/API/',
                     format: str = 'json',
                     retry_on_unauthorized: bool = True,
                     verbose: bool = False,
                     **kwargs) -> Any:
        """
        Get response from request

        Parameters
        ----------
        method : str
            'GET', 'PUT', 'POST', 'DELETE'
        api : str
            Api endpoint
        rqst : str
            Request
        workspace : str
            Workspace name
        data : Any
            Data
        query : Any
            Query string object. Can be dictionary or str
        files : file-like objects
            File objects
        token : str, default None
            Token
        route : str, default 'PetroVisor/API/'
            Route
        format : str, default 'json'
            Response format: 'json', 'text', 'content', 'raw', 'bytes', 'binary'
        retry_on_unauthorized : bool, default True
            Retry if request was unauthorized(401)
        verbose : bool, default False
            Print mode
        """
        request_headers = {
            'accept': 'application/json',
        }
        # add access token to headers
        if token:
            request_headers['authorization'] = f'Bearer {token}'
        # content type to headers
        if data or isinstance(data, dict):
            request_headers['content-type'] = 'application/json'
            if not data:
                data = json.dumps(data)
        # elif(files):
        #     request_headers['content-type'] = 'multipart/form-data'
        # add workspace
        if workspace:
            rqst = workspace + '/' + rqst
        if query:
            if isinstance(query, str):
                rqst = rqst + '?' + query
            elif isinstance(query, list):
                rqst = rqst + '?' + '&'.join([f'{v}' for v in query])
            # generalized dictionary
            elif callable(getattr(query, 'items', None)):
                rqst = rqst + '?' + '&'.join([f'{k}={v}' for k, v in query.items()])
        # get request url
        request_url = ApiRequests.get_request_url(route, api, rqst, verbose=verbose)

        # method name
        method_name = method.upper().strip()
        # get response
        timeout = 59 * 60  # time out limit in seconds (3540)
        response = None
        try:
            if data and not isinstance(data, str):
                data = json.dumps(data)
            # GET: read resource
            # The GET method requests a representation of the specified resource.
            # Requests using GET should only retrieve data.
            if method_name == 'GET':
                response = requests.get(request_url,
                                        headers=request_headers, data=data, files=files, timeout=timeout)
            # POST: create resource
            # The POST method submits an entity to the specified resource,
            # often causing a change in state or side effects on the server.
            elif method_name == 'POST':
                response = requests.post(request_url,
                                         headers=request_headers, data=data, files=files, timeout=timeout)
            # PUT: update resource
            # The PUT method replaces all current representations of the target resource with the request payload.
            elif method_name == 'PUT':
                response = requests.put(request_url,
                                        headers=request_headers, data=data, files=files, timeout=timeout)
            # DELETE: delete resource
            # The DELETE method deletes the specified resource.
            elif method_name == 'DELETE':
                response = requests.delete(request_url,
                                           headers=request_headers, data=data, files=files, timeout=timeout)
            # PATCH: modify resource
            # The PATCH method applies partial modifications to a resource.
            elif method_name == 'PATCH':
                response = requests.patch(request_url,
                                          headers=request_headers, data=data, files=files, timeout=timeout)
            # HEAD: read resource, response without body
            # The HEAD method asks for a response identical to a GET request, but without the response body.
            elif method_name == 'HEAD':
                response = requests.head(request_url,
                                         headers=request_headers, data=data, files=files, timeout=timeout)
            # OPTIONS: specify communication options
            # The OPTIONS method describes the communication options for the target resource.
            elif method_name == 'OPTIONS':
                response = requests.options(request_url,
                                            headers=request_headers, data=data, files=files, timeout=timeout)
            # CONNECT:
            # The CONNECT method establishes a tunnel to the server identified by the target resource.
            elif method_name == 'CONNECT':
                pass
            # TRACE:
            # The TRACE method performs a message loop-back test along the path to the target resource.
            elif method_name == 'TRACE':
                pass
            # raise exception if error occurred
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            # check if unauthorized request (401)
            if retry_on_unauthorized and response.status_code == requests.codes.unauthorized:
                return response
            raise requests.exceptions.HTTPError(err)
            # response = None
        if response is not None:
            try:
                if format in ('json',):
                    return response.json()
                elif format in ('bytes', 'binary', 'content'):
                    return response.content
                elif format in ('text',):
                    return response.text
                elif format in ('raw',):
                    return response.raw
                elif not format:
                    return response
                return response.content
            except:
                return response
        return None

    # get request url
    @staticmethod
    def get_request_url(route: str, api: str, rqst: str, encode: bool = True, verbose: bool = False) -> str:
        """
        Get request url

        Parameters
        ----------
        route : str, default 'PetroVisor/API/'
            Route
        api : str
            Api endpoint
        rqst : str
            Request
        encode : bool, default True
            Encode request
        verbose : bool, default False
            Print mode
        """
        # get web api service url
        web_api_service_url = api
        if not web_api_service_url.endswith('/'):
            web_api_service_url += '/'
        # add request
        request_url = route
        request_url += rqst.strip()
        # encode request
        if encode:
            request_url = ApiRequests.encode_request(request_url)
        # show url
        if verbose:
            print(f'\nRequest: {web_api_service_url + request_url}')
        return web_api_service_url + request_url

    # encode request
    @staticmethod
    def encode_request(request: str) -> str:
        """
        Encode request

        Parameters
        ----------
        request : str
            Request
        """
        encoded_req = quote(request)
        encoded_req = encoded_req.replace('#', '%23').replace('$', '%24').replace('^', '%5E')
        return encoded_req
