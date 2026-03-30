from typing import (
    Any,
    List,
    Optional,
)

from uuid import UUID

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.protocols.protocols import SupportsRequests


# Workflows mixin helper
class WorkflowsMixinHelper:
    """
    Workflows mixin helper — endpoint constants.
    """

    ENDPOINT = "WorkflowExecution"
    ENDPOINT_REQUEST = "WorkflowExecution/AddRequest"


# Workflows API calls
class WorkflowsMixin(SupportsRequests):
    """
    Workflows API calls
    """

    # run 'Workflow'
    def run_workflow(
        self,
        workflow: str,
        contexts: Optional[List[str]] = None,
        scope: Optional[str] = None,
        entity_set: Optional[str] = None,
        schedule_name: str = "Now",
        source: str = "by Activity service",
        **kwargs,
    ) -> Any:
        """
        Run workflow

        Parameters
        ----------
        workflow : str
            Workflow name
        contexts : list[str], default []
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
        data = {
            "WorkflowName": workflow,
            "WorkspaceName": self.Workspace,
            "Source": source,
            "ScheduleName": schedule_name,
            "ProcessingContexts": contexts if contexts else [],
        }
        if scope:
            data["ProcessingScopeName"] = scope
        if entity_set:
            data["ProcessingEntitySet"] = entity_set
        return self.post(WorkflowsMixinHelper.ENDPOINT_REQUEST, data=data, **kwargs)

    # get 'Workflow' execution state
    def get_workflow_execution_state(self, uid: UUID, **kwargs):
        """
        Get workflow execution state

        Parameters
        ----------
        uid : UUID
            Workflow id
        """
        uuid = ApiHelper.get_uuid(uid)
        return self.get(
            f"{WorkflowsMixinHelper.ENDPOINT}/{self.encode(str(uuid))}", **kwargs
        )
