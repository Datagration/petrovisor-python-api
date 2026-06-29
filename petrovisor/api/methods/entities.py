from typing import (
    Any,
    Optional,
    Sequence,
    Union,
    List,
    Dict,
)

from petrovisor.api.models.entity import Entity
from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.enums.items import ItemType
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
)


# Entities mixin helper
class EntitiesMixinHelper:
    """
    Entities mixin helper — endpoint constants.
    """

    ENDPOINT = "Entities"
    ENDPOINT_ALL = "Entities/All"
    ENDPOINT_ADD_OR_EDIT = "Entities/AddOrEdit"
    ENDPOINT_DELETE = "Entities/Delete"
    ENDPOINT_RENAME = "Entities/Rename"
    ENDPOINT_ENTITY_TYPES = "EntityTypes"
    ENDPOINT_ENTITY_TYPES_RENAME = "EntityTypes/Rename"
    ENDPOINT_SIGNALS = "Signals"


# Entities API calls
class EntitiesMixin(SupportsItemRequests, SupportsRequests):
    """
    Entities API calls
    """

    # get entity
    def get_entity(self, name: str, alias: Optional[str] = "", **kwargs) -> Dict:
        """
        Get entity

        Parameters
        ----------
        name : str
            Entity name
        alias : str
            Entity alias
        """
        route = EntitiesMixinHelper.ENDPOINT
        if alias:
            return self.get(f"{route}/{self.encode(alias)}/Entity", **kwargs)
        return self.get(f"{route}/{self.encode(name)}", **kwargs)

    # get entities
    def get_entities(
        self,
        entity_type: Optional[str] = "",
        signal: Optional[str] = "",
        include_entities: bool = True,
        include_opportunities: bool = False,
        **kwargs,
    ) -> List[Dict]:
        """
        Get entities. Filter optionally by entity type and signal

        Parameters
        ----------
        entity_type : str, default ''
            Entity type
        signal : str, default ''
            Signal object or Signal name
        include_entities : bool, default True
            Whether to include entities
        include_opportunities : bool, default False
            Whether to include opportunities
        """
        route = EntitiesMixinHelper.ENDPOINT
        options = {
            "IncludeEntities": include_entities,
            "IncludeOpportunities": include_opportunities,
        }
        options = ApiHelper.update_dict(options, **kwargs)
        # get entities by 'Entity' type
        if entity_type:
            entities = self.get(
                f"{route}/{entity_type}/Entities", query=options, **kwargs
            )
        # get all entities
        else:
            entities = self.get(
                EntitiesMixinHelper.ENDPOINT_ALL, query=options, **kwargs
            )
        # get entities by 'Signal' name
        if signal:
            entity_names = self.get_entity_names(
                signal_type=None, signal=signal, **kwargs
            )
            if entity_names:
                return [e for e in entities if e["Name"] in entity_names]
        return entities if entities is not None else []

    # get entity names
    def get_entity_names(
        self, entity_type: Optional[str] = "", signal: Optional[str] = "", **kwargs
    ) -> List[str]:
        """
        Get entity names. Filter optionally by entity type and signal

        Parameters
        ----------
        entity_type : str, default ''
            Entity type
        signal : str, default ''
            Signal object or Signal name
        """

        route = EntitiesMixinHelper.ENDPOINT
        # get entities by 'Signal' name
        if signal:
            signals_route = EntitiesMixinHelper.ENDPOINT_SIGNALS
            signal_name = ApiHelper.get_object_name(signal)
            entity_names = self.get(
                f"{signals_route}/{self.encode(signal_name)}/Entities", **kwargs
            )
            if entity_type and entity_names is not None:
                entity_type_names = self.get_entity_names(
                    entity_type=entity_type, signal=None, **kwargs
                )
                if entity_type_names:
                    return [e for e in entity_names if e in entity_type_names]
        # get entities by 'Entity' type
        elif entity_type:
            entities = self.get_entities(
                entity_type=entity_type,
                signal=None,
                include_entities=True,
                include_opportunities=True,
                **kwargs,
            )
            return [e["Name"] for e in entities]
        # get all entities
        else:
            options = {
                "IncludeEntities": True,
                "IncludeOpportunities": True,
            }
            options = ApiHelper.update_dict(options, **kwargs)
            entity_names = self.get(f"{route}", query=options, **kwargs)
        return entity_names if entity_names is not None else []

    # add entity
    def add_entity(self, entity: Union[Entity, Dict[str, Any]], **kwargs) -> Any:
        """
        Add entity

        Parameters
        ----------
        entity : Entity | dict
            Entity
        """
        route = EntitiesMixinHelper.ENDPOINT
        if isinstance(entity, Entity):
            validated_entity = entity.model_dump(by_alias=True)
        elif isinstance(entity, dict):
            validated_entity = entity
        else:
            raise ValueError(
                "PetroVisor::add_entity(): "
                "Invalid type. Entity should be of type dict or Entity."
            )
        return self.post(f"{route}", data=validated_entity, **kwargs)

    # add entities
    def add_entities(
        self, entities: Sequence[Union[Entity, Dict[str, Any]]], **kwargs
    ) -> Any:
        """
        Add multiple entities

        Parameters
        ----------
        entities : list[Entity | dict]
            List of entities
        """
        validated_entities = [
            e.model_dump(by_alias=True) if isinstance(e, Entity) else e
            for e in entities
            if isinstance(e, dict) or isinstance(e, Entity)
        ]
        return self.post(
            EntitiesMixinHelper.ENDPOINT_ADD_OR_EDIT, data=validated_entities, **kwargs
        )

    # delete entity
    def delete_entity(
        self, entity: Union[Entity, Dict[str, Any], str], **kwargs
    ) -> Any:
        """
        Delete entity

        Parameters
        ----------
        entity : Entity | dict | str
            Entity
        """
        if isinstance(entity, Entity):
            name = entity.name
        else:
            name = ApiHelper.get_object_name(entity)
        if not name:
            return ApiRequests.success()
        return self.delete_item(ItemType.Entity, name, **kwargs)

    # delete entities
    def delete_entities(
        self, entities: Sequence[Union[Entity, Dict[str, Any], str]], **kwargs
    ) -> Any:
        """
        Delete multiple entities

        Parameters
        ----------
        entities : list[Entity | dict | str]
            List of entities
        """
        names = [
            e.name if isinstance(e, Entity) else ApiHelper.get_object_name(e)
            for e in entities
            if e
        ]
        names = [name for name in names if name]
        return self.post(EntitiesMixinHelper.ENDPOINT_DELETE, data=names, **kwargs)

    # rename entity type
    def rename_entity_type(self, old_name: str, new_name: str, **kwargs) -> Any:
        """
        Rename entity type

        Parameters
        ----------
        old_name : str
            Old name
        new_name : str
            New name
        """
        return self.post(
            EntitiesMixinHelper.ENDPOINT_ENTITY_TYPES_RENAME,
            query={"OldName": old_name, "NewName": new_name},
            **kwargs,
        )

    # rename entity
    def rename_entity(self, old_name: str, new_name: str, **kwargs) -> Any:
        """
        Rename entity

        Parameters
        ----------
        old_name : str
            Old name
        new_name : str
            New name
        """
        return self.post(
            EntitiesMixinHelper.ENDPOINT_RENAME,
            query={"OldName": old_name, "NewName": new_name},
            **kwargs,
        )
