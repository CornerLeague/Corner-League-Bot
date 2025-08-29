from libs.api.response import ApiResponse


def test_api_response_instantiation():
    resp = ApiResponse(success=True, data={"foo": "bar"})
    assert resp.success is True
    assert resp.data == {"foo": "bar"}
