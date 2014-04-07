from sys import exit
def exit_if_file_exists(fname):
    '''Before each task execute, check if file exists. If so, exit.

    Note that a check is only performed before a Task is execute. Thus, jug
    will not exit immediately if it is executing another long-running task.

    Parameters
    ----------
    fname : str
        path to check
    '''
    from jug import hooks
    def check_file(_t):
        from os import path
        if path.exists(fname):
            exit(0)
    hooks.register_hook('execute.task-pre-execute', check_file)

def exit_when_true(f, function_takes_Task=False):
    '''Generic exit check.
    
    After each task, call function ``f`` and exit if it return true.

    Parameters
    ----------
    f : function
        Function to call
    function_takes_Task : boolean, optional
        Whether to call the function with the task just executed (default: False)
    '''

    from jug import hooks
    if not function_takes_Task:
        f = lambda t : f()
    def exit_when(t):
        if f(t):
           exit(0)
    hooks.register_hook('execute.task-executed1', exit_when)

def exit_after_n_tasks(n):
    '''Exit after a specific number of tasks have been executed
    
    Parameters
    ----------
    n : int
        Number of tasks to execute
    '''
    from jug import hooks
    # In newer Python, we could use nonlocal, but this is a work around
    # (http://stackoverflow.com/questions/9603278/is-there-something-like-nonlocal-in-python-3/9603491#9603491)
    executed = [0]
    def exit_after(_t):
        executed[0] += 1
        if executed[0] > n:
           exit(0)
    hooks.register_hook('execute.task-executed1', exit_after)

def exit_after_time(hours=0, minutes=0, seconds=0):
    '''Exit after a specific number of tasks have been executed

    Note that this only checks the time **after each task has finished
    executing**. Thus if you are using this to limit the amount of time each
    process takes, make sure to specify a lower limit than what is needed.

    Parameters
    ----------
    hours : number, optional
    minutes : number, optional
    seconds : number, optional
    '''
    from jug import hooks
    from time import time
    deadline = time()
    deadline += seconds
    deadline += 60*minutes
    deadline += 60*60*hours

    def check_time(_t):
        if time() >= deadline:
            exit(0)
    hooks.register_hook('execute.task-executed1', check_time)

