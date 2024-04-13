from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.protocols.protocols import SupportsRequests


# PetroVisor Logs API calls
class LogsMixin(SupportsRequests):
    """
    PetroVisor Logs API calls
    """

    # add log entry
    def add_log_entry(self, message: str, **kwargs):
        """
        Add log entry message.
        Use keyword arguments to pass other information.
        Known fields are:
            'message',
            'workflow','category','username',
            'workspace','schedule',
            'severity',
            'timestamp'(utc),'starttime','endtime','elapsedtime',
            'script','entity','signal','unit','tag',
            'numberofitems','valuebefore','valueafter',
            'messagedetails','directory'
        Parameters
        ----------
        message : str
            Log message
        """
        log_entry = {
            "Timestamp": None,
            "Message": message,
            "Category": None,
            "UserName": None,
            "Severity": None,
            "Workspace": None,
            "Schedule": None,
            "Workflow": None,
            "StartTime": None,
            "EndTime": None,
            "Script": None,
            "Entity": None,
            "Signal": None,
            "Unit": None,
            "Tag": None,
            "NumberOfItems": None,
            "ValueBefore": None,
            "ValueAfter": None,
            "ElapsedTime": None,
            "MessageDetails": None,
            "Directory": None,
        }
        log_entry = ApiHelper.update_dict(log_entry, **kwargs)
        return self.post(
            "LogEntries", data=ApiHelper.get_non_empty_fields(log_entry), **kwargs
        )

    # add workflow log entry
    def add_workflow_log_entry(self, message: str, workflow: str, **kwargs):
        """
        Add log entry message to tge running workflow.
        Use keyword arguments to pass other information.
        Known fields are:
            'message',
            'workspace','schedule',
            'severity',
            'timestamp'(utc),'starttime','endtime','elapsedtime',
            'script','entity','signal','unit','tag',
            'numberofitems','valuebefore','valueafter',
            'messagedetails','directory'
        Parameters
        ----------
        message : str
            Log message
        workflow : str
            Workflow name
        """
        return self.add_log_entry(
            message,
            Workflow=workflow,
            Category="Workflow Execution",
            UserName="WorkflowService",
            **kwargs,
        )
