import io
import os
import tempfile

import numpy as np
import pandas as pd
import pytest
from petrovisor import PetroVisor
import uuid


def test_files(api: PetroVisor):
    # Dictionary to json file tests
    d = {
        "a": 1,
        "b": "foo",
        "c": [1, 2, 3],
        "d": {
            "x": [
                "a",
                "b",
                "c",
            ],
            "y": [1, 2, 3],
        },
    }

    json_file_name = str(uuid.uuid4()) + ".json"
    api.upload_object(d, json_file_name, binary=False)

    d_loaded1 = api.get_file(json_file_name, format="json")
    assert d == d_loaded1

    d_loaded2 = api.get_object(json_file_name, binary=False)
    assert d == d_loaded2

    api.delete_file(json_file_name)

    # DataFrame tests
    df = pd.DataFrame(
        np.random.uniform(0, 1, size=(int(1e3), 6)), columns=list("ABCDEF")
    )

    # DataFrame to csv tests
    dataframe_csv_file_name = str(uuid.uuid4()) + ".csv"
    api.upload_object(df, dataframe_csv_file_name)

    df_csv_loaded = api.get_object(dataframe_csv_file_name)
    # assert df.equals(df_csv_loaded)
    assert df.shape == df_csv_loaded.shape

    api.delete_file(dataframe_csv_file_name)

    # DataFrame to excel test
    dataframe_excel_file_name = str(uuid.uuid4()) + ".xlsx"
    api.upload_object(df, dataframe_excel_file_name)

    df_excel_loaded = api.get_object(dataframe_excel_file_name)
    # assert df.equals(df_excel_loaded)
    assert df.shape == df_excel_loaded.shape

    api.delete_file(dataframe_excel_file_name)

    # DataFrame to pickle test
    dataframe_pickle_file_name = str(uuid.uuid4()) + ".pkl"
    api.upload_object(df, dataframe_pickle_file_name)

    df_pickle_loaded = api.get_object(dataframe_pickle_file_name)
    assert df.equals(df_pickle_loaded)

    api.delete_file(dataframe_pickle_file_name)


# ============================================================================
# read_dataframe_from_file / read_dataframe_from_bytes
# ============================================================================


def test_read_dataframe_from_file_csv(api):
    df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df_original.to_csv(f.name, index=False)
        temp_file = f.name
    try:
        df_read = api.read_dataframe_from_file(temp_file)
        assert isinstance(df_read, pd.DataFrame)
        assert list(df_read.columns) == ["A", "B"]
        assert len(df_read) == 3
        assert df_read["A"].tolist() == [1, 2, 3]
    finally:
        os.unlink(temp_file)


def test_read_dataframe_from_file_tsv(api):
    df_original = pd.DataFrame({"X": [10, 20], "Y": [30, 40]})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        df_original.to_csv(f.name, index=False, sep="\t")
        temp_file = f.name
    try:
        df_read = api.read_dataframe_from_file(temp_file, delimiter="\t")
        assert isinstance(df_read, pd.DataFrame)
        assert list(df_read.columns) == ["X", "Y"]
        assert len(df_read) == 2
    finally:
        os.unlink(temp_file)


def test_read_dataframe_from_file_excel(api):
    df_original = pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [25, 30]})
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        df_original.to_excel(f.name, index=False, engine="openpyxl")
        temp_file = f.name
    try:
        df_read = api.read_dataframe_from_file(temp_file)
        assert isinstance(df_read, pd.DataFrame)
        assert list(df_read.columns) == ["Name", "Age"]
        assert len(df_read) == 2
    finally:
        os.unlink(temp_file)


def test_read_dataframe_from_file_parquet(api):
    df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4.5, 5.5, 6.5]})
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        df_original.to_parquet(f.name)
        temp_file = f.name
    try:
        df_read = api.read_dataframe_from_file(temp_file)
        assert isinstance(df_read, pd.DataFrame)
        assert list(df_read.columns) == ["A", "B"]
        assert len(df_read) == 3
    finally:
        os.unlink(temp_file)


def test_read_dataframe_from_file_unsupported(api):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_file = f.name
    try:
        with pytest.raises(ValueError, match="Unsupported file extension"):
            api.read_dataframe_from_file(temp_file)
    finally:
        os.unlink(temp_file)


def test_read_dataframe_from_file_polars(api):
    try:
        import polars as pl

        df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df_original.to_csv(f.name, index=False)
            temp_file = f.name
        try:
            df_read = api.read_dataframe_from_file(temp_file, backend="polars")
            assert isinstance(df_read, pl.DataFrame)
            assert df_read.columns == ["A", "B"]
            assert len(df_read) == 3
        finally:
            os.unlink(temp_file)
    except ImportError:
        pytest.skip("polars not installed")


def test_read_dataframe_from_bytes_csv(api):
    df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    csv_bytes = df_original.to_csv(index=False).encode("utf-8")
    df_read = api.read_dataframe_from_bytes(csv_bytes, "data.csv")
    assert isinstance(df_read, pd.DataFrame)
    assert list(df_read.columns) == ["A", "B"]
    assert len(df_read) == 3


def test_read_dataframe_from_bytes_excel(api):
    df_original = pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [25, 30]})
    buffer = io.BytesIO()
    df_original.to_excel(buffer, index=False, engine="openpyxl")
    excel_bytes = buffer.getvalue()
    df_read = api.read_dataframe_from_bytes(excel_bytes, "data.xlsx")
    assert isinstance(df_read, pd.DataFrame)
    assert list(df_read.columns) == ["Name", "Age"]
    assert len(df_read) == 2


def test_read_dataframe_from_bytes_parquet(api):
    df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4.5, 5.5, 6.5]})
    buffer = io.BytesIO()
    df_original.to_parquet(buffer)
    parquet_bytes = buffer.getvalue()
    df_read = api.read_dataframe_from_bytes(parquet_bytes, "data.parquet")
    assert isinstance(df_read, pd.DataFrame)
    assert list(df_read.columns) == ["A", "B"]
    assert len(df_read) == 3


def test_read_dataframe_from_bytes_unsupported(api):
    with pytest.raises(ValueError, match="Unsupported file extension"):
        api.read_dataframe_from_bytes(b"some data", "data.json")


def test_read_dataframe_from_bytes_polars(api):
    try:
        import polars as pl

        df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        csv_bytes = df_original.to_csv(index=False).encode("utf-8")
        df_read = api.read_dataframe_from_bytes(csv_bytes, "data.csv", backend="polars")
        assert isinstance(df_read, pl.DataFrame)
        assert df_read.columns == ["A", "B"]
        assert len(df_read) == 3
    except ImportError:
        pytest.skip("polars not installed")


# ============================================================================
# get_object with DataFrame formats
# ============================================================================


def test_get_object_csv_dataframe(api):
    df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    csv_bytes = df_original.to_csv(index=False).encode("utf-8")
    api.upload_file(io.BytesIO(csv_bytes), name="test_get_object.csv")
    try:
        df_downloaded = api.get_object("test_get_object.csv")
        assert isinstance(df_downloaded, pd.DataFrame)
        assert list(df_downloaded.columns) == ["A", "B"]
        assert len(df_downloaded) == 3
        assert df_downloaded["A"].tolist() == [1, 2, 3]
    finally:
        api.delete_file("test_get_object.csv")


def test_get_object_excel_dataframe(api):
    df_original = pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [25, 30]})
    buffer = io.BytesIO()
    df_original.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    api.upload_file(buffer, name="test_get_object.xlsx")
    try:
        df_downloaded = api.get_object("test_get_object.xlsx")
        assert isinstance(df_downloaded, pd.DataFrame)
        assert list(df_downloaded.columns) == ["Name", "Age"]
        assert len(df_downloaded) == 2
    finally:
        api.delete_file("test_get_object.xlsx")


def test_get_object_parquet_dataframe(api):
    df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4.5, 5.5, 6.5]})
    buffer = io.BytesIO()
    df_original.to_parquet(buffer)
    buffer.seek(0)
    api.upload_file(buffer, name="test_get_object.parquet")
    try:
        df_downloaded = api.get_object("test_get_object.parquet")
        assert isinstance(df_downloaded, pd.DataFrame)
        assert list(df_downloaded.columns) == ["A", "B"]
        assert len(df_downloaded) == 3
    finally:
        api.delete_file("test_get_object.parquet")


def test_get_object_dataframe_with_backend(api):
    try:
        import polars as pl

        df_original = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        csv_bytes = df_original.to_csv(index=False).encode("utf-8")
        api.upload_file(io.BytesIO(csv_bytes), name="test_get_object_polars.csv")
        try:
            df_downloaded = api.get_object(
                "test_get_object_polars.csv", backend="polars"
            )
            assert isinstance(df_downloaded, pl.DataFrame)
            assert df_downloaded.columns == ["A", "B"]
            assert len(df_downloaded) == 3
        finally:
            api.delete_file("test_get_object_polars.csv")
    except ImportError:
        pytest.skip("polars not installed")


# ============================================================================
# convert_dataframe_to_file_object
# ============================================================================


def test_convert_dataframe_to_file_object_pandas_csv(api):
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    file_obj = api.convert_dataframe_to_file_object(df, "test.csv")
    assert isinstance(file_obj, io.BytesIO)
    assert file_obj.name == "test.csv"
    file_obj.seek(0)
    df_read = pd.read_csv(file_obj)
    assert list(df_read.columns) == ["A", "B"]
    assert len(df_read) == 3


def test_convert_dataframe_to_file_object_pandas_excel(api):
    df = pd.DataFrame({"Name": ["Alice", "Bob"], "Age": [25, 30]})
    file_obj = api.convert_dataframe_to_file_object(df, "test.xlsx")
    assert isinstance(file_obj, io.BytesIO)
    assert file_obj.name == "test.xlsx"
    file_obj.seek(0)
    df_read = pd.read_excel(file_obj, engine="openpyxl")
    assert list(df_read.columns) == ["Name", "Age"]
    assert len(df_read) == 2


def test_convert_dataframe_to_file_object_pandas_pickle(api):
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    file_obj = api.convert_dataframe_to_file_object(df, "test.pkl")
    assert isinstance(file_obj, io.BytesIO)
    assert file_obj.name == "test.pkl"
    file_obj.seek(0)
    df_read = pd.read_pickle(file_obj, compression="gzip")
    assert list(df_read.columns) == ["A", "B"]
    assert len(df_read) == 3


def test_convert_dataframe_to_file_object_polars_csv(api):
    try:
        import polars as pl

        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        file_obj = api.convert_dataframe_to_file_object(df, "test.csv")
        assert isinstance(file_obj, io.BytesIO)
        assert file_obj.name == "test.csv"
        file_obj.seek(0)
        df_read = pd.read_csv(file_obj)
        assert list(df_read.columns) == ["A", "B"]
        assert len(df_read) == 3
    except ImportError:
        pytest.skip("polars not installed")


def test_convert_dataframe_to_file_object_polars_excel(api):
    try:
        import polars as pl

        df = pl.DataFrame({"Name": ["Alice", "Bob"], "Age": [25, 30]})
        file_obj = api.convert_dataframe_to_file_object(df, "test.xlsx")
        assert isinstance(file_obj, io.BytesIO)
        assert file_obj.name == "test.xlsx"
        file_obj.seek(0)
        df_read = pd.read_excel(file_obj, engine="openpyxl")
        assert list(df_read.columns) == ["Name", "Age"]
        assert len(df_read) == 2
    except ImportError:
        pytest.skip("polars not installed")


def test_convert_dataframe_to_file_object_with_backend_param(api):
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    file_obj = api.convert_dataframe_to_file_object(df, "test.csv", backend="pandas")
    assert isinstance(file_obj, io.BytesIO)
    assert file_obj.name == "test.csv"
    file_obj.seek(0)
    df_read = pd.read_csv(file_obj)
    assert list(df_read.columns) == ["A", "B"]
    assert len(df_read) == 3


def test_convert_dataframe_to_file_object_with_date_format(api):
    df = pd.DataFrame(
        {"Date": pd.date_range("2024-01-01", periods=3), "Value": [10, 20, 30]}
    )
    file_obj = api.convert_dataframe_to_file_object(
        df, "test.csv", date_format="%Y-%m-%dT%H:%M:%S.%fZ"
    )
    assert isinstance(file_obj, io.BytesIO)
    file_obj.seek(0)
    content = file_obj.read().decode("utf-8")
    assert "2024-01-01T00:00:00" in content


def test_convert_dataframe_to_file_object_non_dataframe(api):
    not_a_df = "just a string"
    result = api.convert_dataframe_to_file_object(not_a_df, "test.csv")
    assert result == "just a string"
