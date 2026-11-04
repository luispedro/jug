from jug import TaskGenerator, barrier

@TaskGenerator
def before(x):
    return x + 1

@TaskGenerator
def after(x):
    return 2 * x

@TaskGenerator
def after_skipped(x):
    return x

vals = [before(i) for i in range(4)]
barrier()
# These tasks are only seen once the jugfile is re-loaded
doubled = [after(v) for v in vals]
skipped = [after_skipped(v) for v in vals]
