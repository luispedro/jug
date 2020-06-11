from jug import TaskGenerator

@TaskGenerator
def double(x):
    return 2*x

@TaskGenerator
def create_result(r, oname):
    with open(oname, 'wt') as out:
        out.write('Result is {}\n'.format(r))

two = double(1)
four = double(2)
eight = double(four)
sixteen = double(eight)

create_result(sixteen, 'test-result.txt')



