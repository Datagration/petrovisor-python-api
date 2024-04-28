from typing import Union

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.enums.internal_dtypes import (
    SignalType,
    AggregationType,
)
from petrovisor.api.enums.ml import (
    MLModelType,
    MLNormalizationType,
)
from petrovisor.api.enums.increments import (
    TimeIncrement,
    DepthIncrement,
)


class Validator:

    # get valid signal type name
    @staticmethod
    def get_signal_type_enum(
        signal_type: Union[str, SignalType], **kwargs
    ) -> SignalType:
        """
        Get SignalType enum

        Parameters
        ----------
        signal_type : str, SignalType
            Signal type
        """
        if isinstance(signal_type, SignalType):
            return signal_type
        # prepare name for comparison
        signal_type = ApiHelper.get_comparison_string(signal_type, **kwargs)
        if signal_type in ("static", "staticnumeric"):
            return SignalType.Static
        elif signal_type in ("time", "timenumeric", "timedependent"):
            return SignalType.TimeDependent
        elif signal_type in ("depth", "depthnumeric", "depthdependent"):
            return SignalType.DepthDependent
        elif signal_type in ("string", "staticstring"):
            return SignalType.String
        elif signal_type in ("stringtime", "timestring", "stringtimedependent"):
            return SignalType.StringTimeDependent
        elif signal_type in ("stringdepth", "depthstring", "stringdepthdependent"):
            return SignalType.StringDepthDependent
        elif signal_type in ("pvt", "pvtnumeric"):
            return SignalType.PVT
        raise ValueError(
            f"PetroVisor::get_signal_type_enum(): "
            f"unknown data type: '{signal_type}'! "
            f"Should be one of: {[t.name for t in SignalType]}"
        )

    # get time increment name
    @staticmethod
    def get_time_increment_enum(
        increment_type: Union[str, TimeIncrement], **kwargs
    ) -> TimeIncrement:
        """
        Get TimeIncrement enum

        Parameters
        ----------
        increment_type : str, TimeIncrement
            Increment
        """
        if isinstance(increment_type, TimeIncrement):
            return increment_type
        # prepare name for comparison
        increment_type = ApiHelper.get_comparison_string(increment_type, **kwargs)
        if increment_type in ("hourly", "h", "hr", "hour", "1h", "1hr", "1hour"):
            return TimeIncrement.Hourly
        elif increment_type in ("daily", "d", "day", "1d", "1day"):
            return TimeIncrement.Daily
        elif increment_type in ("monthly", "m", "month", "1m", "1month"):
            return TimeIncrement.Monthly
        elif increment_type in ("yearly", "y", "year", "1y", "1year"):
            return TimeIncrement.Yearly
        elif increment_type in ("quarterly", "q", "3m", "3month", "quarter"):
            return TimeIncrement.Quarterly
        elif increment_type in ("everyminute", "min", "minute", "1min", "1minute"):
            return TimeIncrement.EveryMinute
        elif increment_type in (
            "everysecond",
            "s",
            "sec",
            "second",
            "1s",
            "1sec",
            "1second",
        ):
            return TimeIncrement.EverySecond
        elif increment_type in ("everyfiveminute", "5min", "5minutes"):
            return TimeIncrement.EveryFiveMinutes
        elif increment_type in ("everyfifteenminutes", "15min", "15minutes"):
            return TimeIncrement.EveryFifteenMinutes
        raise ValueError(
            f"PetroVisor::get_time_increment_enum(): "
            f"unknown time increment: '{increment_type}'! "
            f"Should be one of: {[inc.name for inc in TimeIncrement]}"
        )

    # get depth increment name
    @staticmethod
    def get_depth_increment_enum(
        increment_type: Union[str, DepthIncrement], **kwargs
    ) -> DepthIncrement:
        """
        Get DepthIncrement enum

        Parameters
        ----------
        increment_type : str, DepthIncrement
            Increment
        """
        if isinstance(increment_type, DepthIncrement):
            return increment_type
        # prepare name for comparison
        increment_type = ApiHelper.get_comparison_string(increment_type, **kwargs)
        if increment_type in ("meter", "m", "1meter", "1m"):
            return DepthIncrement.Meter
        elif increment_type in (
            "halfmeter",
            "halfm",
            ".5meter",
            ".5m",
            "0.5meter",
            "0.5m",
        ):
            return DepthIncrement.HalfMeter
        elif increment_type in ("tenthmeter", ".1meter", ".1m", "0.1meter", "0.1m"):
            return DepthIncrement.TenthMeter
        elif increment_type in (
            "eightmeter",
            ".125meter",
            ".125m",
            "0.125meter",
            "0.125m",
        ):
            return DepthIncrement.EighthMeter
        elif increment_type in ("foot", "ft", "1foot", "1ft"):
            return DepthIncrement.Foot
        elif increment_type in (
            "halffoot",
            "halfft",
            ".5foot",
            ".5feet",
            ".5ft",
            "0.5foot",
            "0.5feet",
            "0.5ft",
        ):
            return DepthIncrement.HalfFoot
        raise ValueError(
            f"PetroVisor::get_depth_increment_enum(): "
            f"unknown depth increment: '{increment_type}'! "
            f"Should be one of: {[inc.name for inc in DepthIncrement]}"
        )

    # get valid aggregation type name
    @staticmethod
    def get_aggregation_type_enum(
        aggregation_type: Union[str, AggregationType], **kwargs
    ) -> AggregationType:
        """
        Get AggregationType enum

        Parameters
        ----------
        aggregation_type : str | AggregationType
            Aggregation type
        """
        if isinstance(aggregation_type, AggregationType):
            return aggregation_type
        # prepare name for comparison
        aggregation_type = ApiHelper.get_comparison_string(aggregation_type, **kwargs)
        if aggregation_type in ("sum", "concatenate", "concat"):
            return AggregationType.Sum
        elif aggregation_type in (
            "average",
            "avg",
            "mean",
        ):
            return AggregationType.Average
        elif aggregation_type in ("max", "maximum", "longest", "largest", "biggest"):
            return AggregationType.Max
        elif aggregation_type in ("min", "minimum", "shortest", "smallest"):
            return AggregationType.Min
        elif aggregation_type in ("first",):
            return AggregationType.First
        elif aggregation_type in ("last",):
            return AggregationType.Last
        elif aggregation_type in ("count",):
            return AggregationType.Count
        elif aggregation_type in (
            "none",
            "no",
            "noaggregation",
            "noagg",
        ):
            return AggregationType.NoAggregation
        elif aggregation_type in ("median",):
            return AggregationType.Median
        elif aggregation_type in ("mode",):
            return AggregationType.Mode
        elif aggregation_type in (
            "standarddeviation",
            "std",
        ):
            return AggregationType.StandardDeviation
        elif aggregation_type in (
            "variance",
            "var",
        ):
            return AggregationType.Variance
        elif aggregation_type in ("percentile",):
            return AggregationType.Percentile
        elif aggregation_type in ("range",):
            return AggregationType.Range
        raise ValueError(
            f"PetroVisor::get_aggregation_type_enum(): "
            f"unknown data type: '{aggregation_type}'! "
            f"Should be one of: {[t.name for t in AggregationType]}"
        )

    # get ML Model Type enum
    @staticmethod
    def get_ml_model_type_enum(type: Union[str, MLModelType], **kwargs) -> MLModelType:
        """
        Get ML Model Type

        Parameters
        ----------
        type : str, MLModelType
            ML Model type
        """
        if isinstance(type, MLModelType):
            return type
        # prepare name for comparison
        type = ApiHelper.get_comparison_string(type, **kwargs)
        if type in ("regression", "reg"):
            return MLModelType.Regression
        elif type in ("binaryclassification", "binaryclass", "binclass", "bin"):
            return MLModelType.BinaryClassification
        elif type in (
            "multipleclassification",
            "multiclassification",
            "multipleclass",
            "multiclass",
            "multiple",
            "multi",
        ):
            return MLModelType.MultipleClassification
        elif type in ("clustering", "cluster"):
            return MLModelType.Clustering
        elif type in ("naivebayes", "bayes"):
            return MLModelType.NaiveBayes
        elif type in ("naivebayescategorical", "bayescategorical"):
            return MLModelType.NaiveBayesCategorical
        raise ValueError(
            f"PetroVisor::get_ml_model_enum(): "
            f"unknown data type: '{type}'! "
            f"Should be one of: {[t.name for t in MLModelType]}"
        )

    # get ML Normalization Type enum
    @staticmethod
    def get_ml_normalization_type_enum(
        type: Union[str, MLNormalizationType], **kwargs
    ) -> MLNormalizationType:
        """
        Get ML Normalization Type

        Parameters
        ----------
        type : str, MLNormalizationType
            ML Normalization type
        """
        if isinstance(type, MLNormalizationType):
            return type
        # prepare name for comparison
        type = ApiHelper.get_comparison_string(type, **kwargs)
        if type in ("auto", "automatic"):
            return MLNormalizationType.Auto
        elif type in ("minmax",):
            return MLNormalizationType.MinMax
        elif type in ("meanvariance", "meanvar"):
            return MLNormalizationType.MeanVariance
        elif type in ("logmeanvariance", "logmeanvar"):
            return MLNormalizationType.LogMeanVariance
        elif type in ("binning", "bin"):
            return MLNormalizationType.Binning
        elif type in ("supervisedbinning", "supervisedbin", "superbin"):
            return MLNormalizationType.SupervisedBinning
        elif type in ("robustscaling", "robust"):
            return MLNormalizationType.RobustScaling
        elif type in ("lpnorm", "lp"):
            return MLNormalizationType.LpNorm
        elif type in ("globalcontrast", "contrast"):
            return MLNormalizationType.GlobalContrast
        raise ValueError(
            f"PetroVisor::get_ml_normalization_enum(): "
            f"unknown data type: '{type}'! "
            f"Should be one of: {[t.name for t in MLNormalizationType]}"
        )
