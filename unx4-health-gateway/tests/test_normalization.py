from app.main import norm, num

def test_norm():
    assert norm("Région sociosanitaire") == "rgionsociosanitaire"

def test_num():
    assert num("1 234,5") == 1234.5
    assert num(None) is None
    assert num("abc") is None
