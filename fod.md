# my god, why? #

because we can!

# but I heard we can't! type inference doesn't scale! it's exponential.. #

does the graph published [here](http://shed-skin.blogspot.com/2010/12/shed-skin-07-type-inference-scalability.html) look exponential? since publishing it, the largest program has almost doubled in size, and it still fits this (slightly quadratic?) curve.

type inference for arbitrary python code may be intractable, but that doesn't say anything about statically restricted programs. there just hasn't been much research on the topic in recent years, and failed experiments from way back still seem to linger in people's minds. there have been real improvements though, and computers are infinitely faster these days.

the perceived problem is also somewhat academic, because one could observe most types in a running python program (or store analysis results of a previous session), making type inference much easier. shedskin doesn't do this, because so far it's not needed.

# but still, a JIT compiler is easier to use, and just as fast #

shedskin makes a different trade-off than the typical JIT compiler. rather than try and give a good speedup for arbitrary python code, it is a tool that explicitly sacrifices some flexibility in order to maximize performance for certain types of programs. this may make it useless in many cases, and useful in some.

it is very useful to have a good JIT compiler when writing, say, a Django application. but when you are writing a neural network implementation, for example, it is not easy for a JIT to come close to the performance of a static C++ compiler. [here](http://attractivechaos.github.com/plb/) is an interesting performance comparison between different python implementions. note that the first two tests can run a lot faster still when using 'shedskin -b'.

static compilation has other advantages. if you know what you are doing, for example, it is more transparent how your code is optimized. static typing also gives you a guarantee of type-correctness - compilation with shedskin sometimes actually uncovers bugs in the original code.

# no sir, I don't like it. restricted python is not python! #

code accepted by shedskin is still pure python code. you can still debug it with cpython, use most of the python builtins, list comprehensions, and more than 20 common standard library modules. the [shedskin example test set](http://gitorious.org/shedskin/mainline/trees/master/examples) shows that a statically restricted subset of python can still be quite useful.

shedskin can also generate extension modules for you, that can be incorporated into larger python programs. so you can use unrestricted python code and arbitrary libraries in your main program, but still get a speedup in some critical piece of code, while keeping everything in pure python.

for example, the [pylot raytracer example](http://gitorious.org/shedskin/mainline/trees/master/examples) uses Tk and multiprocessing in combination with a shedskin-compiled extension module, and the [c64 emulator example](http://gitorious.org/shedskin/mainline/trees/master/examples) uses pygtk for its interface.

# if you want to have ultimate performance, use manual C #

true, but:

- not everyone can program in C

- not everyone likes to program in C

- not every program can be made much faster in C

- statically compiled python code can often be fast enough

- a single python version is easier to debug and maintain

well, almost true, because you will have to use assembly language for ultimate performance of course.

# but wait, those JIT compilers will be faster than manual assembly language! #

that's of course ridiculous. but it's true JITs will probably be 'fast enough' in more and more cases, so it's just not worth it to spend time optimizing things further. shedskin is there to push performance further if needed, with potentially much less user effort than having to resort to manual C.

# integration is not straightforward #

shedskin has its own implementation of the python builtins, so when objects are passed between shedskin and cpython, they often have to be converted, which can be very slow indeed. additionally, not every type of object can be passed. for example, numpy is currently not supported, so numpy arrays have to be passed via their 'tolist' method.

shedskin is a tool, that can be very useful at times, but often you'll have to puzzle a bit how to best use it in a given situation.

# my program doesn't become faster after compilation #

in most cases, this is because C++ is not faster at IO, allocating small objects or string operations. there's often no use in compiling a program for speed if one of these is the bottleneck.

working around small object allocations can often make the resulting C++ much faster. see the [documentation](http://code.google.com/p/shedskin/wiki/docs) for other performance tips.

# shedskin doesn't terminate for my program #

we'd really like to hear about such programs, as they can be very useful to improve shedskin's type inference engine. please post them on the mailing list, or send them in private to mark.dufour, at gmail.com.

shedskin is known to have trouble analyzing actually dynamic types. first please make sure that you are not mixing different types together, such as integers and strings in the same list or variable.

if you are not sure where the dynamic types come from, try to compile a small version of your program first, and add to it, until you see which part of the code triggers them.

# what about parallellization? #

the preferred way to parallelize shedskin-compiled programs is to generate a single extension module (shedskin -e), and use this in combination with the multiprocessing library. this way, the original program will also run faster than when using threads (no issues with the Global Interpreter Lock).

see the [pylot raytracer example](http://gitorious.org/shedskin/mainline/trees/master/examples) for an example of this.