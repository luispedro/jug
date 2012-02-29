from jug.subcommands.webstatus import _format_counts

def test_format_counts():
    assert len(_format_counts({'n': 0}, {'n': 1}, {'n': 2}, {'n':3}))
    assert len(_format_counts(
                    {'n': 0, 'n2': 1 },
                    {'n': 1, 'n2': 0 },
                    {'n': 2, 'n2': 3 },
                    {'n': 3, 'n2': 4 }
                    ))
