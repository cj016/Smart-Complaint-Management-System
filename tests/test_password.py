from app.models import User


def test_hash_is_not_plain_text():
    u = User(name="A", email="a@x.com")
    u.set_password("Secret123!")
    assert u.password_hash != "Secret123!"


def test_same_password_gives_different_hashes():
    u1 = User(name="A", email="a@x.com")
    u2 = User(name="B", email="b@x.com")
    u1.set_password("Secret123!")
    u2.set_password("Secret123!")
    assert u1.password_hash != u2.password_hash


def test_check_password():
    u = User(name="A", email="a@x.com")
    u.set_password("Secret123!")
    assert u.check_password("Secret123!")
    assert not u.check_password("wrong")