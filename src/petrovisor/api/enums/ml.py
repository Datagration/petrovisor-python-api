from enum import (
    IntEnum,
    auto,
)


# PetroVisor Machine Learning model types
class MLModelType(IntEnum):
    # Regression
    Regression = 0
    # Binary classification
    BinaryClassification = auto()
    # Multiple classification
    MultipleClassification = auto()
    # Clustering
    Clustering = auto()
    # Naive Bayes
    NaiveBayes = auto()
    # Naive Bayes (categorical data)
    NaiveBayesCategorical = auto()


# PetroVisor Machine Learning normalization types
class MLNormalizationType(IntEnum):
    # ML engine will automatically pick a normalization method
    Auto = auto()
    # MinMax
    MinMax = auto()
    # MeanVariance
    MeanVariance = auto()
    # LogMeanVariance
    LogMeanVariance = auto()
    # Binning
    Binning = auto()
    # SupervisedBinning
    SupervisedBinning = auto()
    # RobustScaling
    RobustScaling = auto()
    # LpNorm
    LpNorm = auto()
    # GlobalContrast
    GlobalContrast = auto()
