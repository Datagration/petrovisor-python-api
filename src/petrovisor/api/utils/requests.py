import time
from typing import (
    Any,
    Optional,
    Union,
)
import json
import requests
from requests import Response
from requests.utils import requote_uri
from urllib.parse import quote
import warnings


# requests functionality
class ApiRequests:
    """
    ApiRequest performs REST API calls
    """

    def __init__(self):
        pass

    # 'GET' request
    @staticmethod
    def get(
        api: str,
        rqst: str,
        workspace: str = "",
        data: Optional[Any] = None,
        query: Optional[Any] = None,
        files: Optional[Any] = None,
        token: str = "",
        route: str = "PetroVisor/API/",
        format: str = "json",
        **kwargs,
    ) -> Any:
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
        return ApiRequests.get_response(
            "GET",
            api,
            rqst,
            workspace=workspace,
            data=data,
            query=query,
            files=files,
            token=token,
            route=route,
            format=format,
            **kwargs,
        )

    # 'POST' request
    @staticmethod
    def post(
        api: str,
        rqst: str,
        workspace: str = "",
        data: Optional[Any] = None,
        query: Optional[Any] = None,
        files: Optional[Any] = None,
        token: str = "",
        route: str = "PetroVisor/API/",
        format: str = "json",
        **kwargs,
    ) -> Any:
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
        return ApiRequests.get_response(
            "POST",
            api,
            rqst,
            workspace=workspace,
            data=data,
            query=query,
            files=files,
            token=token,
            route=route,
            format=format,
            **kwargs,
        )

    # 'PUT' request
    @staticmethod
    def put(
        api: str,
        rqst: str,
        workspace: str = "",
        data: Optional[Any] = None,
        query: Optional[Any] = None,
        files: Optional[Any] = None,
        token: str = "",
        route: str = "PetroVisor/API/",
        format: str = "json",
        **kwargs,
    ) -> Any:
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
        return ApiRequests.get_response(
            "PUT",
            api,
            rqst,
            workspace=workspace,
            data=data,
            query=query,
            files=files,
            token=token,
            route=route,
            format=format,
            **kwargs,
        )

    # 'DELETE' request
    @staticmethod
    def delete(
        api: str,
        rqst: str,
        workspace: str = "",
        data: Optional[Any] = None,
        query: Optional[Any] = None,
        files: Optional[Any] = None,
        token: str = "",
        route: str = "PetroVisor/API/",
        format: str = "json",
        **kwargs,
    ) -> Any:
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
        return ApiRequests.get_response(
            "DELETE",
            api,
            rqst,
            workspace=workspace,
            data=data,
            query=query,
            files=files,
            token=token,
            route=route,
            format=format,
            **kwargs,
        )

    # get REST API response
    @staticmethod
    def get_response(
        method: str,
        api: str,
        rqst: str,
        workspace: str = "",
        data: Optional[Any] = None,
        query: Optional[Any] = None,
        files: Optional[Any] = None,
        token: str = "",
        route: str = "PetroVisor/API/",
        format: str = "json",
        retry_on_unauthorized: bool = True,
        errors: str = "coerce",
        **kwargs,
    ) -> Any:
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
        errors : str, default 'coerce'
            If ‘raise’, then invalid request will raise an exception.
            If ‘coerce’, then invalid request will issue a warning and return None.
            If ‘ignore’, then invalid request will return the response.
        """
        request_headers = {
            "accept": "application/json",
        }
        # add access token to headers
        if token:
            request_headers["authorization"] = f"Bearer {token}"
        # content type to headers
        if data or isinstance(data, dict):
            request_headers["content-type"] = "application/json"
            if not data:
                data = json.dumps(data)
        # elif(files):
        #     request_headers['content-type'] = 'multipart/form-data'
        # add workspace
        if workspace:
            rqst = workspace + "/" + rqst
        if query:
            if isinstance(query, str):
                rqst = rqst + "?" + query
            elif isinstance(query, list):
                rqst = rqst + "?" + "&".join([f"{v}" for v in query])
            # generalized dictionary
            elif callable(getattr(query, "items", None)):
                rqst = (
                    rqst
                    + "?"
                    + "&".join(
                        [f"{k}={ApiRequests.encode(v)}" for k, v in query.items()]
                    )
                )
        # get request url
        request_url = ApiRequests.get_request_url(route, api, rqst)

        # method name
        method_name = method.upper().strip()

        # convert data to json string
        if data and not isinstance(data, str):
            data = json.dumps(data)

        # request secs
        timeout = None  # no timeout
        max_retries = (
            1  # increased to 3 times in case of 400 Bad Request or 4004 Not Found
        )
        waiting_time = 5  # in seconds

        # get response
        response = None
        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                # GET: read resource
                # The GET method requests a representation of the specified resource.
                # Requests using GET should only retrieve data.
                if method_name == "GET":
                    response = requests.get(
                        request_url,
                        headers=request_headers,
                        data=data,
                        files=files,
                        timeout=timeout,
                    )
                # POST: create resource
                # The POST method submits an entity to the specified resource,
                # often causing a change in state or side effects on the server.
                elif method_name == "POST":
                    response = requests.post(
                        request_url,
                        headers=request_headers,
                        data=data,
                        files=files,
                        timeout=timeout,
                    )
                # PUT: update resource
                # The PUT method replaces all current representations of the target resource with the request payload.
                elif method_name == "PUT":
                    response = requests.put(
                        request_url,
                        headers=request_headers,
                        data=data,
                        files=files,
                        timeout=timeout,
                    )
                # DELETE: delete resource
                # The DELETE method deletes the specified resource.
                elif method_name == "DELETE":
                    response = requests.delete(
                        request_url,
                        headers=request_headers,
                        data=data,
                        files=files,
                        timeout=timeout,
                    )
                # PATCH: modify resource
                # The PATCH method applies partial modifications to a resource.
                elif method_name == "PATCH":
                    response = requests.patch(
                        request_url,
                        headers=request_headers,
                        data=data,
                        files=files,
                        timeout=timeout,
                    )
                # HEAD: read resource, response without body
                # The HEAD method asks for a response identical to a GET request, but without the response body.
                elif method_name == "HEAD":
                    response = requests.head(
                        request_url,
                        headers=request_headers,
                        data=data,
                        files=files,
                        timeout=timeout,
                    )
                # OPTIONS: specify communication options
                # The OPTIONS method describes the communication options for the target resource.
                elif method_name == "OPTIONS":
                    response = requests.options(
                        request_url,
                        headers=request_headers,
                        data=data,
                        files=files,
                        timeout=timeout,
                    )
                # CONNECT:
                # The CONNECT method establishes a tunnel to the server identified by the target resource.
                elif method_name == "CONNECT":
                    pass
                # TRACE:
                # The TRACE method performs a message loop-back test along the path to the target resource.
                elif method_name == "TRACE":
                    pass
                # raise exception if error occurred
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:

                # check if unauthorized request (401)
                if (
                    retry_on_unauthorized
                    and response.status_code == requests.codes.unauthorized
                ):
                    return response

                if response.status_code in {
                    requests.codes.bad_request,
                    requests.codes.not_found,
                }:
                    max_retries = 3

                # retry request
                if attempt < max_retries:
                    time.sleep(waiting_time)
                    response = None
                    continue

                # get more informative error message
                response_content = (
                    getattr(
                        err.response, "text", getattr(err.response, "content", None)
                    )
                    or None
                )
                if response_content:
                    err.args = (f"{err.args[0]}, Response: \n{response_content}",)

                def issue_warning(error):
                    error_message = f"{error}"
                    # print(error_message, file=sys.stderr)
                    warnings.warn(error_message, RuntimeWarning, stacklevel=1)

                if isinstance(errors, str):
                    error_type = errors.lower()
                    if error_type == "coerce":
                        issue_warning(err)
                        return None
                    elif error_type == "ignore":
                        return response
                raise err
            break

        if response is not None:
            try:
                if format in ("json",):
                    return response.json()
                elif format in ("bytes", "binary", "content"):
                    return response.content
                elif format in ("text",):
                    return response.text
                elif format in ("raw",):
                    return response.raw
                elif not format:
                    return response
                return response.content
            except (AttributeError, requests.exceptions.JSONDecodeError):
                return response
        return None

    # get request url
    @staticmethod
    def get_request_url(route: str, api: str, rqst: str, **kwargs) -> str:
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
        """
        # get web api service url
        web_api_service_url = api
        if not web_api_service_url.endswith("/"):
            web_api_service_url += "/"
        # form request url
        request_url = route + rqst.strip()
        # validate request url
        request_url = ApiRequests.validate_url(request_url)
        return web_api_service_url + request_url

    # validate request url
    @staticmethod
    def validate_url(request: str) -> str:
        """
        Validate request url

        Parameters
        ----------
        request : str
            Request
        """
        return requote_uri(request)

    # encode url component
    @staticmethod
    def encode(url_component: str, safe: Union[str, bytes] = "~", **kwargs) -> str:
        """
        Encode url component

        Parameters
        ----------
        url_component : str
            URL component
        safe : str
            Safe symbols which doesn't need to be encoded
        """
        if not isinstance(url_component, str):
            return url_component
        return quote(url_component, safe=safe, **kwargs)

    # return success response
    @staticmethod
    def success():
        """
        Return success response
        """
        response = Response()
        response.status_code = 200
        response._content = json.dumps({"message": "Success!"}).encode("utf-8")
        return response
