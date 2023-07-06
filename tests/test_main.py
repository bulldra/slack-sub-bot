import main


def test_main():
    app = main.create_app()
    app.test_client().post("/", data={"product": "MVNO携帯電話"})
    assert True
