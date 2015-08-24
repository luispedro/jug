import jug
import jug.task

jug.init('jugfile.py', 'jugfile.jugdata')
import jugfile


results = jug.task.value(jugfile.results)
with open('MPs.txt') as f:
    for mp, r in zip(f, results):
        mp = mp.strip()
        print(mp, ":    ", " ".join(r[:8]))
