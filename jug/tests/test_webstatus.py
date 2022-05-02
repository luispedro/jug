from jug.subcommands.status import TaskStatus
from jug.subcommands.webstatus import _format_counts

def test_format_counts():

    ts = TaskStatus()
    ts.waiting = {'n': 1}
    ts.ready = {'n': 2}
    ts.running = {'n': 3}
    ts.finished = {'n': 4}

    assert len(_format_counts(ts))

    ts.waiting = {'n': 1, 'n1': 0}
    ts.ready = {'n': 2, 'n1': 1}
    ts.running = {'n': 3, 'n1': 3}
    ts.finished = {'n': 4, 'n1': 2}

    assert len(_format_counts(ts))
