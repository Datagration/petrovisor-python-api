from typing import (
    Any,
    Optional,
    Union,
    Dict,
)

import json
import base64
import requests


class ApiLogin:
    """
    PetroVisor login

    Returns
    -------
    Access Token
    """

    def __init__(self, **kwargs):
        pass

    # get access token
    @staticmethod
    def get_access_token(
        key: str = "",
        username: str = "",
        password: str = "",
        refresh_token: str = "",
        discovery_url: str = "",
        token_endpoint: str = "",
        **kwargs,
    ) -> Dict:
        """
        Get access token response

        Parameters
        ----------
        key : str, default None
            Access key generated from username and password
        refresh_token : str, default None
            Refresh Token
        discovery_url : str, default None
            Discovery url
        username : str, default None
            Username
        password : str, default None
            Password
        token_endpoint : str, default None
            Token endpoint
        """
        access_response = None
        if key:
            access_response = ApiLogin.get_access_token_from_key(
                key,
                discovery_url=discovery_url,
                token_endpoint=token_endpoint,
                **kwargs,
            )
        if not access_response and username and password:
            access_response = ApiLogin.get_access_token_from_credentials(
                username,
                password,
                discovery_url=discovery_url,
                token_endpoint=token_endpoint,
                **kwargs,
            )
        if not access_response and refresh_token:
            access_response = ApiLogin.get_access_token_from_refresh_token(
                refresh_token,
                discovery_url=discovery_url,
                token_endpoint=token_endpoint,
                **kwargs,
            )
        return access_response

    # get access token from key
    @staticmethod
    def get_access_token_from_key(
        key: str, discovery_url: str = "", token_endpoint: str = "", **kwargs
    ) -> Dict:
        """
        Get access token response from key

        Parameters
        ----------
        key : str
            Access key generated from username and password
        discovery_url : str, default None
            Discovery url
        token_endpoint : str, default None
            Token endpoint
        """
        credentials = ApiLogin.get_credentials_from_key(key)
        username = credentials["username"]
        password = credentials["password"]
        return ApiLogin.get_access_token_from_credentials(
            username,
            password,
            discovery_url=discovery_url,
            token_endpoint=token_endpoint,
        )

    # get access token from username and password
    @staticmethod
    def get_access_token_from_credentials(
        username: str,
        password: str,
        discovery_url: str = "",
        token_endpoint: str = "",
        **kwargs,
    ) -> Dict:
        """
        Get access token response from credentials

        Parameters
        ----------
        username : str
            Username
        password : str
            Password
        discovery_url : str, default None
            Discovery url
        token_endpoint : str, default None
            Token endpoint
        """
        if not token_endpoint:
            token_endpoint = ApiLogin.get_token_endpoint(discovery_url=discovery_url)
        grant_type = "password"
        client_id = "petrovisor.python.client"
        scope = "petrovisor.api"
        requests_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        request_data = {
            "username": username,
            "password": password,
            "client_id": client_id,
            "grant_type": grant_type,
            "scope": scope,
        }
        response = requests.post(
            token_endpoint, headers=requests_headers, data=request_data
        )
        # get response content
        access_response = json.loads(response.content)
        return access_response

    # get access token from refresh token
    @staticmethod
    def get_access_token_from_refresh_token(
        refresh_token: str, discovery_url: str = "", token_endpoint: str = "", **kwargs
    ) -> Dict:
        """
        Get access token response from refresh token

        Parameters
        ----------
        refresh_token : str, default None
            Refresh Token
        discovery_url : str, default None
            Discovery url
        token_endpoint : str, default None
            Token endpoint
        """
        if not token_endpoint:
            token_endpoint = ApiLogin.get_token_endpoint(discovery_url=discovery_url)
        grant_type = "refresh_token"
        client_id = "petrovisor.python.client"
        scope = "petrovisor.api"
        requests_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        request_data = {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "grant_type": grant_type,
            "scope": scope,
        }
        response = requests.post(
            token_endpoint, headers=requests_headers, data=request_data
        )
        # get response content
        access_response = json.loads(response.content)
        return access_response

    # get credentials structure with username and password from key
    @staticmethod
    def get_credentials_from_key(key: str, **kwargs) -> Dict:
        """
        Get credentials from key

        Parameters
        ----------
        key : str
            Access key generated from username and password
        """
        valid_credentials = {
            "username": "",
            "password": "",
        }
        if key and isinstance(key, str):
            # decode the key
            auth = ApiLogin.decode_base64(key)
            if auth:
                s = str(auth).split(":")
                if s and len(s) > 1:
                    valid_credentials["username"] = s[0]
                    valid_credentials["password"] = ":".join(s[1:])
        return valid_credentials

    # get credentials structure with username and password
    @staticmethod
    def get_credentials(username: str, password: str) -> Dict:
        """
        Get credentials from username and password

        Parameters
        ----------
        username : str
            Username
        password : str
            Password
        """
        valid_credentials = {
            "username": username,
            "password": password,
        }
        return valid_credentials

    # generate credentials key from username and password
    @staticmethod
    def generate_credentials_key(
        username: str = "", password: str = "", **kwargs
    ) -> str:
        """
        Get credentials key

        Parameters
        ----------
        username : str, default None
            Username
        password : str, default None
            Password
        """
        if username and password:
            # decode the key
            key = ApiLogin.encode_base64(username + ":" + password)
        else:
            key = ""
        return key

    # get token endpoint
    @staticmethod
    def get_token_endpoint(discovery_url: str = "", **kwargs) -> str:
        """
        Get token endpoint

        Parameters
        ----------
        discovery_url : str, default None
            Discovery url
        """
        return ApiLogin.get_endpoint("token_endpoint", discovery_url=discovery_url)

    # get web api endpoint
    @staticmethod
    def get_web_api_endpoint(discovery_url: str = "", **kwargs) -> str:
        """
        Get web api endpoint

        Parameters
        ----------
        discovery_url : str, default None
            Discovery url
        """
        return ApiLogin.get_endpoint(
            "petrovisor_webapi_endpoint", discovery_url=discovery_url
        )

    # get endpoint
    @staticmethod
    def get_endpoint(endpoint_name: str, discovery_url: str = "", **kwargs) -> str:
        """
        Get endpoint

        Parameters
        ----------
        endpoint_name : str
            Endpoint name
        discovery_url : str, default None
            Discovery url
        """
        endpoints = ApiLogin.get_discovery_document(discovery_url)
        if endpoints and endpoint_name in endpoints:
            return endpoints[endpoint_name]
        return ""

    # get discovery document
    @staticmethod
    def get_discovery_document(discovery_url: str = "", **kwargs) -> Any:
        """
        Get discovery document

        Parameters
        ----------
        discovery_url : str, default None
            Discovery url
        """
        if not discovery_url:
            raise ValueError(
                "PetroVisorLogin::get_discovery_document(): "
                "'discovery_url' is undefined!"
            )
        if not discovery_url.endswith("/"):
            discovery_url += "/"
        well_known_url = f"{discovery_url}.well-known/openid-configuration"
        endpoints = requests.get(well_known_url).json()
        return endpoints

    # encode base64 message
    @staticmethod
    def decode_base64(
        base64_message: Union[bytes, str],
        fmt: str = "ascii",
        altchars: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Decode base64 string

        Parameters
        ----------
        base64_message : bytes, str
            Base64 message
        fmt : str, default 'ascii'
            Format
        altchars : str
            Alternative characters encoded instead of + or / characters.
            altchars is a byte-like object and must have a minimum length of 2.
        """
        base64_bytes = (
            base64_message
            if isinstance(base64_message, bytes)
            else str(base64_message).encode(fmt)
        )
        # altchars = b'+/'
        # base64_bytes = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'', base64_bytes)  # normalize
        missing_padding = (4 - len(base64_bytes) % 4) % 4
        if missing_padding:
            base64_bytes += b"=" * missing_padding
        # num_bytes = len(base64_bytes)
        # message_bytes = base64.b64decode(base64_bytes, altchars)
        has_dash_underscore = (
            True if (b"-" in base64_bytes or b"_" in base64_bytes) else False
        )
        if has_dash_underscore:
            altchars = b"-_"
        message_bytes = None
        try:
            if altchars:
                message_bytes = base64.b64decode(base64_bytes, altchars)
            else:
                message_bytes = base64.b64decode(base64_bytes)
        except ValueError:
            pass
        finally:
            if message_bytes:
                message = (
                    message_bytes
                    if ApiLogin.is_binary_string(message_bytes)
                    else message_bytes.decode(fmt)
                )
            else:
                message = ""
        return message

    # encode base64 message
    @staticmethod
    def encode_base64(
        base64_message: Union[bytes, str], fmt: str = "ascii", **kwargs
    ) -> str:
        """
        Encode base64 string

        Parameters
        ----------
        base64_message : bytes, str
            Base64 message
        fmt : str, default 'ascii'
            Format
        """
        import base64

        base64_bytes = (
            base64_message
            if isinstance(base64_message, bytes)
            else str(base64_message).encode(fmt)
        )
        message_bytes = base64.b64encode(base64_bytes)
        message = message_bytes.decode(fmt)
        return message

    # check whether string is binary
    @staticmethod
    def is_binary_string(bytes_str: bytes, **kwargs) -> bool:
        """
        Check whether string is binary

        Parameters
        ----------
        bytes_str : bytes
            Bytes string
        """
        textchars = bytearray(
            {7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F}
        )
        return bool(bytes_str.translate(None, textchars))
