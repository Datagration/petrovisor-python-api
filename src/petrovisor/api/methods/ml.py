from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

from uuid import UUID

from petrovisor.api.enums.items import ItemType
from petrovisor.api.enums.ml import (
    MLModelType,
    MLNormalizationType,
)
from petrovisor.api.utils.validators import Validator
from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
    SupportsPsharpRequests,
)


# PetroVisor ML API calls
class MLMixin(SupportsPsharpRequests, SupportsItemRequests, SupportsRequests):
    """
    PetroVisor ML API calls
    """

    # get ML models
    def ml_models(self, **kwargs) -> Any:
        """
        Get ML Models
        """
        return self.get_items(ItemType.MLModel, **kwargs)

    # get ML models
    def ml_model_names(self, **kwargs) -> Any:
        """
        Get ML Model names
        """
        return self.get_item_names(ItemType.MLModel, **kwargs)

    # get ML model
    def ml_model(self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        return self.get_item(ItemType.MLModel, model_name, **kwargs)

    # get ML model attribute
    def ml_model_attribute(self, model_name: str, attribute: str, **kwargs) -> Any:
        """
        Get ML Model type

        Parameters
        ----------
        model_name : str
            ML Model name
        attribute : str
            ML Model attribute
        """
        ml_model = self.ml_model(model_name, **kwargs)
        if ml_model is None or not ml_model:
            raise ValueError(
                f"PetroVisor::ml_model_attribute(): "
                f"ML Model '{model_name}' cannot be found!"
            )
        if attribute in ml_model:
            return ml_model[attribute]
        raise ValueError(
            f"PetroVisor::ml_model_attribute(): "
            f"unknown ML Model attribute '{attribute}'!"
        )

    # get ML model type
    def ml_model_type(self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model type

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        return self.ml_model_attribute(model_name, "Type", **kwargs)

    # get ML model features and label
    def ml_model_features_and_label(self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model features and label

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        features = {}
        features_script = self.ml_model_attribute(model_name, "TableFormula", **kwargs)
        feature_tables = self.get_psharp_script_columns_and_signals(
            features_script, **kwargs
        )
        if feature_tables:
            for table_name, table in feature_tables.items():
                if table:
                    return table
        return features

    # get ML model features
    def ml_model_features(self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model features

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        features = self.ml_model_features_and_label(model_name, **kwargs)
        label = self.ml_model_attribute(model_name, "LabelColumnName", **kwargs)
        return {k: v for k, v in features.items() if k != label}

    # get ML model feature names
    def ml_model_feature_names(self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model feature names

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        features = self.ml_model_features(model_name, **kwargs)
        return list(features.keys())

    # get ML model label
    def ml_model_label(self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model label

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        label = self.ml_model_attribute(model_name, "LabelColumnName", **kwargs)
        features = self.ml_model_features_and_label(model_name, **kwargs)
        for k, v in features.items():
            if k == label:
                return label, v
        return label, None

    # get ML model label name
    def ml_model_label_name(self, model_name: str, **kwargs) -> Any:
        """
        Get ML Model label name

        Parameters
        ----------
        model_name : str
            ML Model name
        """
        return self.ml_model_attribute(model_name, "LabelColumnName", **kwargs)

    # get ML trainers and metrics
    def ml_trainers_and_metrics(
        self, model_type: Union[str, MLModelType], **kwargs
    ) -> Any:
        """
        Get ML trainers and metrics

        Parameters
        ----------
        model_type : str, MLModelType
            ML Model type:
            'Regression', 'BinaryClassification', 'MultipleClassification', 'Clustering',
            'NaiveBayes', 'NaiveBayesCategorical'
        """
        route = "MLModels/TrainersAndMetrics"
        model_type = self.get_ml_model_type_enum(model_type, **kwargs).name
        return self.get(route, query={"ModelType": model_type}, **kwargs)

    # get ML trainers
    def ml_trainers(self, model_type: Union[str, MLModelType], **kwargs) -> Any:
        """
        Get ML trainers

        Parameters
        ----------
        model_type : str, MLModelType
            ML Model type:
            'Regression', 'BinaryClassification', 'MultipleClassification', 'Clustering',
            'NaiveBayes', 'NaiveBayesCategorical'
        """
        model_type = self.get_ml_model_type_enum(model_type, **kwargs).name
        ml_trainers_and_metrics = self.ml_trainers_and_metrics(model_type, **kwargs)
        if not ml_trainers_and_metrics:
            raise ValueError(
                f"PetroVisor::ml_trainers(): unknown ML Model type: '{model_type}'!"
            )
        return ml_trainers_and_metrics["Trainers"]

    # get ML metrics
    def ml_metrics(self, model_type: Union[str, MLModelType], **kwargs) -> Any:
        """
        Get ML metrics

        Parameters
        ----------
        model_type : str, MLModelType
            ML Model type:
            'Regression', 'BinaryClassification', 'MultipleClassification', 'Clustering',
            'NaiveBayes', 'NaiveBayesCategorical'
        """
        model_type = self.get_ml_model_type_enum(model_type, **kwargs).name
        ml_trainers_and_metrics = self.ml_trainers_and_metrics(model_type, **kwargs)
        if not ml_trainers_and_metrics:
            raise ValueError(
                f"PetroVisor::ml_trainers(): unknown ML Model type: '{model_type}'!"
            )
        return ml_trainers_and_metrics["Metrics"]

    # get ML pre-training statistics
    def ml_pre_training_statistics(
        self, model_name: str, skip_pre_processing: bool = True, **kwargs
    ) -> Any:
        """
        Get ML pre-training statistics

        Parameters
        ----------
        model_name : str
            ML Model name
        skip_pre_processing : bool, default True
            Skip pre-processing of the data
        """
        route = "MLModels/PreTrainingStatistics"
        return self.post(
            route,
            data={
                "ModelName": model_name,
                "SkipPreProcessing": skip_pre_processing,
            },
            **kwargs,
        )

    # get ML post-training statistics
    def ml_post_training_statistics(
        self, model_name: str, entity: Optional[Union[str, dict]] = None, **kwargs
    ) -> Any:
        """
        Get ML post-training statistics

        Parameters
        ----------
        model_name : str
            ML Model name
        entity : str | dict | None, default None
            Entity object or Entity name
        """
        route = "MLModels/PostTrainingStatistics"
        if entity:
            request = {"ModelName": model_name}
            entity_name = ApiHelper.get_object_name(entity)
            request["EntityName"] = entity_name
            return self.post(route, data=request, **kwargs)
        return self.post(route, data={"ModelName": model_name}, **kwargs)

    # predict ML model
    def ml_predict(
        self, model_name: str, entity: Union[str, dict], data: dict, **kwargs
    ) -> Any:
        """
        Get ML post-training statistics

        Parameters
        ----------
        model_name : str
            ML Model name
        entity : str, dict
            Entity object or Entity name
        data : dict
            ML Model data
        """
        route = "MLModels/Predict"
        entity_name = ApiHelper.get_object_name(entity)
        request = {
            "ModelName": model_name,
            "EntityName": entity_name,
            "SourceData": data,
        }
        request = ApiHelper.update_dict(request, **kwargs)
        return self.post(route, data=request, **kwargs)

    # train ML model
    def ml_train(
        self,
        model_name: str,
        time_to_train: int = 5,
        complete_case_only: bool = True,
        per_entity: bool = False,
        normalization: str = "Auto",
        trainers: Optional[Union[str, List[str]]] = None,
        optimization_metric: str = "",
        validation_fraction: float = 0.1,
        cross_folds: int = 0,
        clusters: int = 0,
        test_fraction: float = 0.0,
        test_latin_hypercube: bool = True,
        entity_set: Optional[Union[str, Dict]] = None,
        scope: Optional[Union[str, Dict]] = None,
        as_request: bool = False,
        request_source: Optional[str] = "manually by user",
        activity: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Get ML post-training statistics

        Parameters
        ----------
        model_name : str
            ML Model name
        time_to_train : int, default 5
            Time to train in seconds
        complete_case_only : bool, default True
            Train only on complete case data (all features, no nulls)
        per_entity : bool, default False
            Whether training model should be produced per entity
        trainers : str, list[str], default None
            Trainer or trainers to be used. If None all available trainers will be used
        optimization_metric : str
            Optimization metrics
        cross_folds : int, default 0
            Number of cross folds
        clusters : int, default 0
            Number of clusters, only for clustering approach
        normalization : str, default 'Auto'
            Normalization type
        validation_fraction : float, default 0.1
            Validation set fraction from training data
        test_fraction : float, default 0.0
            Test set fraction from training data
        test_latin_hypercube : bool, default True
            Select test set using latin hypercube
        entity_set : str | dict, default None,
            Entity set
        scope : str | dict, default None
            Scope
        as_request : bool, default True
            Send train request
        request_source : str, default 'manually by user'
            Source of request
        activity : str
            Name of workflow activity to select best ML Model
        """
        route = "MLModels/Train"
        request = {
            "ModelName": model_name,
            "Options": {
                "EntitySet": None,
                "Scope": None,
                "TestFraction": test_fraction,
                "TestLatinHypercube": test_latin_hypercube,
                "ValidationFraction": validation_fraction,
                "OptimizationMetric": optimization_metric,
                "TimeToTrain": time_to_train,
                "NumberOfClusters": clusters,
                "NumberOfCrossValidationFolds": cross_folds,
                "TrainersToExclude": [],
                "NormalizationType": self.get_ml_normalization_type_enum(
                    normalization, **kwargs
                ).name,
                "CompleteCasesOnly": complete_case_only,
            },
            "IsModelPerEntity": per_entity,
        }
        # define trainers
        if trainers:
            # get trainers for current model type
            ml_model_type = self.ml_model_type(model_name, **kwargs)
            ml_trainers = self.ml_trainers(ml_model_type, **kwargs)
            # define trainers to exclude
            if not isinstance(trainers, list):
                trainers = ApiHelper.to_list(trainers)
            request["TrainersToExclude"] = [t for t in ml_trainers if t in trainers]
        # define training 'EntitySet'
        if entity_set:
            if isinstance(entity_set, str):
                entity_set = self.get_item(ItemType.EntitySet, entity_set, **kwargs)
            request["EntitySet"] = entity_set
        # define training 'Scope'
        if scope:
            if isinstance(scope, str):
                scope = self.get_item(ItemType.Scope, scope, **kwargs)
            request["Scope"] = scope
        # update options
        request["Options"] = ApiHelper.update_dict(request["Options"], **kwargs)
        if as_request:
            request["WorkspaceName"] = self.Workspace
            request["Source"] = request_source
            if activity:
                request["Activity"] = activity
            self.post(f"{route}/AddRequest", data=request, **kwargs)
        return self.post(route, data=request, **kwargs)

    # check whether ML service is idle
    def ml_is_service_idle(self, **kwargs) -> Any:
        """
        Is ML service idle

        Parameters
        ----------
        """
        route = "ModelTraining/Idle"
        return self.get(route, **kwargs)

    # get ML model training states
    def ml_get_model_training_states(
        self, exclude_processed: bool = False, **kwargs
    ) -> Any:
        """
        Get ML model training states

        Parameters
        ----------
        exclude_processed : bool, default False
            Exclude processed states
        """
        route = "ModelTraining"
        if exclude_processed:
            self.get(f"{route}/NoProcessed", **kwargs)
        return self.get(route, **kwargs)

    # get ML model id
    def ml_get_model_training_id(
        self, model_name_or_id: Union[str, UUID], **kwargs
    ) -> Any:
        """
        Get ML model training id

        Parameters
        ----------
        model_name_or_id : str, UUID
            ML Model name or ML Model Training Process UUID
        """
        mid = model_name_or_id
        if isinstance(model_name_or_id, str):
            ml_training_states = self.ml_get_model_training_states(
                exclude_processed=False, **kwargs
            )
            mid = None
            for state in ml_training_states:
                if state["ModelName"].lower() == model_name_or_id.lower():
                    mid = state["Id"]
        if mid is None:
            raise ValueError(
                f"PetroVisor::ml_get_model_training_id(): "
                f"couldn't find '{model_name_or_id}' in the training list!"
            )
        return ApiHelper.get_uuid(mid)

    # get ML model training state
    def ml_get_model_training_state(
        self, model_name_or_id: Union[str, UUID], **kwargs
    ) -> Any:
        """
        Get ML model training state

        Parameters
        ----------
        model_name_or_id : str, UUId
            ML Model name or ML Model Training Process UUID
        """
        route = "ModelTraining"
        uuid = self.ml_get_model_training_id(model_name_or_id, **kwargs)
        return self.get(f"{route}/{self.encode(uuid)}", **kwargs)

    # get ML model training results
    def ml_get_model_training_results(
        self, model_name_or_id: Union[str, UUID], **kwargs
    ) -> Any:
        """
        Get ML model training results

        Parameters
        ----------
        model_name_or_id : str, UUId
            ML Model name or ML Model Training Process UUID
        """
        route = "ModelTraining/Results"
        uuid = self.ml_get_model_training_id(model_name_or_id, **kwargs)
        return self.get(f"{route}/{self.encode(uuid)}", **kwargs)

    # get ML Model Type enum
    def get_ml_model_type_enum(
        self, type: Union[str, MLModelType], **kwargs
    ) -> MLModelType:
        """
        Get ML Model Type

        Parameters
        ----------
        type : str, MLModelType
            ML Model type
        """
        return Validator.get_ml_model_type_enum(type, **kwargs)

    # get ML Normalization Type enum
    def get_ml_normalization_type_enum(
        self, type: Union[str, MLNormalizationType], **kwargs
    ) -> MLNormalizationType:
        """
        Get ML Normalization Type

        Parameters
        ----------
        type : str, MLNormalizationType
            ML Normalization type
        """
        return Validator.get_ml_normalization_type_enum(type, **kwargs)
