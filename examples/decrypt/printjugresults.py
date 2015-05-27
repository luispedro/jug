import jug
jug.init('jugfile', 'jugdata')
import jugfile


results = jug.task.value(jugfile.fullresults)
for p, t in results:
    print("%s\n\n    Password was '%s'" % (t, p))
