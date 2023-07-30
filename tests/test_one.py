import sys


def test_sys_path():
    print(sys.path)
    assert True


def test_passing():
    assert (1, 2, 3) == (1, 2, 3)


def test_failing1():
    assert (1, 2, 3) != (3, 2, 1)


def test_failing2():
    assert 1 in [1, 2, 3]


def test_failing3():
    a = 1
    b = 2
    assert a < b


def test_failing4():
    assert "fizz" in "fizzbuzz"
