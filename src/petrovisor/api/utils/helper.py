from typing import (
    Any,
    Union,
    List,
    Dict,
    Optional,
    cast,
)

import os
from uuid import UUID
import pandas as pd
import numpy as np


# General helper utilities
class ApiHelper:
    """
    General helper utilities
    """

    # get default discovery urls
    @staticmethod
    def get_discovery_urls() -> List[str]:
        """
        Get known discovery urls
        """
        return [
            r"https://identity-latest.eu1.petrovisor.com",
            r"https://identity.eu1.petrovisor.com",
            r"https://identity-latest.us1.petrovisor.com",
            r"https://identity.us1.petrovisor.com",
        ]

    # get object name
    @staticmethod
    def get_object_name(obj: Any, field: str = "Name", **kwargs) -> str:
        """
        Get object name

        Parameters
        ----------
        obj : Any
            Object
        field : str, default 'Name'
            Field name
        """
        if isinstance(obj, str):
            return obj
        elif obj is None:
            return ""
        try:
            return ApiHelper.get_field(obj, field, ignore_case=True) or ""
        except Exception:
            return str(obj)

    # update dictionary
    @staticmethod
    def update_dict(d: Dict, **kwargs) -> Dict:
        """
        Update dictionary fields with keyword argument values

        Parameters
        ----------
        d : dict
            Dictionary
        """
        if kwargs:
            updated_dict = {}
            for k, v in d.items():
                val = ApiHelper.get_dict_value(kwargs, k)
                updated_dict[k] = val if (val is not None) else v
            return updated_dict
        return d

    # remove dictionary fields
    @staticmethod
    def remove_from_dict(d: Dict, keys: Union[str, List[str]], **kwargs):
        """
        Remove dictionary fields

        Parameters
        ----------
        d : dict
            Dictionary
        keys: str | list[str]
            Dictionary keys
        """
        if not isinstance(keys, list):
            keys = [keys]
        return {k: v for k, v in d.items() if k not in keys}

    # check if object has field or attribute
    @staticmethod
    def has_field(obj: Any, field: str, ignore_case: bool = False, **kwargs):
        """
        Check whether object/dict has provided field/attribute

        Parameters
        ----------
        obj : Any
            Object
        field : str
            Field name
        ignore_case : bool, default False
            Whether to ignore field/attribute name case
        """
        if isinstance(obj, dict):
            if field in obj:
                return True
            elif ignore_case:
                if field.casefold() in obj:
                    return True
                return any(k.casefold() == field.casefold() for k in obj.keys())
            else:
                return False
        else:
            if hasattr(obj, field):
                return True
            elif ignore_case:
                if hasattr(obj, field.casefold()):
                    return True
                else:
                    return any(attr.casefold() == field.casefold() for attr in dir(obj))
            else:
                return False

    # get object field value or default
    @staticmethod
    def get_field(obj: Any, field: str, ignore_case: bool = False, **kwargs):
        """
        Get object's field/attribute values

        Parameters
        ----------
        obj : Any
            Object
        field : str
            Field name
        ignore_case : bool, default False
            Whether to ignore field/attribute name case
        kwargs: keyword arguments
            Keyword argument among which if 'default' is present then it is used as default value,
            when field does not exist.
        """
        if isinstance(obj, dict):
            if field in obj:
                return obj[field]
            elif ignore_case:
                if field.casefold() in obj:
                    return obj[field.casefold()]
                else:
                    for k in obj.keys():
                        if k.casefold() == field.casefold():
                            return obj[k]
        else:
            if hasattr(obj, field):
                return getattr(obj, field)
            elif ignore_case:
                if hasattr(obj, field.casefold()):
                    return getattr(obj, field.casefold())
                else:
                    for attr in dir(obj):
                        if attr.casefold() == field.casefold():
                            return getattr(obj, attr)
        # could not find object field/attribute
        if "default" in kwargs:
            return kwargs["default"]
        raise AttributeError(
            f"'{type(obj).__name__}' object has no attribute '{field}'"
        )

    # get non-empty fields
    @staticmethod
    def get_non_empty_fields(d: Dict) -> Dict:
        """
        Get non-empty(is not None) fields of dictionary

        Parameters
        ----------
        d : dict
            Dictionary
        """
        return {k: v for k, v in d.items() if (v is not None)}

    # get default characters to ignore
    @staticmethod
    def get_default_ignore_characters() -> List[str]:
        """
        Get list of default characters to ignore when comparing string names
        """
        return [" ", "_", "-", ".", ","]

    # get comparison string
    @staticmethod
    def get_comparison_string(
        s: str,
        ignore_characters: Union[List[str], str, bool] = True,
        ignore_case: bool = True,
        strip: bool = True,
        **kwargs,
    ):
        """
        Get string preprocessed for comparison

        Parameters
        ----------
        s : str
            String
        ignore_characters : list | bool | str, default True
            Characters to ignore. If True self.get_default_ignore_characters() will be used
        ignore_case: bool, default True
            Ignore case
        strip : bool, default True
            Strip/Trim string
        """
        if ignore_characters:
            if isinstance(ignore_characters, bool):
                ignore_characters = ApiHelper.get_default_ignore_characters()
            elif isinstance(ignore_characters, str):
                ignore_characters = [ignore_characters]
            for c in ignore_characters:
                s = s.replace(c, "")
        if ignore_case:
            s = s.lower()
        return s.strip() if strip else s

    # get dictionary value
    @staticmethod
    def get_dict_value(
        d: Dict,
        key: Union[str, Any],
        ignore_characters: Union[List[str], str, bool] = True,
        ignore_case: bool = True,
        strip: bool = True,
        **kwargs,
    ) -> Optional[str]:
        """
        Get dictionary value

        Parameters
        ----------
        d : str
            String
        key : str | Any
            Dictionary key.
        ignore_characters : list | bool | str, default True
            Characters to ignore. If True self.get_default_ignore_characters() will be used.
        ignore_case: bool, default True
            Ignore case.
        strip : bool, default True
            Strip/Trim string.
        """
        if d:
            if not isinstance(key, str):
                key = str(key)
            if key in d:
                return d[key]
            else:
                key_to_compare = ApiHelper.get_comparison_string(
                    key,
                    ignore_characters=ignore_characters,
                    ignore_case=ignore_case,
                    strip=strip,
                    **kwargs,
                )
                for k, v in d.items():
                    k_to_compare = ApiHelper.get_comparison_string(
                        k,
                        ignore_characters=ignore_characters,
                        ignore_case=ignore_case,
                        strip=strip,
                        **kwargs,
                    )
                    if k_to_compare == key_to_compare:
                        return v
        return None

    # check whether dict/list contains key
    @staticmethod
    def contains(
        d: Union[Dict, List],
        key: Union[str, Any],
        ignore_characters: Union[List[str], str, bool] = True,
        ignore_case: bool = True,
        strip: bool = True,
        **kwargs,
    ) -> bool:
        """
        Check whether dictionary contains field/key

        Parameters
        ----------
        d : str
            String
        key : str | Any
            Dictionary key.
        ignore_characters : list | bool | str, default True
            Characters to ignore. If True self.get_default_ignore_characters() will be used.
        ignore_case: bool, default True
            Ignore case.
        strip : bool, default True
            Strip/Trim string.
        """
        if not isinstance(key, str):
            key = str(key)
        if key in d:
            return True
        else:
            key_to_compare = ApiHelper.get_comparison_string(
                key,
                ignore_characters=ignore_characters,
                ignore_case=ignore_case,
                strip=strip,
                **kwargs,
            )
            for k in d:
                k_to_compare = ApiHelper.get_comparison_string(
                    k,
                    ignore_characters=ignore_characters,
                    ignore_case=ignore_case,
                    strip=strip,
                    **kwargs,
                )
                if k_to_compare == key_to_compare:
                    return True
        return False

    # check whether convertible to integer
    @staticmethod
    def is_int(value: Any, **kwargs) -> bool:
        """
        Is integer value

        Parameters
        ----------
        value : Any
            Value
        """
        try:
            int(value)
        except ValueError:
            return False
        return True

    # check whether convertible to float
    @staticmethod
    def is_float(value: Any, **kwargs) -> bool:
        """
        Is float value

        Parameters
        ----------
        value : Any
            Value
        """
        try:
            float(value)
        except ValueError:
            return False
        return True

    # get uuid
    @staticmethod
    def get_uuid(value: Any, **kwargs) -> UUID:
        """
        Get UUID value

        Parameters
        ----------
        value : Any
            Value
        """
        return UUID(value) if ApiHelper.is_uuid(value) else UUID(value["Id"])

    # is uuid
    @staticmethod
    def is_uuid(value: Any, **kwargs) -> bool:
        """
        Is UUID value

        Parameters
        ----------
        value : Any
            Value
        """
        try:
            UUID(value)
        except ValueError:
            return False
        return True

    # is iterable
    @staticmethod
    def is_iterable(x: Any, exclude_str: bool = True, **kwargs) -> bool:
        """
        Is iterable object

        Parameters
        ----------
        x : Any
            Object
        exclude_str : bool, default True
            Whether to exclude str as iterable
        """
        if hasattr(x, "__iter__") and (not isinstance(x, str) or not exclude_str):
            return True
        return False

    # is empty
    @staticmethod
    def is_empty(x: Any, **kwargs) -> bool:
        """
        Is empty object

        Parameters
        ----------
        x : Any
            Object
        """
        if isinstance(x, np.ndarray):
            return False if x.size else True
        elif isinstance(x, (pd.DataFrame, pd.Series)):
            return True if x.empty else False
        return False if x else True

    # get number of rows
    @staticmethod
    def get_num_rows(x: Any, **kwargs) -> Optional[int]:
        """
        Get number of rows

        Parameters
        ----------
        x : Any
            Object
        """
        if isinstance(x, (np.ndarray, pd.DataFrame, pd.Series)):
            return x.shape[0]
        elif hasattr(x, "__len__"):
            return len(x)
        return None

    # get number of columns
    @staticmethod
    def get_num_cols(x: Any, **kwargs) -> Optional[int]:
        """
        Get number of columns

        Parameters
        ----------
        x : Any
            Object
        """
        if isinstance(x, pd.Series):
            return 0
        elif isinstance(x, (np.ndarray, pd.DataFrame)):
            return x.shape[1] if (len(x.shape) > 1) else 0
        elif isinstance(x, list):
            cols_set = set()
            for row in x:
                cols_set.add(len(row) if ApiHelper.is_iterable(row) else -1)
            if len(cols_set) == 1:
                num_cols = cols_set.pop()
                return None if (num_cols == 0) else 0 if (num_cols == -1) else num_cols
            return None
        return None

    # convert object to list
    @staticmethod
    def to_list(x: Any, **kwargs) -> List[Any]:
        """
        Convert object to list

        Parameters
        ----------
        x : Any
            Object
        """
        if isinstance(x, list):
            return x
        elif isinstance(x, (pd.DataFrame, pd.Series)):
            return cast(list, x.values.tolist())
        elif isinstance(x, np.ndarray):
            return cast(list, x.tolist())
        elif isinstance(
            x,
            (
                set,
                tuple,
            ),
        ):
            return list(x)
        elif isinstance(x, (dict,)):
            return list(x.items())
        return [x]

    # get file extension
    @staticmethod
    def get_file_extension(path: str, **kwargs) -> str:
        """
        Get file extension

        Parameters
        ----------
        path : str
            File path.
        """
        _, file_extension = os.path.splitext(path)
        return file_extension

    # get file name
    @staticmethod
    def get_file_name(path: str, **kwargs) -> str:
        """
        Get file name without extension

        Parameters
        ----------
        path : str
            File path.
        """
        full_name = os.path.basename(path)
        file_name, _ = os.path.splitext(full_name)
        return file_name

    # get Windows-like file path
    @staticmethod
    def get_windows_like_path(path: str, **kwargs) -> str:
        """
        Get Windows-like file path

        Parameters
        ----------
        path : str
            File path.
        """
        if "/" in path:
            path = path.replace("/", "\\")
        return path

    # get Unix-like file path
    @staticmethod
    def get_unix_like_path(path: str, **kwargs) -> str:
        """
        Get Unix-like file path

        Parameters
        ----------
        path : str
            File path.
        """
        if "\\" in path:
            path = path.replace("\\", "/")
        return path
