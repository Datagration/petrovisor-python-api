from petrovisor import PetroVisor


def test_api(api: PetroVisor):
    assert api.Api
    assert api.ItemRoutes
