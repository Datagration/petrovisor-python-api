from typing import (
    Any,
    Optional,
    List,
    Callable,
)

import os
import io
import json
import pickle

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.protocols.protocols import SupportsRequests


# Files API calls
class FilesMixin(SupportsRequests):
    """
    Files API calls
    """

    # get file names
    def get_file_names(self, **kwargs) -> List[str]:
        """
        Get file names
        """
        return self.get("Files", **kwargs)

    # get file by name
    def get_file(self, filename: str, format: str = "bytes", **kwargs) -> Any:
        """
        Get file

        Parameters
        ----------
        filename : str
            File name
        format : str, default 'bytes'
            File format
        """
        filename = ApiHelper.get_windows_like_path(filename)
        return self.get(f"Files/{self.encode(filename)}", format=format, **kwargs)

    # delete file by given name
    def delete_file(self, filename: str, **kwargs) -> Any:
        """
        Delete file

        Parameters
        ----------
        filename : str
            File name
        """
        filename = ApiHelper.get_windows_like_path(filename)
        return self.delete(f"Files/{self.encode(filename)}", **kwargs)

    # upload file
    def upload_file(self, file: Any, name: str = "", **kwargs) -> Any:
        """
        Upload file

        Parameters
        ----------
        file : str | stream
            File path or file-like object
        name : str
            File name
        """
        # upload file with specified name
        if name:
            name = ApiHelper.get_unix_like_path(name)
            return self.post(
                "Files/Upload",
                files={
                    "file": (name, open(file, "rb") if isinstance(file, str) else file)
                },
                **kwargs,
            )
        # upload file with the same name as file's name or name specified in the file-like object
        return self.post(
            "Files/Upload",
            files={"file": open(file, "rb") if isinstance(file, str) else file},
            **kwargs,
        )

    # upload folder
    def upload_folder(self, folder: str, name: str = "", **kwargs) -> Any:
        """
        Upload folder

        Parameters
        ----------
        folder : str
            Folder path
        name : str
            Folder name
        """
        if not os.path.isdir(folder):
            return
        # validate new folder name
        if name:
            name = ApiHelper.get_unix_like_path(name)
        # upload folder with specified name
        folder_relpath: str = os.path.dirname(folder)
        for root, dirs, files in os.walk(folder):
            for filename in files:
                file_path = os.path.join(root, filename)

                # get file relative path
                root_relpath = os.path.relpath(root, folder_relpath)
                if name:
                    parts = root_relpath.split(os.sep)
                    parts[0] = name
                    root_relpath = os.sep.join(parts)

                # get file relative path
                file_relpath = os.path.join(root_relpath, filename)
                file_relpath = os.path.normpath(file_relpath)

                # upload file
                self.upload_file(file_path, name=file_relpath, **kwargs)

    # delete folder by given name
    def delete_folder(self, folder: str, **kwargs) -> Any:
        """
        Delete folder

        Parameters
        ----------
        folder : str
            Folder name
        """
        # get all files
        files = self.get_file_names(**kwargs)
        # validate folder name (path is returned in Unix-like style)
        if folder:
            folder = ApiHelper.get_unix_like_path(folder)
        for filename in files:
            if filename.startswith(folder):
                self.delete_file(filename, **kwargs)

    # get object by name
    def get_object(
        self, name: str, func: Optional[Callable] = None, binary: bool = True, **kwargs
    ) -> Any:
        """
        Load object from blob storage using pickle.loads()

        Parameters
        ----------
        name : str
            Object name
        func : Optional[Callable], default None
            Function to be called to prepare object after load. If None, then pickle.loads() is used
        binary : bool, default True
            Whether to use binary (True) stream io.BytesIO or text (False) stream io.StringIO
        """
        file_obj = self.get_file(name, format="bytes", **kwargs)
        if func and hasattr(func, "__call__"):
            return func(file_obj, **kwargs)
        if binary:
            return pickle.loads(file_obj)
        return json.load(io.BytesIO(file_obj), **kwargs)

    # upload object
    def upload_object(
        self,
        obj: Any,
        name: str,
        func: Optional[Callable] = None,
        binary: bool = True,
        **kwargs,
    ) -> Any:
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
        binary : bool, default True
            Whether to use binary (True) stream io.BytesIO or text (False) stream io.StringIO
        """
        # upload file by full path
        if func and hasattr(func, "__call__"):
            file = func(obj, **kwargs)
        elif binary:
            file = pickle.dumps(obj)
        else:
            file = json.dumps(obj, **kwargs)
        # binary stream
        if binary:
            file_obj = io.BytesIO(file)
        else:
            file_obj = io.StringIO(file)
        file_obj.name = name
        return self.upload_file(file=file_obj, name=name, **kwargs)
