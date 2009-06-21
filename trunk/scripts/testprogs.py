import os
import sys

def do_cmd(cmd):
    print '\n\n', cmd, '\n'
    assert os.system(cmd) == 0

files = ['neural1.py', 'mask_alg.py', 'mandelbrot.py', 'sudoku3.py', 'pystone.py', 'nbody.py', 'genetic.py', 'richards.py', 'voronoi.py', 'oliva2.py', 'sieve.py', 'linalg.py', 'brainfuck.py', 'pisang.py', 'sudoku2.py', 'life.py', 'sudoku1.py', 'othello.py', 'chess.py', 'pygmy.py', 'tictactoe.py', 'yopyra.py', 'dijkstra.py', 'amaze.py', 'neural2.py', 'mastermind.py', 'rdb.py', 'TonyJpegDecoder.py', 'mao.py', 'sudo.py', 'mastermind2.py', 'minilight.py', 'circle.py', 'voronoi2'] # XXX fysphun

if sys.platform != 'win32':
    files.extend(['msp_ss.py'])

print 'examples: %d' % len(set(files))

# cmd-line options

print '*** cmd-line options:'

do_cmd('shedskin -b othello')
do_cmd('make run')
do_cmd('shedskin -w othello')
do_cmd('make run')

# ss-progs

print '*** examples:'

if sys.platform == 'win32':
    os.system('copy lib\*.* ..\lib')
else:
    os.system('cp lib/* ../lib')

for (i, file) in enumerate(files):
    print '*** test: %s %d' % (file, i)

    options = ''
    if file == 'minilight.py':
        options += ' -r'

    do_cmd('shedskin %s %s' % (options.strip(), file)) 
    if file in ['mastermind.py', 'rdb.py', 'TonyJpegDecoder.py', 'voronoi2']: 
        do_cmd('make')
    else:
        do_cmd('make run')
    do_cmd('shedskin -e %s %s' % (options.strip(), file))
    do_cmd('make')

