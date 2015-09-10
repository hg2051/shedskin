# string formatting performance #

the important modfill function in lib/builtin.cpp can probably become a lot faster by building the result in one go, instead of using many intermediate allocations. we probably want to implement our own asprintf function. something similar holds for many repr methods..

# itertools.product #

the performance of this common function can be improved in at least two ways, as was done for the zip(a,b) implementation: preallocate tuples if their number is known, and use FOR\_IN type iteration. (first part was done for 0.9.1)

# cygwin instead of mingw #

could this work, and would it lessen the pain of supporting windows?

# extension module improvements #

we could use more tests (see tests/run.py). support for class-level attributes and properties would be nice.

# string support #

profile and optimize commonly used string methods. long term, we want to replace the STL strings with a cpython-based implementation, but that's a lot of work.

# parameterize double type #

for ints, we use a special ss\_int type that can be changed from a single line (shedskin -l does this). for floats, it would be nice to do something similar, so we can lower/increase precision at will.

# list implementation #

currently we use an STL vector internally. it should probably be faster to use our own cpython-based implementation, and GC\_MALLOC\_ATOMIC when possible (as was done for the set and dict classes). probably not that easy, but a proof-of-concept would be very interesting.

# shedskin -x improvement #

it would be nice to get closer to a python traceback, including filenames and line numbers. there are some snippets on the web to do this for C, so with some minor modifications it can probably be made to work for C++.

this is also currently disabled under windows.

# arbitrary-size arithmetic #

might be quite a bit of work, but long term it would be nice to support arbitrary-size integer arithmetic through something like libgmp. note the 'typedef ss\_int' statement in the top of lib/builtin.hpp.

# share memory between shedskin and cpython #

e.g. by making arrays accessible from both sides (no conversion). would be very nice to allow shedskin to work on numpy objects this way.

# struct and ieee754 #

(un)packing floats on hardware that doesn't natively use ieee754 format currently doesn't work.