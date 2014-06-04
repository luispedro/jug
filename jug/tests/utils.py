def simple_execute():
    from jug.jug import execution_loop
    from jug.task import alltasks
    from jug.options import default_options
    execution_loop(alltasks, default_options)
