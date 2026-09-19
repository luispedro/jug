import jug
jug.init('jugfile.py', 'jugfile.jugdata')
import jugfile


results = jug.task.value(jugfile.fullresults)
for p, t in results:
    print(f"{t}\n\n    Password was '{p}'")
