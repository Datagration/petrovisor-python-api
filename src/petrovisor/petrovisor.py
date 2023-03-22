from typing import Optional

# import api methods
from petrovisor.api.base import RequestsMixin
from petrovisor.api.methods.items import ItemsMixin
from petrovisor.api.methods.entities import EntitiesMixin
from petrovisor.api.methods.signals import SignalsMixin
from petrovisor.api.methods.workspace_values import WorkspaceValuesMixin
from petrovisor.api.methods.psharp import PsharpMixin
from petrovisor.api.methods.reference_tables import RefTableMixin
from petrovisor.api.methods.pivot_tables import PivotTableMixin
from petrovisor.api.methods.dataframes import DataFrameMixin
from petrovisor.api.methods.ml import MLMixin
from petrovisor.api.methods.workflows import WorkflowsMixin
from petrovisor.api.methods.files import FilesMixin
from petrovisor.api.methods.logs import LogsMixin


# PetroVisor API calls
class PetroVisor(RequestsMixin,
                 ItemsMixin,
                 EntitiesMixin,
                 SignalsMixin,
                 WorkspaceValuesMixin,
                 PsharpMixin,
                 RefTableMixin,
                 PivotTableMixin,
                 MLMixin,
                 WorkflowsMixin,
                 FilesMixin,
                 LogsMixin,
                 DataFrameMixin, ):
    """
    PetroVisor API class
    """

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

        super().__init__(workspace=workspace,
                         api=api,
                         token=token,
                         discovery_url=discovery_url,
                         key=key,
                         username=username,
                         password=password,
                         **kwargs)
