import argparse

from creosote.config import CustomAppendAction


def test_custom_append_action_none_default():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--foo", dest="foo", action=CustomAppendAction)
    args = parser.parse_args(["-f", "1", "-f", "2"])
    assert args.foo == ["1", "2"]


def test_custom_append_action_list_default():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--foo", dest="foo", action=CustomAppendAction, default=["3"]
    )
    args = parser.parse_args([])
    assert args.foo == ["3"]


def test_custom_append_action_list_default_override():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--foo", dest="foo", action=CustomAppendAction, default=["3"]
    )
    args = parser.parse_args(["-f", "1", "-f", "2"])
    assert args.foo == ["1", "2"]


def test_custom_append_action_list_set_defaults():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--foo", dest="foo", action=CustomAppendAction)
    parser.set_defaults(foo=["3"])
    args = parser.parse_args([])
    assert args.foo == ["3"]


def test_custom_append_action_list_set_defaults_override():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--foo", dest="foo", action=CustomAppendAction)
    parser.set_defaults(foo=["3"])
    args = parser.parse_args(["-f", "1", "-f", "2"])
    assert args.foo == ["1", "2"]
