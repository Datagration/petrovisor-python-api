from typing import (
    Any,
    List,
    Optional,
)

from uuid import UUID

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.protocols.protocols import SupportsRequests


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
        scope: str = None,
        entity_set: str = None,
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
        return self.post("WorkflowExecution/AddRequest", data=data, **kwargs)

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
        return self.get(f"WorkflowExecution/{self.encode(str(uuid))}", **kwargs)
