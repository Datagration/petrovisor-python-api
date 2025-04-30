from typing import (
    Any,
    Optional,
    List,
)

from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
)


# DataGrid API calls
class DataGridsMixin(SupportsItemRequests, SupportsRequests):
    """
    DataGrid API calls
    """

    # import data grids according to specified filter
    def import_data_grids(
        self,
        file_filter: Optional[str] = "",
        file_extension: Optional[str] = "",
        default_crs: Optional[str] = "EPSG:3857",
        **kwargs,
    ) -> List[str]:
        """
        Import DataGrid according to specified filter

        Parameters
        ----------
        file_extension : str, default None
            File extension
        file_filter : str, default None
            File filter
        default_crs : str, default 'EPSG:3857'
            Coordinate Reference System (CRS)
        """
        route = "DataGrids"
        options = {
            "Extension": file_extension,
            "Filter": file_filter,
            "DefaultCRS": default_crs,
        }
        return self.get(f"{route}/Import", query=options)

    # update DataGrid's CRS
    def update_data_grid_crs(self, name: str, crs: str, **kwargs) -> Any:
        """
        Set DataGrid's CRS

        Parameters
        ----------
        name : str
            DataGrid name
        crs : str
            Coordinate Reference System (CRS)
        """
        route = "DataGrids"
        options = {"CRS": crs}
        return self.post(f"{route}/{self.encode(name)}/CRS", query=options)

    # project DataGrid to specified CRS
    def project_data_grid_to_crs(
        self, name: str, crs: str = "+proj=longlat +datum=WGS84 +no_defs", **kwargs
    ) -> Any:
        """
        Project DataGrid to specified CRS

        Parameters
        ----------
        name : str
            DataGrid name
        crs : str, default '+proj=longlat +datum=WGS84 +no_defs'
            Coordinate Reference System (CRS)
        """
        route = "DataGrids"
        options = {"CRS": crs}
        return self.get(f"{route}/{self.encode(name)}/Project", query=options)
