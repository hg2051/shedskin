# Shed Skin 0.9.4 (16-6-2013) #

- type inference fix (concluding dynamic types too soon), which allowed a 5,000+ sloc program to compile

- new examples (now 75 in total!):

> - wolfenstein-like engine (Mariano Lambir, found by Ernesto Ferro)

> - 3D convex hull (Michel Anders)

> - C image processing library (Paul Haeberli)

- several large code cleanups:

> - simplified module lookup (Ernesto Ferro)

> - split up shared.py (Ernesto Ferro)

> - remove setgx/getgx functions (Ernesto Ferro)

> - limit setmv/getmv functions to graph.py

> - better follow python style guide, rename classes in shared.py (Ernesto Ferro)

> - move most cpp-specific code to cpp.py (Ernesto Ferro)

> - removed copy_and struct_ modules (Ernesto Ferro)

- fix for passing long integers to extension module (Ernesto Ferro)

- fixes for pickling (triggered by Ernesto Ferro)

- fix for when iteration variable is declared global (reported by Alex Susu)

- fix for method names equal to certain python builtins

- fix for lost types in certain virtual functions

- fix for default args and inheritance

- fix for block quotes (#{ and #}, triggered by Paul Haeberli)

- fix for unpacking negative integers (reported by RealGrandrew)

- fix corner case: removing last element of list while iterating over it.. (reported by akatopaz)

- random.vonmisesvariate changed in python 2.7.4

- added tests for most errors/warnings

- make `__to_py__` method virtual (triggered by Ernesto Ferro)

- partial implementation of `__del__` (triggered by Paul Haeberli)

- parallelize tests (Ernesto Ferro)


# Shed Skin 0.9.3 (9-1-2013) #

- much improved support for arbitrary code at the class level

- support select.select (UNIX, danny milosavljevic)

- greatly optimized creating/extending arrays (triggered by piotr tarsa)

- new example programs (now 72 in total):

> - pygasus, a NES emulator (about 1500 lines, Maciek "Mistrall" Żuk)

> - timsort sorting algorithm (about 650 lines, dan stromberg)

> - a conflict-driven satisfiability solver (thomas leonard)

> - TarsaLZP, a data compression algorithm (about 900 lines, piotr tarsa)

> - minpng, a minimal uncompressed PNG encoder

- fix generator expression problem (triggered by piotr tarsa)

- improve string formatting and null chars (reported by jorik blaas)

- new -g option to disable GC warnings

- remaining fixes for GCC 4.7 (help from thomas spura, mos4567)

- avoid crash on non-existant attribute (reported by danny milosavljevic)

- improve include file ordering (triggered by danny)

- avoid trouble by adding main module to module cache (reported by badamomike)

- update random.expovariate to 2.7 behaviour, finally fixing test 172

- add a few warnings for broken python code

- fix for when module exists in multiple libdirs (shedskin -L)

- fix annotation crash (shedskin -a)

# Shed Skin 0.9.2 (5-5-2012) #

- new example: stereo computer vision (james coughlan)

- new example: rubik's cube solver (author unknown)

- new example: thistlethwaite rubik's cube solver (stephan pochmann)

- optimized array indexing, slicing (reported by francesco frassinelli)

- optimized list.pop without arguments (reported by ecir hana)

- optimized bool(list) (idem)

- os.popen2 fix (danny milosavljevic)

- support `float.is_integer` (reported by tony veijalainen)

- use 64-bit arithmetic in `pow` internally (idem)

- `set.__ior__` etc. modeling fix (reported by william edwards)

- model `__eq__` in methods `__contains__`, `index`, `count`, `remove` (reported  by tony veijalainen)

- fix for skipped calls in generator (reported by francesco frassinelli)

- avoid abstract `object` type, to avoid hiding warnings (reported by wilkin ng)

- avoid multiple definitions for rich comparison code in header file (idem)

- look in correct context for inherited methods (idem)

- some fixes for GCC 4.7 (reported by mos4567)

# Shed Skin 0.9.1 (15-01-2012) #

- new -L option to add library directories (Artem Egorkine)

- support /etc/shedskin/FLAGS, /usr/share/shedskin/lib (triggered by Paul Boddie)

- support enumerate 'start' argument

- itertools.product optimization (triggered by lesshaste)

- str.join and str non-equality optimization (triggered by lesshaste)

- new example: hq2x image scaling

- fix for itertools.izip (Jérémie Roquet)

- several fixes for MSVC (Liu Zhenhai)

- fix os.listdir crash (Pierre-Marie de Rodat)

- annotation fix (William Edwards)

- fix for 'not a < b < c' (François Boutines)

- os.popen2 improvement (triggered by Danny Milosavljevic)

- improved extmod warnings (triggered by Paul Boddie)

- sys.exit improvements (reported by rodseth)

- added missing class qualifier/include statement

- fix for ConfigParser model (reported by Danny Milosavljevic)

# Shed Skin 0.9 (10-09-2011) #

- major type inference scalability improvements (c64 emulator 10 times faster!)

- support for 'mmap' module (francois boutines)

- support for 'binascii' module (fahrzin hemmati)

- support for 'colorsys' module (tony veijalainen)

- greatly improved file I/O performance (francois)

- massive optimization for complex numbers (copy-by-value)

- optimized 'for .., .. in somedict.iteritems()'

- 6 new example programs (now 63 in total!):

> - natural language parser (andreas van cranenburgh)

> - sokoban (uses array, collections.deque)

> - connect-4

> - interactive mandelbrot (tony veijalainen)

> - dancing links sudoku solver

> - K-means++ clustering

- c64 emulator example now without glitches for international karate

- fixes for 'universal mode' (francois)

- only print tracebacks for uncaught exceptions (shedskin -x; joris van zwieten)

- some further exception handling cleanups

- add set.isdisjoint, sys.maxsize (brent pedersen)

- several set methods now take multiple arguments (brent)

- string equality optimization (francois)

- fix for string/array equality and \0 (francois)

- improved support for overloading comparison operators

- several inheritance fixes (thanks to test case by jason ye)

- improvements for working with 'incompatible' types (e.g., `[[]] == [[1]]`)

- implementation of builtins split up into separate files (triggered by francois)

- cleaned up GCC warnings for builtins (triggered by francois)

- support 'id' builtin for non-scalars

- some optimizations for array('c')

- some improvements for 'copy' module

- use 'long' type for hash values everywhere

- support for 'isinstance' was dropped

- avoid 'jump' to 100% in progress bar

- removed -d command-line option, replaced it with hidden debug-level option

- add --silent mode, showing only warnings

- add timer (jason ye)

- os.utime implementation for windows

- documented how to profile extension modules

- documentation moved to wiki


# Shed Skin 0.8 (15-06-2011) #

- support for 'struct' module (triggered by danny milo)

- support for 'array' module

- upgraded c64 emulator example, now around 3,500 lines (sloccount; uses struct, array; danny milo)

- new 'havlak loop recognition' example

- new 'sha-1' example (uses struct; thanks to emanuel rumpf)

- new 'solitaire encryption' example (thanks to funami)

- important type inference fix (reported by fahrzin hemmati)

- base include file order on cross-file inheritance relations

- add -x option as first attempt at displaying exception backtraces

- improved printing of uncaught exceptions

- fix for tuple assignment unpacking to single variable (reported by danny milo)

- fix for OSX (separate FLAGS.osx, triggered by ian ozsvald)

- GCC 4.3 fix (reported by paul boddie)

- 64-bit fix (reported by thomas spura)

- remove -fomit-frame-pointer (thomas spura)

- optimized power(float, {2,3}) (reported by thomas spura)

- add default hash method (triggered by frank chang)

- some fixes for Exception hierarchies

- list.delslice fix

- bin() buffer overflow fix (reported by brian cleary)

- improvements to sys module (sys.byteorder, sys.platform..)

- added 'setup.py test' option (thomas spura)

- updated tutorial (thanks to james coughlan, ian ozsvald and others for suggestions)

- added 'distributing binaries' section to the tutorial

- added 'faq' section to the wiki

- removed FOR\_IN\_SEQ macro, renamed FOR\_IN\_NEW to FOR\_IN

- several minor fixes, cleanups

# Shed Skin 0.7.1 (19-02-2011) #

- new quantum monte carlo simulation example (mark dewing, 1,200 sloc)

- new 'rsync' example

- updated 'c64 emulator' example, better and faster

- Makefile cleanups (fahrzin hemmati)

- experimental PyPy extmod generation (victor garcia)

- optimized 'pow' (thomas spura)

- several important extmod fixes (found by running all the tests using -e)

- add extmod leakage test script, and fix some refcounting issues

- explicitly warn about tuples of length > 2 and different types of elements

- optimized zip, min, max, map, filter, reduce

- fixes for some list method corner cases

- cleanups for the internal abstract sequence class

- removed remains of deprecated FOR\_IN macro

- several minor fixes


# Shed Skin 0.7 (12-12-2010) #

- windows package, based on recent mingw (GCC 4.5)

- fix warnings again (now with tests!)

- many multi-module fixes (several for circular imports)

- major improvement to casting/conversion framework

- string equality and slicing optimizations

- new -o/--noassert option to disable assertions

- two new examples:

> - 1050 sloc advanced raytracer (eric uhrhane)

> - 200 sloc path tracing raytracer (jonas wagner)

- C64 emulator example split up again in many modules

- basic support for 'super' keyword

- fixes for dict/defaultdict.update method

- fix for str.partition/rpartition methods

- fix for global variables and tuple assignment

- improve support for IOError attributes

- string hash value sometimes not initialized as -1

- fix global/instance variable clash in C++

- 1-length string cache and strange chars

- explicitly imported but unused function problem

- untested socket.makefile implementation

- fix for float('inf') and such under windows

- removed some leftovers from support for generics

- added 'easy tasks' wiki page

# Shed Skin 0.6 (16-10-2010) #

-major scalability improvement (incremental type analysis)

-progress bar (possible because of incremental analysis!)

-extension module improvements:

> -basic support for (un)pickling of compiled classes

> -exposition of inheritance relations

> -improved support for operator overloading

-argument unpacking, as in 'def blah((a,(b,c)):' (hakan ardo)

-optional 'murmur' string hashing (shedskin -s; thomas spura)

-some printing cleanups (thomas spura)

-new 'chaos fractals' example (carl friedrich boltz)

-new commodore 64 emulator example! (danny milosavljevic)

-several major bugfixes:

> -improved module/lineno information for warnings

> -variable lookup would sometimes look in wrong module

> -dict corruption on 64-bit

-reorganized test setup

-several minor cleanups and bugfixes

# Shed Skin 0.5 (20-6-2010) #

-64-bit integer support (shedskin -l)

-many iteration optimizations (new FOR\_IN, builtins using it)

-new dict implementation, based on cpython (FFAO)

-basic support for MSVC (shedskin -v; andy miller, jason ye)

-improvements to the socket module (michael elkins)

-support for generator methods (douglas mcneil)

-support "from future import print\_function" (douglas mcneil)

-new "adatron" example (stavros korokithakis)

-optimized printing (thomas spura)

-time.strptime implementation for windows (andy miller)

-support for @x.setter syntax

-optimize str(int) and int(str) conversion

-major optimization in random module

-improvements for class-level attributes

-many minor optimizations, cleanups and bugfixes

# Shed Skin 0.4 (27-3-2010) #

-support for generator expressions

-first-class support for booleans (so they print as 'True', for example)

-support for the 'key' argument of 'min' and 'max'

-dropped windows support

-four new examples, now 47 in total:

> -pylife (by David Bau, based on the wonderful hashlife algorithm)

> -a-star/pygame algorithm (John Eriksson)

> -a second genetic example (Stavros Korokithakis)

> -a replacement for the game of life example (Francesco Frassinelli)

-fix  [issue 53](https://code.google.com/p/shedskin/issues/detail?id=53) : casting to builtins when type inference is not enough

-examples/life.py: randomize TI a bit, to avoid getting stuck

-heapq.{merge,nsmallest,nlargest} (jeremie roquet)

-several improvements to 'defaultdict' (for example, support for 'defaultdict(None, ..)')

-improved partial support for 'kwargs' in lib/

-resolved some licensing issues for time.strptime and string hashing implementations

-pass defaultdicts to/from extension modules

-support for open('U') (jeremie roquet)

-support `dict([1,1])` and similar

-support for 'bin' (jeremie roquet)

-support for 'math.factorial' (jeremie roquet)

-support for 'random.triangular'

-random.seed: support None or hashable argument (brent pedersen)

-fix many GCC warnings that occur when enabling all warnings

-improvements for `SystemExit`

-several large code cleanups

-added some important warnings

-optimizations for tuple equality, 'any', 'all', 'reduce'

-cleaner output for boolean testing, 'and' and 'or'

-'itertools.product' repeat argument bug fix (jeremie roquet)

-many, many other bug fixes

# Shed Skin 0.3 (13-1-2010) #

- support for 3 new standard library modules (now about 20 in total):

> - itertools (jeremie roquet)

> - heapq (jeremie roquet)

> - csv (converted using shedskin)

- 4 new example programs (now 44 in total!):

> - maximum weighted matching algorithm (joris van rantwijk)

> - kanoodle: knuth's dancing links (david austin)

> - bidirectional dijkstra algorithm (from networkx, uses heapq)

> - barnes-hut force calculation

- improved type inference (scalability, bugfixes, major cleanup)

- support for 'map', 'filter', 'reduce' and 'next'

- support for 'with' statement (jeremie roquet)

- support for 'key' argument of 'sorted' (and 'list.sort')

- reorganized codebase, distutils setup.py (thomas spura)

- optimized list indexing (joris van rantwijk)

- optimized addition of 1-length lists and strings

- improved forward referencing of variables/functions

- avoid GCC warnings after 'shedskin -e'

- support for passing keyword arguments to extension modules

- optimized list slicing

- ignore blocks surrounded by #{ and #} (mike schrick)

- add --makefile option (mike schrick)

- several cleanups, removing about 100 lines again

- large amount of bugfixes

# Shed Skin 0.2 (14-7-2009) #

- 7 new example programs (some removed, now 40 in total):

> -disco: a simple monte carlo + UCT go player (368 lines, mark dufour)

> -a more advanced voronoi algorithm (795 lines; steve fortune, bill simons)

> -a nicer neural network implementation (raymond hettinger, jeff hinrichs)

> -TSP approximation using ant colonies (eric rollins)

> -Lempel-Ziv compressor (david mackay)

> -huffman block compressor (david mackay)

> -arithmetic coding compressor (david mackay)

- many inlining optimizations

- huge speedups for 'for a, b in enumerate/zip(sequence, [sequence](sequence.md))'


- important TI fix (involving default arguments)

- fixes for 'import as'


- follow module initialization order

- optimized 'len(list)' (remove virtual call)

- optimized list slicing (when step is 1)

- drop compatibility with 2.3, follow 2.6 implementation

- fysphun example now uses an extension module

- variable with name underscore no special case anymore (could be dynamic)

- cleaned up compiler core further, removing about 100 lines again

- many minor bugfixes


# Shed Skin 0.1.1 (22-4-2009) #

-five new example programs:

> -minilight: advanced raytracer (triangle primitives, octree spatial index)

> -peter norvig's sudoku solver (solves top 95 difficult ones in under 10 seconds)

> -interactive circle packing algorithm (pygame + compiled extension module)

> -ao bench: ambient occlusion benchmark

> -mastermind strategy evaluator

-removal of generic type support (nice, but rarely useful)

> -no need for command-line option -i anymore

> -compiler core is now 10% smaller (from 7700 to under 7000 lines)

> -weird templates would confuse user

-traditional important TI fixes (disappearing types, non-termination)

-compiler should use about 25% less memory and CPU time

-huge refactoring for readability in infer.py and cpp.py

-extmod fixes:

> -incref None, so it doesn't get deallocated

> -accept None when converting to custom class instance

-new command-line option -r, for faster random number generator (C rand())

-bounds checking is now on by default (for compatibility), -b now turns it off

-many minor bug fixes/improvements

> -added os.SEEK`*`

> -added file.next

> -fixed return type of re.groups

> -fixed overloading of getitem

> -asterisk support in string formatting ('%`*`d' % (7,8))

> -optimized string slicing

-added performance tips to tutorial

# Shed Skin 0.1 (25-1-2009) #

- almost complete support for 'os' (UNIX)

- jpeg decoder (1200 lines) and two other programs added to ss-progs

- extension module fixes:

> - improved exception handling

> - support for frozenset

> - improved compiler flags under OSX

- important type inference fix (disappearing type)

- improved variable overloading

- casting improvements

- fixes for setslice, delslice corner cases

- xrange returns xrange object instead of iterator

- several other bugfixes

# Shed Skin 0.0.30 (2-12-2008) #

- user-defined class support in extension modules

- blindingly fast set implementation (FFAO)

- complex number support

- many string formatting improvements

- None maps to NULL instead of 0, and prints as 'None'

- re.match\_object.group accepts multiple arguments

- casting improvements

- inheritance from builtin exceptions other than Exception

- hashing None should work now

- important type inference fix

- many, many bugfixes

# Shed Skin 0.0.29 (20-9-2008) #

- `datetime` implementation (Karel Heyse, Pavel Vinogradov, FFAO, David Marek)

- `ConfigParser` implementation (suggested by Albert Hofkamp)

- `staticmethod` and `property` decorator support (Seo Sanghyeon)

- GCC 4.3 fixes (Seo Sanghyeon, Winterknight)

- FreeBSD, OpenSolaris and 64-bit support

- support for mapping keys(`'%(key)x' % some_dict`)

- improvements to the import mechanism for nested modules (e.g. `os.path`)

- `__init__` is now less of a special case

- many fixes for calling ancestor methods (e.g. `__init__`)

- all example programs now compile to extension modules

- avoid stack overflows for highly recursive/dynamic types

- `re.sub` now accepts a replacement function

- remove tuple hash caching (as CPython does not do this)

- many, many bugfixes

# Shed Skin 0.0.28 (3-6-2008) #

- basic 'socket' support (Michael Elkins)

- support for os.{popen3, popen4} (Jaroslaw Tworek)

- support for time.strptime under Windows (David Marek)

- options for changing output dir, disabling annotation (Dave Tweed)

- support for 'cmp' and 'reverse' arguments of 'sorted' and 'list.sort'

- fixes for cross-module default arguments

- important fixes for type inference and inheritance

- restore compatibility with Python 2.3

- many minor bugfixes


# Shed Skin 0.0.27 (23-2-2008) #

- support for 're', via libpcre (perl-compatible-regular-expressions)

- support for 'time' (except for time.strptime under Windows)

- basic support for 'staticmethod' and 'property'

- support for 'fnmatch', 'glob' (bootstrapped)

- improved support for 'os' (POSIX)

- OSX support (including extension modules!)

- many fixes for multi-dir/multi-file projects

- several builtin optimizations (zip, list(str)..)

- type model for 'datetime' (no C++ implementation yet)

- split up compiler core, ss.py, into several files

- many minor bugfixes


# Shed Skin 0.0.26 (6-1-2008) #

-support for:

> -most os.path methods

> -many os methods

> -collections.defaultdict

> -getopt.gnu\_getopt

> -5 of the last missing str methods

> -some missing file functionality

-improved locale support

-removed many leading underscores in code generation

-optimized string addition (a+b+c+..)

-new documentation/tutorial

-added a Debian package

-moved to Google code hosting

-many minor bug fixes