from jug.subcommands.status import TaskStatus
from jug.subcommands.webstatus import _format_counts, _render_page

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


def test_format_counts_failed():
    ts = TaskStatus()
    ts.failed['f'] = 7
    ts.finished['n'] = 4

    out = _format_counts(ts)
    assert '<td>7</td>' in out
    # 2 tasks + blank row + total, each with 5 counts
    assert out.count('<td>') == 4 * 5


def test_render_page_escapes():
    ts = TaskStatus()
    ts.finished['<b>name</b>'] = 1
    page = _render_page('<script>x</script>.py', '0"><script>alert(1)</script>', ts)
    assert '<script>' not in page
    assert 'content="3"' in page
    assert '&lt;b&gt;name&lt;/b&gt;' in page

    page = _render_page('jugfile.py', '10', ts)
    assert 'content="10"' in page
    page = _render_page('jugfile.py', '', ts)
    assert 'content="3"' in page
