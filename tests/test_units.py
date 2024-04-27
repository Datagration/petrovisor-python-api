import numpy as np
import pandas as pd
from petrovisor import PetroVisor


def test_units(api: PetroVisor):

    value = api.convert_units(3, "cm", "m")
    assert value == 0.03

    values = api.convert_units([1, 2, 4, 5], "cm", "m")
    assert values == [0.01, 0.02, 0.04, 0.05]

    values = api.convert_units(np.asarray([1, 2, 4, 5]), "cm", "m")
    assert values == [0.01, 0.02, 0.04, 0.05]

    values = api.convert_units(pd.Series([1, 2, 4, 5]), "cm", "m")
    assert values == [0.01, 0.02, 0.04, 0.05]
