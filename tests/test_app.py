# Basic check to ensure that builds flask app correctly 
def test_app_factory_sets_testing_true(app):
    assert app is not None
    assert app.config.get("TESTING") is True


# This endpoint ensures that the home page can render
def test_root_route_responds(client):
    resp = client.get("/")
    assert resp.status_code in (200, 301, 302)
