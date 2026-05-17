from jammate_engine.runtime.generate import generate_accompaniment


def test_import_smoke():
    assert callable(generate_accompaniment)
