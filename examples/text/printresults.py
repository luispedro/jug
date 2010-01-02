import jug
import jug.task

jug.init('jugfile', 'jugdata')
import jugfile

results = jug.task.value(jugfile.results)
for mp,r in zip(file('MPs.txt'), results):
    mp = mp.strip()
    print mp, ":    ", " ".join(r[:8])
