from typing import (
    Any,
    Optional,
    List,
    Dict,
)

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
)


# Entities API calls
class EntitiesMixin(SupportsItemRequests, SupportsRequests):
    """
    Entities API calls
    """

    # get entity
    def get_entity(self, name: str, alias: Optional[str] = '', **kwargs) -> Dict:
        """
        Get entity

        Parameters
        ----------
        name : str
            Entity name
        alias : str
            Entity alias
        """
        route = 'Entities'
        if alias:
            return self.get(f'{route}/{self.encode(alias)}/Entity', **kwargs)
        return self.get(f'{route}/{self.encode(name)}', **kwargs)

    # get entities
    def get_entities(self, entity_type: Optional[str] = '', signal: Optional[str] = '', **kwargs) -> List[Dict]:
        """
        Get entities. Filter optionally by entity type and signal

        Parameters
        ----------
        entity_type : str, default ''
            Entity type
        signal : str, default ''
            Signal object or Signal name
        """
        route = 'Entities'
        # get entities by 'Entity' type
        if entity_type:
            entities = self.get(f'{route}/{entity_type}/Entities', **kwargs)
        # get all entities
        else:
            entities = self.get(f'{route}/All', **kwargs)
        # get entities by 'Signal' name
        if signal:
            entity_names = self.get_entity_names(signal_type=None, signal=signal, **kwargs)
            if entity_names:
                return [e for e in entities if e['Name'] in entity_names]
        return entities if entities is not None else []

    # get entity names
    def get_entity_names(self, entity_type: Optional[str] = '', signal: Optional[str] = '', **kwargs) -> List[str]:
        """
        Get entity names. Filter optionally by entity type and signal

        Parameters
        ----------
        entity_type : str, default ''
            Entity type
        signal : str, default ''
            Signal object or Signal name
        """

        route = 'Entities'
        # get entities by 'Signal' name
        if signal:
            signals_route = 'Signals'
            signal_name = ApiHelper.get_object_name(signal)
            entity_names = self.get(f'{signals_route}/{self.encode(signal_name)}/Entities', **kwargs)
            if entity_type and entity_names is not None:
                entity_type_names = self.get_entity_names(entity_type=entity_type, signal=None, **kwargs)
                if entity_type_names:
                    return [e for e in entity_names if e in entity_type_names]
        # get entities by 'Entity' type
        elif entity_type:
            entities = self.get_entities(entity_type=entity_type, signal=None, **kwargs)
            return [e['Name'] for e in entities]
        # get all entities
        else:
            entity_names = self.get(f'{route}', **kwargs)
        return entity_names if entity_names is not None else []

    # add entities
    def add_entities(self, entities: List, **kwargs) -> Any:
        """
        Add multiple entities

        Parameters
        ----------
        entities : list
            List of entities
        """
        route = 'Entities'
        return self.post(f'{route}/AddOrEdit', data=entities, **kwargs)

    # delete entities
    def delete_entities(self, entities: List, **kwargs) -> Any:
        """
        Delete multiple entities

        Parameters
        ----------
        entities : list
            List of entities
        """
        route = 'Entities'
        return self.post(f'{route}/Delete', data=entities, **kwargs)

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
        route = 'EntityTypes'
        return self.post(f'{route}/Rename', query={'OldName': old_name, 'NewName': new_name}, **kwargs)

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
        route = 'Entities'
        return self.post(f'{route}/Rename', query={'OldName': old_name, 'NewName': new_name}, **kwargs)
