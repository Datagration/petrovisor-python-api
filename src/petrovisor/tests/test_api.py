from petrovisor import PetroVisor


def test_api(pv_api: PetroVisor):
    assert pv_api.Api
    assert pv_api.ItemRoutes
