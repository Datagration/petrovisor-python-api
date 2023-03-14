from typing import (
    Any,
    Optional,
    List,
    Callable,
)

import io
import pickle

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
        return self.get('Files', **kwargs)

    # get file by name
    def get_file(self, filename: str, format: str = 'bytes', **kwargs) -> Any:
        """
        Get file

        Parameters
        ----------
        filename : str
            File name
        format : str, default 'bytes'
            File format
        """
        return self.get(f'Files/{filename}', format=format, **kwargs)

    # get file by name
    def delete_file(self, filename: str, **kwargs) -> Any:
        """
        Delete file

        Parameters
        ----------
        filename : str
            File name
        """
        return self.delete(f'Files/{filename}', **kwargs)

    # upload file
    def upload_file(self, file: Any, **kwargs) -> Any:
        """
        Upload file

        Parameters
        ----------
        file : Any
            file object
        """
        return self.post('Files/Upload', files={'file': open(file, 'rb') if isinstance(file, str) else file}, **kwargs)

    # get object by name
    def get_object(self, objectname: str, func: Optional[Callable] = None, **kwargs) -> Any:
        """
        Load object from blob storage using pickle.loads()

        Parameters
        ----------
        objectname : str
            Object name
        func : Optional[Callable], default None
            Function to be called to prepare object after load. If None, then pickle.loads() is used
        """
        file_obj = self.get_file(objectname, format='bytes', **kwargs)
        if func and hasattr(func, '__call__'):
            return func(file_obj, **kwargs)
        return pickle.loads(file_obj)

    # upload object
    def upload_object(self, obj: Any, name: str, func: Optional[Callable] = None, **kwargs) -> Any:
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
        if func and hasattr(func, '__call__'):
            file = func(obj, **kwargs)
        else:
            file = pickle.dumps(obj)
        file_obj = io.BytesIO(file)
        file_obj.name = name
        return self.upload_file(file=file_obj, **kwargs)
