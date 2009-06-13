'''
*** SHED SKIN Python-to-C++ Compiler ***
Copyright 2005-2009 Mark Dufour; License GNU GPL version 3 (See LICENSE)

cpp.py: output C++ code

output equivalent C++ code, using templates and virtuals to support data, parametric and OO polymorphism.

class generateVisitor: inherits visitor pattern from compiler.visitor.ASTVisitor, to recursively generate C++ code for each syntactical Python construct. the constraint graph, with inferred types, is first 'merged' back to program dimensions (getgx().merged_inh). 

typesetreprnew(): returns the C++ (or annotation) type declaration, taking into consideration detected data/parametric polymorphism (via analyze_virtuals() and template_detect()).

'''

from compiler import *
from compiler.ast import *
from compiler.visitor import *

from shared import *
import extmod

import textwrap, string

from backward import *

# --- code generation visitor; use type information
class generateVisitor(ASTVisitor):
    def __init__(self, module):
        self.output_base = os.path.join(getgx().output_dir, module.filename[:-3])
        self.out = file(self.output_base+'.cpp','w')
        self.indentation = ''
        self.consts = {}
        self.mergeinh = merged(getgx().types, inheritance=True) 
        self.module = module
        self.name = module.ident
        self.filling_consts = False
        self.constant_nr = 0

    def insert_consts(self, declare): # XXX ugly
        if not self.consts: return
        self.filling_consts = True

        if declare: suffix = '.hpp'
        else: suffix = '.cpp'

        lines = file(self.output_base+suffix,'r').readlines()
        newlines = [] 
        j = -1
        for (i,line) in enumerate(lines):
            if line.startswith('namespace ') and not 'XXX' in line: # XXX
                j = i+1
            newlines.append(line)
        
            if i == j:
                pairs = []
                done = set()
                for (node, name) in self.consts.items():
                    if not name in done and node in self.mergeinh and self.mergeinh[node]: # XXX
                        ts = typesetreprnew(node, inode(node).parent)
                        if declare: ts = 'extern '+ts
                        pairs.append((ts, name))
                        done.add(name)

                newlines.extend(self.group_declarations(pairs))
                newlines.append('\n')

        newlines2 = [] 
        j = -1
        for (i,line) in enumerate(newlines):
            if line.startswith('void __init() {'):
                j = i
            newlines2.append(line)
        
            if i == j:
                todo = {}
                for (node, name) in self.consts.items():
                    if not name in todo:
                        todo[int(name[6:])] = node
                todolist = todo.keys()
                todolist.sort()
                for number in todolist:
                    if self.mergeinh[todo[number]]: # XXX
                        name = 'const_'+str(number)
                        self.start('    '+name+' = ')
                        self.visit(todo[number], inode(todo[number]).parent)
                        newlines2.append(self.line+';\n')

                newlines2.append('\n')
        
        file(self.output_base+suffix,'w').writelines(newlines2)
        self.filling_consts = False
        
    def insert_includes(self): # XXX ugly
        includes = get_includes(self.module)
        prop_includes = set(self.module.prop_includes) - set(includes)
        if not prop_includes: return
 
        #print 'insert', self.module, prop_includes

        lines = file(self.output_base+'.hpp','r').readlines()
        newlines = []
 
        prev = ''
        for line in lines:
            if prev.startswith('#include') and not line.strip():
                for include in prop_includes:
                    newlines.append('#include "%s"\n' % include)
            newlines.append(line)
            prev = line
 
        file(self.output_base+'.hpp','w').writelines(newlines)

    # --- group pairs of (type, name) declarations, while paying attention to '*'
    def group_declarations(self, pairs):
        group = {}
        for (type, name) in pairs:
            group.setdefault(type, []).append(name)
        
        result = []
        for (type, names) in group.items():
            names.sort(cmp)
            if type.endswith('*'):
                result.append(type+(', *'.join(names))+';\n')
            else:
                result.append(type+(', '.join(names))+';\n')

        return result

    def header_file(self):
        self.out = file(self.output_base+'.hpp','w')
        self.visit(self.module.ast, True)
        self.out.close()

    def classes(self, node):
        return set([t[0].ident for t in inode(node).types()])

    def output(self, text):
        print >>self.out, self.indentation+text

    def start(self, text=None):
        self.line = self.indentation
        if text: self.line += text
    def append(self, text):
        self.line += text
    def eol(self, text=None):
        if text: self.append(text)
        if self.line.strip():
            print >>self.out, self.line+';'

    def indent(self):
        self.indentation += 4*' '
    def deindent(self):
        self.indentation = self.indentation[:-4]

    def connector(self, node, func):
        if singletype(node, module): return '::'

        elif func and func.listcomp:
            return '->'
        elif isinstance(node, Name) and not lookupvar(node.name, func): # XXX
            return '::'

        return '->'

    def declaredefs(self, vars, declare): # XXX use group_declarations
        decl = {}
        for (name,var) in vars:
            if singletype(var, module) or var.invisible: # XXX buh
                continue
            typehu = typesetreprnew(var, var.parent)
            # void *
            if not typehu or not var.types(): continue 

            decl.setdefault(typehu, []).append(self.cpp_name(name))
        decl2 = []
        for (t,names) in decl.items():
            names.sort(cmp)
            prefix=''
            if declare: prefix='extern '
            if t.endswith('*'):
                decl2.append(prefix+t+(', *'.join(names)))
            else:
                decl2.append(prefix+t+(', '.join(names)))
        return ';\n'.join(decl2)

    def constant_constructor(self, node):
        if isinstance(node, (UnarySub, UnaryAdd)):
            node = node.expr
        if isinstance(node, Const) and type(node.value) in [int, float, str]:
            return False

        return self.constant_constructor_rec(node)
       
    def constant_constructor_rec(self, node):
        if isinstance(node, (UnarySub, UnaryAdd)):
            node = node.expr

        # --- determine whether built-in constructor call builds a (compound) constant, e.g. [(1,),[1,(1,2)]]
        if isinstance(node, (List, Tuple, Dict)):
            return not False in [self.constant_constructor_rec(child) for child in node.getChildNodes()]

        # --- strings may also be constants of course
        elif isinstance(node, Const) and type(node.value) in [int, float, str]:
            if type(node.value) == str:
                self.get_constant(node)
            return True

        return False

    def find_constants(self):
        # --- determine (compound, non-str) constants
        for callfunc, _ in getmv().callfuncs:
            if isinstance(callfunc.node, Getattr) and callfunc.node.attrname in ['__ne__', '__eq__', '__contains__']:
                for node in [callfunc.node.expr, callfunc.args[0]]:
                    if self.constant_constructor(node):
                        self.get_constant(node)

        for node in getmv().for_in_iters:
            if self.constant_constructor(node):
                self.get_constant(node)

        for node in self.mergeinh:
            if isinstance(node, Subscript):
                if self.constant_constructor(node.expr):
                    self.get_constant(node.expr)

    def get_constant(self, node):
        parent = inode(node).parent
        while isinstance(parent, function) and parent.listcomp: # XXX
            parent = parent.parent
        if isinstance(parent, function) and parent.inherited:
            return

        for other in self.consts:
            if node is other or self.equal_constructor_rec(node, other):
                return self.consts[other]
        
        self.consts[node] = 'const_'+str(self.constant_nr)
        self.constant_nr += 1

        return self.consts[node]
    
    def equal_constructor_rec(self, a, b):
        if isinstance(a, (UnarySub, UnaryAdd)) and isinstance(b, (UnarySub, UnaryAdd)):
            return self.equal_constructor_rec(a.expr, b.expr)

        if isinstance(a, Const) and isinstance(b, Const):
            for c in (int, float, str):
                if isinstance(a.value, c) and isinstance(b.value, c):
                    return a.value == b.value
        
        for c in (List, Tuple, Dict):
            if isinstance(a, c) and isinstance(b, c) and len(a.getChildNodes()) == len(b.getChildNodes()): 
                return not 0 in [self.equal_constructor_rec(d,e) for (d,e) in zip(a.getChildNodes(), b.getChildNodes())]

        return 0

    def module_hpp(self, node):
        define = '_'.join(self.module.mod_path).upper()+'_HPP'
        print >>self.out, '#ifndef __'+define
        print >>self.out, '#define __'+define+'\n'

        # --- include header files
        if self.module.dir == '': depth = 0
        else: depth = self.module.dir.count('/')+1
        #print >>self.out, '#include "'+depth*'../'+'builtin_.hpp"'

        includes = get_includes(self.module)
        if 'getopt.hpp' in includes: # XXX
            includes.add('os/__init__.hpp')
            includes.add('os/path.hpp')
            includes.add('stat.hpp')
        if 'os/__init__.hpp' in includes: # XXX
            includes.add('os/path.hpp')
            includes.add('stat.hpp')
        for include in includes:
            print >>self.out, '#include "'+include+'"'
        if includes: print >>self.out

        # --- namespaces
        print >>self.out, 'using namespace __shedskin__;'
        for n in self.module.mod_path:
            print >>self.out, 'namespace __'+n+'__ {'
        print >>self.out
             
        skip = False
        for child in node.node.getChildNodes():
            if isinstance(child, From): 
                skip = True
                mod_id = '__'+'__::__'.join(child.modname.split('.'))+'__'

                for (name, pseudonym) in child.names:
                    if name == '*':
                        for func in getgx().modules[child.modname].funcs.values():
                            if func.cp: 
                                print >>self.out, 'using '+mod_id+'::'+self.cpp_name(func.ident)+';';
                        for cl in getgx().modules[child.modname].classes:
                            print >>self.out, 'using '+mod_id+'::'+cl+';';
                    else:
                        if not pseudonym: pseudonym = name
                        if not pseudonym in self.module.mv.globals:# or [t for t in self.module.mv.globals[pseudonym].types() if not isinstance(t[0], module)]:
                            print >>self.out, 'using '+mod_id+'::'+nokeywords(name)+';'
        if skip: print >>self.out

        # class declarations
        gotcl = False
        for child in node.node.getChildNodes():
            if isinstance(child, Class): 
                gotcl = True
                cl = defclass(child.name)
                print >>self.out, 'class '+nokeywords(cl.ident)+';'

        # --- lambda typedefs
        if gotcl: print >>self.out
        self.func_pointers(True)

        # globals
        defs = self.declaredefs(list(getmv().globals.items()), declare=True);
        if defs:
            self.output(defs+';')
            print >>self.out

        # --- class definitions
        for child in node.node.getChildNodes():
            if isinstance(child, Class): 
                self.class_hpp(child)

        # --- defaults
        if self.module.mv.defaults.items(): 
            for default, nr in self.module.mv.defaults.items():
                print >>self.out, 'extern '+typesetreprnew(default, None)+' '+('default_%d;'%nr)
            print >>self.out
                
        # function declarations
        if self.module != getgx().main_module:
            print >>self.out, 'void __init();'
        for child in node.node.getChildNodes():
            if isinstance(child, Function): 
                func = getmv().funcs[child.name]
                if not self.inhcpa(func):
                #if not hmcpa(func) and (not func in getgx().inheritance_relations or not [1 for f in getgx().inheritance_relations[func] if hmcpa(f)]): # XXX merge with visitFunction
                    pass
                elif not func.mv.module.builtin and not func.ident in ['min','max','zip','sum','__zip2','enumerate']: # XXX latter for test 116
                    self.visitFunction(func.node, declare=True)
        print >>self.out

        for n in self.module.mod_path:
            print >>self.out, '} // module namespace'

        if getgx().extension_module and self.module == getgx().main_module: 
            extmod.convert_methods2(self, self.module.classes.values())

        print >>self.out, '#endif'

    def module_cpp(self, node):
        # --- external dependencies 
        if self.module.filename.endswith('__init__.py'): # XXX nicer check
            print >>self.out, '#include "__init__.hpp"\n'
        else:
            #print >>self.out, '#include "'+'/'.join(self.module.mod_path+[self.module.ident])+'.hpp"\n'
            print >>self.out, '#include "%s.hpp"\n' % self.module.ident

        # --- comments
        if node.doc:
            self.do_comment(node.doc)
            print >>self.out

        # --- namespace
        for n in self.module.mod_path:
            print >>self.out, 'namespace __'+n+'__ {'
        print >>self.out

        # --- globals
        defs = self.declaredefs(list(getmv().globals.items()), declare=False);
        if defs:
            self.output(defs+';')
            print >>self.out

        # --- constants: __eq__(const) or ==/__eq(List())
        self.find_constants()

        # --- defaults
        if self.module.mv.defaults.items(): 
            for default, nr in self.module.mv.defaults.items():
                print >>self.out, typesetreprnew(default, None)+' '+('default_%d;'%nr)
            print >>self.out

        # --- list comprehensions
        self.listcomps = {}
        for (listcomp,lcfunc,func) in getmv().listcomps:
            self.listcomps[listcomp] = (lcfunc, func)
        for (listcomp,lcfunc,func) in getmv().listcomps: # XXX cleanup
            if lcfunc.mv.module.builtin:
                continue

            parent = func
            while isinstance(parent, function) and parent.listcomp: 
                parent = parent.parent

            if isinstance(parent, function):
                if not self.inhcpa(parent) or parent.inherited:
                    continue

            self.listcomp_func(listcomp)

        # --- lambdas
        for l in getmv().lambdas.values():
            if l.ident not in getmv().funcs:
                self.visit(l.node)

        # --- classes 
        for child in node.node.getChildNodes():
            if isinstance(child, Class): 
                self.class_cpp(child)

        # --- __init
        self.output('void __init() {')
        self.indent()
        if self.module == getgx().main_module and not getgx().extension_module: self.output('__name__ = new str("__main__");\n')
        else: self.output('__name__ = new str("%s");\n' % self.module.ident)

        if getmv().classes:
            for cl in getmv().classes.values():
                self.output('cl_'+cl.cpp_name+' = new class_("%s", %d, %d);' % (cl.cpp_name, cl.low, cl.high))

                for var in cl.parent.vars.values():
                    if var.initexpr:
                        self.start()
                        self.visitm(cl.ident+'::'+self.cpp_name(var.name)+' = ', var.initexpr, None)
                        self.eol()

            print >>self.out

        for child in node.node.getChildNodes():
            if isinstance(child, Function): 
                for default in child.defaults:
                    if default in getmv().defaults:
                        self.start('')
                        self.visitm('default_%d = ' % getmv().defaults[default], default, ';')
                        self.eol()

            elif isinstance(child, Class):
                for child2 in child.code.getChildNodes():
                    if isinstance(child2, Function): 
                        for default in child2.defaults:
                            if default in getmv().defaults:
                                self.start('')
                                self.visitm('default_%d = ' % getmv().defaults[default], default, ';')
                                self.eol()

            elif isinstance(child, Discard):
                if isinstance(child.expr, Const) and child.expr.value == None: # XXX merge with visitStmt
                    continue
                if isinstance(child.expr, Const) and type(child.expr.value) == str:
                    continue

                self.start('')
                self.visit(child)
                self.eol()

            elif isinstance(child, From):
                mod_id = '__'+'__::__'.join(child.modname.split('.'))+'__'
                for (name, pseudonym) in child.names:
                    if name == '*':
                        for var in getgx().modules[child.modname].mv.globals.values():
                            if not var.invisible and not var.imported and not var.name.startswith('__') and var.types():
                                self.start(nokeywords(var.name)+' = '+mod_id+'::'+nokeywords(var.name))
                                self.eol()
                    else:
                        if not pseudonym: pseudonym = name
                        if pseudonym in self.module.mv.globals and not [t for t in self.module.mv.globals[pseudonym].types() if isinstance(t[0], module)]:
                            self.start(nokeywords(pseudonym)+' = '+mod_id+'::'+nokeywords(name))
                            self.eol()

            elif not isinstance(child, (Class, Function)):
                self.do_comments(child)
                self.visit(child)

        self.deindent()
        self.output('}\n')

        for child in node.node.getChildNodes():
            if isinstance(child, Function): 
                self.do_comments(child)
                self.visit(child)

        # --- close namespace
        for n in self.module.mod_path:
            print >>self.out, '} // module namespace'
        print >>self.out

        # --- c++ main/extension module setup
        if self.module == getgx().main_module: 
            if getgx().extension_module:
                extmod.do_extmod(self)
            else:
                self.do_main()
        
    def visitModule(self, node, declare=False):
        if declare:
            self.module_hpp(node)
        else:
            self.module_cpp(node)

    def do_main(self):
        print >>self.out, 'int main(int argc, char **argv) {'

        self.do_init_modules()

        print >>self.out, '    __shedskin__::__exit();'
        print >>self.out, '}'

    def do_init_modules(self):
        print >>self.out, '    __shedskin__::__init();'

        # --- init imports
        mods = getgx().modules.values()
        mods.sort(cmp=lambda a,b: cmp(a.import_order, b.import_order))
        for mod in mods:
            if mod != getgx().main_module and mod.ident != 'builtin':
                if mod.ident == 'sys':
                    if getgx().extension_module:
                        print >>self.out, '    __sys__::__init(0, 0);'
                    else:
                        print >>self.out, '    __sys__::__init(argc, argv);'
                else:
                    print >>self.out, '    __'+'__::__'.join([n for n in mod.mod_path])+'__::__init();' # XXX sep func

        # --- start program
        print >>self.out, '    __'+self.module.ident+'__::__init();'

    def do_comment(self, s):
        if not s: return
        doc = s.replace('/*', '//').replace('*/', '//').split('\n')
        self.output('/**')
        if doc[0].strip():
            self.output(doc[0])
        # re-indent the rest of the doc string
        rest = textwrap.dedent('\n'.join(doc[1:])).splitlines()
        for l in rest:
            self.output(l)
        self.output('*/')

    def do_comments(self, child):
        if child in getgx().comments:
            for n in getgx().comments[child]:
                self.do_comment(n)

    def visitContinue(self, node, func=None):
        self.start('continue')
        self.eol()

    def bool_test(self, node, func):
        if [1 for t in self.mergeinh[node] if isinstance(t[0], class_) and t[0].ident == 'int_']:
            self.visit(node, func)
        else:
            self.visitm('___bool(', node, ')', func)

    def visitWhile(self, node, func=None):
        print >>self.out

        if node.else_:
            self.output('%s = 0;' % getmv().tempcount[node.else_])
         
        self.start('while (')
        self.bool_test(node.test, func)
        self.append(') {')
        print >>self.out, self.line

        self.indent()
        getgx().loopstack.append(node)
        self.visit(node.body, func)
        getgx().loopstack.pop()
        self.deindent()

        self.output('}')

        if node.else_:
            self.output('if (!%s) {' % getmv().tempcount[node.else_])
            self.indent()
            self.visit(node.else_, func)
            self.deindent()
            self.output('}')

    def class_hpp(self, node, declare=True): # XXX remove declare
        cl = getmv().classes[node.name]
        self.output('extern class_ *cl_'+cl.cpp_name+';') 

        # --- header
        if cl.bases: 
            pyobjbase = []
        else:
            pyobjbase = ['public pyobj']

        clnames = [namespaceclass(b) for b in cl.bases]
        self.output('class '+nokeywords(cl.ident)+' : '+', '.join(pyobjbase+['public '+clname for clname in clnames])+' {')

        self.do_comment(node.doc)
        self.output('public:')
        self.indent()

        self.class_variables(cl)

        # --- constructor
        need_init = False
        if '__init__' in cl.funcs:
            initfunc = cl.funcs['__init__']
            if self.inhcpa(initfunc): 
                 need_init = True

        # --- default constructor
        if need_init:
            self.output(nokeywords(cl.ident)+'() {}')
        else:
            self.output(nokeywords(cl.ident)+'() { this->__class__ = cl_'+cl.cpp_name+'; }')

        # --- init constructor
        if need_init:
            self.func_header(initfunc, declare=True, is_init=True)
            self.indent()
            self.output('this->__class__ = cl_'+cl.cpp_name+';')
            self.output('__init__('+', '.join([self.cpp_name(f) for f in initfunc.formals[1:]])+');')
            self.deindent()
            self.output('}')

        # --- virtual methods
        if cl.virtuals:
            self.virtuals(cl, declare)

        # --- regular methods
        for func in cl.funcs.values():
            if func.node and not (func.ident=='__init__' and func.inherited): 
                self.visitFunction(func.node, cl, declare)

        if cl.has_copy and not 'copy' in cl.funcs:
            self.copy_method(cl, '__copy__', declare)
        if cl.has_deepcopy and not 'deepcopy' in cl.funcs:
            self.copy_method(cl, '__deepcopy__', declare)
        
        if getgx().extension_module:
            extmod.convert_methods(self, cl, declare)

        self.deindent()
        self.output('};\n')

    def class_cpp(self, node, declare=False): # XXX declare
        cl = getmv().classes[node.name]

        if cl.virtuals:
            self.virtuals(cl, declare)

        if node in getgx().comments:
            self.do_comments(node)
        else:
            self.output('/**\nclass %s\n*/\n' % cl.ident)
        self.output('class_ *cl_'+cl.cpp_name+';\n')

        # --- method definitions
        for func in cl.funcs.values():
            if func.node and not (func.ident=='__init__' and func.inherited): 
                self.visitFunction(func.node, cl, declare)
        if cl.has_copy and not 'copy' in cl.funcs:
            self.copy_method(cl, '__copy__', declare)
        if cl.has_deepcopy and not 'deepcopy' in cl.funcs:
            self.copy_method(cl, '__deepcopy__', declare)
        
        # --- class variable declarations
        if cl.parent.vars: # XXX merge with visitModule
            for var in cl.parent.vars.values():
                if getgx().merged_inh[var]:
                    self.start(typesetreprnew(var, cl.parent)+cl.ident+'::'+self.cpp_name(var.name)) 
                    self.eol()
            print >>self.out

        return

    def class_variables(self, cl):
        # --- class variables 
        if cl.parent.vars:
            for var in cl.parent.vars.values():
                if getgx().merged_inh[var]:
                    self.output('static '+typesetreprnew(var, cl.parent)+self.cpp_name(var.name)+';') 
            print >>self.out

        # --- instance variables
        for var in cl.vars.values():
            if var.invisible: continue # var.name in cl.virtualvars: continue

            # var is masked by ancestor var
            vars = set()
            for ancestor in cl.ancestors():
                vars.update(ancestor.vars)
                #vars.update(ancestor.virtualvars)
            if var.name in vars:
                continue

            # virtual
            if var.name in cl.virtualvars:
                ident = var.name
                subclasses = cl.virtualvars[ident]

                merged = set()
                for m in [getgx().merged_inh[subcl.vars[ident]] for subcl in subclasses if ident in subcl.vars and subcl.vars[ident] in getgx().merged_inh]: # XXX
                    merged.update(m)
            
                ts = self.padme(typestrnew({(1,0): merged}, cl, True, cl))
                if merged:
                    self.output(ts+self.cpp_name(ident)+';') 

            # non-virtual
            elif var in getgx().merged_inh and getgx().merged_inh[var]:
                self.output(typesetreprnew(var, cl)+self.cpp_name(var.name)+';') 

        if [v for v in cl.vars if not v.startswith('__')]:
            print >>self.out

    def copy_method(self, cl, name, declare): # XXX merge?
        header = nokeywords(cl.ident)+' *'
        if not declare:
            header += nokeywords(cl.ident)+'::'
        header += name+'('
        self.start(header)
        
        if name == '__deepcopy__':
            self.append('dict<void *, pyobj *> *memo')
        self.append(')')

        if not declare:
            print >>self.out, self.line+' {'
            self.indent()
            self.output(nokeywords(cl.ident)+' *c = new '+nokeywords(cl.ident)+'();')
            if name == '__deepcopy__':
                self.output('memo->__setitem__(this, c);')
           
            for var in cl.vars.values():
                if var in getgx().merged_inh and getgx().merged_inh[var]:
                #if var not in cl.funcs and not var.invisible:
                    if name == '__deepcopy__':
                        self.output('c->%s = __deepcopy(%s);' % (var.name, var.name))
                    else:
                        self.output('c->%s = %s;' % (var.name, var.name))
            self.output('return c;')

            self.deindent()
            self.output('}\n')
        else:
            self.eol()

    def padme(self, x): 
        if not x.endswith('*'): return x+' '
        return x

    def virtuals(self, cl, declare):
        for ident, subclasses in cl.virtuals.items():
            if not subclasses: continue

            # --- merge arg/return types
            formals = []
            retexpr = False

            for subcl in subclasses:
                if ident not in subcl.funcs: continue

                func = subcl.funcs[ident]
                sig_types = []

                if func.returnexpr:
                    retexpr = True
                    if func.retnode.thing in self.mergeinh:
                        sig_types.append(self.mergeinh[func.retnode.thing]) # XXX mult returns; some targets with return some without..
                    else:
                        sig_types.append(set()) # XXX

                for name in func.formals[1:]:
                    var = func.vars[name]
                    sig_types.append(self.mergeinh[var])
                formals.append(sig_types)

            merged = []
            for z in zip(*formals):
                merge = set()
                for types in z: merge.update(types)
                merged.append(merge)
                
            formals = list(subclasses)[0].funcs[ident].formals[1:]
            ftypes = [self.padme(typestrnew({(1,0): m}, func.parent, True, func.parent)) for m in merged] 

            # --- prepare for having to cast back arguments (virtual function call means multiple targets)
            for subcl in subclasses:
                subcl.funcs[ident].ftypes = ftypes

            # --- virtual function declaration
            if declare:
                self.start('virtual ')
                if retexpr: 
                    self.append(ftypes[0])
                    ftypes = ftypes[1:]
                else:
                    self.append('void ')
                self.append(self.cpp_name(ident)+'(')

                self.append(', '.join([t+f for (t,f) in zip(ftypes, formals)]))

                if ident in cl.funcs and self.inhcpa(cl.funcs[ident]):
                    self.eol(')')
                else:
                    self.eol(') {}') # XXX 

                if ident in cl.funcs: cl.funcs[ident].declared = True

    def inhcpa(self, func):
        return hmcpa(func) or (func in getgx().inheritance_relations and [1 for f in getgx().inheritance_relations[func] if hmcpa(f)])

    def visitSlice(self, node, func=None):
        if node.flags == 'OP_DELETE':
            self.start()
            self.visit(inode(node.expr).fakefunc, func)
            self.eol()
        else:
            self.visit(inode(node.expr).fakefunc, func)

    def visitLambda(self, node, parent=None):
        self.append(getmv().lambdaname[node])

    def children_args(self, node, ts, func=None): 
        if len(node.getChildNodes()): 
            self.append(str(len(node.getChildNodes()))+', ')

        double = set(ts[ts.find('<')+1:-3].split(', ')) == set(['double']) # XXX whaa

        for child in node.getChildNodes():
            if double and self.mergeinh[child] == set([(defclass('int_'), 0)]):
                self.append('(double)(')

            if child in getmv().tempcount:
                self.append(getmv().tempcount[child])
            else:
                self.visit(child, func)

            if double and self.mergeinh[child] == set([(defclass('int_'), 0)]):
                self.append(')')

            if child != node.getChildNodes()[-1]:
                self.append(', ')
        self.append(')')

    def visitDict(self, node, func=None):
        if not self.filling_consts and node in self.consts:
            self.append(self.consts[node])
            return

        temp = self.filling_consts
        self.filling_consts = False
        self.append('(new '+typesetreprnew(node, func)[:-2]+'(')

        if node.items:
            self.append(str(len(node.items))+', ')

        for (key, value) in node.items:
            self.visitm('new tuple2'+typesetreprnew(node, func)[4:-2]+'(2,', key, ',', value, ')', func)
            if (key, value) != node.items[-1]:
                self.append(', ')
        self.append('))')

        self.filling_consts = temp

    def visittuplelist(self, node, func=None):
        if not self.filling_consts and node in self.consts:
            self.append(self.consts[node])
            return

        temp = self.filling_consts
        self.filling_consts = False

        ts = typesetreprnew(node, func)
        self.append('(new '+ts[:-2])
        self.append('(')
        self.children_args(node, ts, func)
        self.append(')')

        self.filling_consts = temp

    def visitTuple(self, node, func=None):
        self.visittuplelist(node, func)

    def visitList(self, node, func=None):
        self.visittuplelist(node, func)

    def visitAssert(self, node, func=None):
        self.start('ASSERT(')
        self.visitm(node.test, ', ', func)
        if len(node.getChildNodes()) > 1:
            self.visit(node.getChildNodes()[1], func)
        else:
            self.append('0')
        self.eol(')')

    def visitm(self, *args):
        if args and isinstance(args[-1], function):
            func = args[-1]
        else:
            func = None

        for arg in args[:-1]:
            if not arg: return
            if isinstance(arg, str):
                self.append(arg)
            else:
                self.visit(arg, func)

    def visitRaise(self, node, func=None):
        cl = None # XXX sep func
        t = [t[0] for t in self.mergeinh[node.expr1]]
        if len(t) == 1:
            cl = t[0]

        self.start('throw (')
        # --- raise class [, constructor args]
        if isinstance(node.expr1, Name) and not lookupvar(node.expr1.name, func): # XXX lookupclass 
            self.append('new %s(' % node.expr1.name)
            if node.expr2:
                if isinstance(node.expr2, Tuple) and node.expr2.nodes:
                    for n in node.expr2.nodes:
                        self.visit(n, func)
                        if n != node.expr2.nodes[-1]: self.append(', ') # XXX visitcomma(nodes)
                else:
                    self.visit(node.expr2, func)
            self.append(')')
        # --- raise instance
        elif isinstance(cl, class_) and cl.mv.module.ident == 'builtin' and not [a for a in cl.ancestors_upto(None) if a.ident == 'Exception']:
            self.append('new Exception()')
        else:
            self.visit(node.expr1, func)
        self.eol(')')
 
    def visitTryExcept(self, node, func=None):
        # try
        self.start('try {')
        print >>self.out, self.line
        self.indent()
        if node.else_:
            self.output('%s = 0;' % getmv().tempcount[node.else_])
        self.visit(node.body, func)
        if node.else_:
            self.output('%s = 1;' % getmv().tempcount[node.else_])
        self.deindent()
        self.start('}')

        # except
        for handler in node.handlers:
            if isinstance(handler[0], Tuple):
                pairs = [(n, handler[1], handler[2]) for n in handler[0].nodes]
            else:
                pairs = [(handler[0], handler[1], handler[2])]

            for (h0, h1, h2) in pairs:
                if isinstance(h0, Name) and h0.name in ['int', 'float', 'str', 'class']:
                    continue # XXX lookupclass
                elif h0:
                    cl = lookupclass(h0, getmv())
                    if cl.mv.module.builtin and cl.ident in ['KeyboardInterrupt', 'FloatingPointError', 'OverflowError', 'ZeroDivisionError', 'SystemExit']:
                        error("system '%s' is not caught" % cl.ident, h0, warning=True)
                    arg = namespaceclass(cl)+' *'
                else:
                    arg = 'Exception *'

                if h1:
                    arg += h1.name

                self.append(' catch (%s) {' % arg) 
                print >>self.out, self.line

                self.indent()
                self.visit(h2, func)
                self.deindent()
                self.start('}')

        print >>self.out, self.line

        # else
        if node.else_: 
            self.output('if(%s) { // else' % getmv().tempcount[node.else_])
            self.indent()
            self.visit(node.else_, func)
            self.deindent()
            self.output('}')
            
    def fastfor(self, node, assname, neg, func=None):
        ivar, evar = getmv().tempcount[node.assign], getmv().tempcount[node.list]

        self.start('FAST_FOR%s('%neg+assname+',')

        if len(node.list.args) == 1: 
            self.append('0,')
            if node.list.args[0] in getmv().tempcount: # XXX in visit?
                self.append(getmv().tempcount[node.list.args[0]])
            else:
                self.visit(node.list.args[0], func)
            self.append(',')
        else: 
            if node.list.args[0] in getmv().tempcount: # XXX in visit?
                self.append(getmv().tempcount[node.list.args[0]])
            else:
                self.visit(node.list.args[0], func)
            self.append(',')
            if node.list.args[1] in getmv().tempcount: # XXX in visit?
                self.append(getmv().tempcount[node.list.args[1]])
            else:
                self.visit(node.list.args[1], func)
            self.append(',')

        if len(node.list.args) != 3:
            self.append('1')
        else:
            if node.list.args[2] in getmv().tempcount: # XXX in visit?
                self.append(getmv().tempcount[node.list.args[2]])
            else:
                self.visit(node.list.args[2], func)
        self.append(',%s,%s)' % (ivar[2:],evar[2:]))
        #print 'ie', ivar, evar 

        print >>self.out, self.line

    def visitFor(self, node, func=None):
        if isinstance(node.assign, AssName):
            if node.assign.name != '_':
                assname = node.assign.name
            else:
                assname = getmv().tempcount[(node.assign,1)]
        elif isinstance(node.assign, AssAttr): 
            self.start('')
            self.visitAssAttr(node.assign, func)
            assname = self.line.strip()
        else:
            assname = getmv().tempcount[node.assign]

        print >>self.out

        if node.else_:
            self.output('%s = 0;' % getmv().tempcount[node.else_])

        # --- for i in range(..) -> for( i=l, u=expr; i < u; i++ ) .. 
        if fastfor(node):
            if len(node.list.args) == 3 and not const_literal(node.list.args[2]):
                self.fastfor_switch(node, func)
                self.indent()
                self.fastfor(node, assname, '', func)
                self.forbody(node, func)
                self.deindent()
                self.output('} else {')
                self.indent()
                self.fastfor(node, assname, '_NEG', func)
                self.forbody(node, func)
                self.deindent()
                self.output('}')
            else:
                neg=''
                if len(node.list.args) == 3 and const_literal(node.list.args[2]) and isinstance(node.list.args[2], UnarySub):
                    neg = '_NEG'

                self.fastfor(node, assname, neg, func)
                self.forbody(node, func)

        # --- otherwise, apply macro magic
        else:
            assname = self.cpp_name(assname)
                
            pref = ''
            if not [t for t in self.mergeinh[node.list] if t[0] != defclass('tuple2')]:
                pref = '_T2' # XXX generalize to listcomps

            if not [t for t in self.mergeinh[node.list] if t[0] not in (defclass('tuple'), defclass('list'))]:
                pref = '_SEQ'

            if pref == '': tail = getmv().tempcount[(node,1)][2:]
            else: tail = getmv().tempcount[node][2:]+','+getmv().tempcount[node.list][2:]

            self.start('FOR_IN%s(%s,' % (pref, assname))
            self.visit(node.list, func)
            print >>self.out, self.line+','+tail+')'
            self.forbody(node, func)

        print >>self.out

    def forbody(self, node, func=None):
        self.indent()

        if isinstance(node.assign, (AssTuple, AssList)):
            self.tuple_assign(node.assign, getmv().tempcount[node.assign], func)

        getgx().loopstack.append(node)
        self.visit(node.body, func)
        getgx().loopstack.pop()
        self.deindent()

        self.output('END_FOR')

        if node.else_:
            self.output('if (!%s) {' % getmv().tempcount[node.else_])
            self.indent()
            self.visit(node.else_, func)
            self.deindent()
            self.output('}')

    def func_pointers(self, print_them):
        getmv().lambda_cache = {}
        getmv().lambda_signum = {}

        for func in getmv().lambdas.values():
            argtypes = [typesetreprnew(func.vars[formal], func).rstrip() for formal in func.formals]
            signature = '_'.join(argtypes)

            if func.returnexpr:
                rettype = typesetreprnew(func.retnode.thing,func)
            else:
                rettype = 'void '
            signature += '->'+rettype

            if signature not in getmv().lambda_cache: 
                nr = len(getmv().lambda_cache)
                getmv().lambda_cache[signature] = nr
                if print_them:
                    print >>self.out, 'typedef %s(*lambda%d)(' % (rettype, nr) + ', '.join(argtypes)+');'

            getmv().lambda_signum[func] = getmv().lambda_cache[signature]

        if getmv().lambda_cache and print_them: print >>self.out

    # --- function/method header
    def func_header(self, func, declare, is_init=False):
        method = isinstance(func.parent, class_)
        if method: 
            formals = [f for f in func.formals if f != 'self'] 
        else:
            formals = [f for f in func.formals] 

        ident = func.ident
        self.start()

        # --- return expression
        header = ''
        if is_init:
            ident = nokeywords(func.parent.ident)
        elif func.ident in ['__hash__']:
            header += 'int '
        elif func.returnexpr: 
            header += typesetreprnew(func.retnode.thing, func) # XXX mult
        else:
            header += 'void '
            ident = self.cpp_name(ident)

        ftypes = [typesetreprnew(func.vars[f], func) for f in formals]

        # if arguments type too precise (e.g. virtually called) cast them back 
        oldftypes = ftypes
        if func.ftypes:
            ftypes = func.ftypes[1:]

        # --- method header
        if method and not declare:
            header += nokeywords(func.parent.ident)+'::'
        
        if is_init:
            header += ident
        else:
            header += self.cpp_name(ident)

        # --- cast arguments if necessary (explained above)
        casts = []
        if func.ftypes:
            #print 'cast', oldftypes, formals, ftypes

            for i in range(min(len(oldftypes), len(ftypes))): # XXX this is 'cast on specialize'.. how about generalization?
                if oldftypes[i] != ftypes[i]:
                    #print 'cast!', oldftypes[i], ftypes[i+1]
                    casts.append(oldftypes[i]+formals[i]+' = ('+oldftypes[i]+')__'+formals[i]+';')
                    if not declare:
                        formals[i] = '__'+formals[i]

        formals2 = formals[:]
        for (i,f) in enumerate(formals2): # XXX
            formals2[i] = self.cpp_name(f)

        formaldecs = [o+f for (o,f) in zip(ftypes, formals2)]

        if declare and isinstance(func.parent, class_) and func.ident in func.parent.staticmethods:
            header = 'static '+header

        if is_init and not formaldecs:
            formaldecs = ['int __ss_init']

        # --- output 
        self.append(header+'('+', '.join(formaldecs)+')')
        if is_init:
            print >>self.out, self.line+' {'

        elif declare: 
            self.eol()
            return
        else:
            print >>self.out, self.line+' {'
            self.indent()
                    
            if not declare and func.doc: 
                self.do_comment(func.doc)
                
            for cast in casts: 
                self.output(cast)
            self.deindent()

    def cpp_name(self, name, func=None):
        if self.module == getgx().main_module and name == 'init'+self.module.ident: # conflict with extmod init
            return '_'+name
        if name in [cl.ident for cl in getgx().allclasses]:
            return '_'+name
        elif name+'_' in [cl.ident for cl in getgx().allclasses]:
            return '_'+name
        elif name in self.module.funcs and func and isinstance(func.parent, class_) and name in func.parent.funcs: 
            return '__'+func.mv.module.ident+'__::'+name

        return nokeywords(name)

    def visitFunction(self, node, parent=None, declare=False):
        # locate right func instance
        if parent and isinstance(parent, class_):
            func = parent.funcs[node.name]
        elif node.name in getmv().funcs:
            func = getmv().funcs[node.name]
        else:
            func = getmv().lambdas[node.name]

        if func.invisible or (func.inherited and not func.ident == '__init__'):
            return
        if func.mv.module.builtin or func.ident in ['min','max','zip','sum','__zip2','enumerate']: # XXX latter for test 116
            return
        if declare and func.declared: # XXX
            return

        # check whether function is called at all (possibly via inheritance)
        if not self.inhcpa(func):
            if func.ident in ['__iadd__', '__isub__', '__imul__']:
                return
            error(repr(func)+' not called!', node, warning=True)
            if not (declare and func.ident in func.parent.virtuals):
                return
              
        if func.isGenerator and not declare:
            self.generator_class(func)

        self.func_header(func, declare)
        if declare:
            return
        self.indent()

        if func.isGenerator:
            self.generator_body(func)
            return

        # --- local declarations
        pairs = []
        for (name, var) in func.vars.items():
            if var.invisible: continue

            if name not in func.formals:
                #print 'declare', var, self.mergeinh[var], getgx().merged_inh[var]

                name = self.cpp_name(name)
                ts = typesetreprnew(var, func)
            
                pairs.append((ts, name))

        self.output(self.indentation.join(self.group_declarations(pairs)))

        # --- function body
        self.visit(node.code, func)
        if func.fakeret:
            self.visit(func.fakeret, func)
        
        # --- add Return(None) (sort of) if function doesn't already end with a Return
        if node.getChildNodes():
            lastnode = node.getChildNodes()[-1]
            if not func.ident == '__init__' and not func.fakeret and not isinstance(lastnode, Return) and not (isinstance(lastnode, Stmt) and isinstance(lastnode.nodes[-1], Return)): # XXX use Stmt in moduleVisitor
                self.output('return 0;')

        self.deindent()
        self.output('}\n')

    def generator_class(self, func):
        self.output('class __gen_%s : public %s {' % (func.ident, typesetreprnew(func.retnode.thing, func)[:-2]))
        self.output('public:')
        self.indent()
        pairs = [(typesetreprnew(func.vars[f], func), self.cpp_name(f)) for f in func.vars]
        self.output(self.indentation.join(self.group_declarations(pairs)))
        self.output('int __last_yield;\n')

        args = []
        for f in func.formals:
            args.append(typesetreprnew(func.vars[f], func)+self.cpp_name(f))
        self.output(('__gen_%s(' % func.ident) + ','.join(args)+') {')
        self.indent()
        for f in func.formals:
            self.output('this->%s = %s;' % (self.cpp_name(f),self.cpp_name(f)))
        self.output('__last_yield = -1;')
        self.deindent()
        self.output('}\n')

        self.output('%s next() {' % typesetreprnew(func.retnode.thing, func)[7:-3])
        self.indent()
        self.output('switch(__last_yield) {')
        self.indent()
        for (i,n) in enumerate(func.yieldNodes):
            self.output('case %d: goto __after_yield_%d;' % (i,i))
        self.output('default: break;')
        self.deindent()
        self.output('}')

        for child in func.node.code.getChildNodes():
            self.visit(child, func)
        self.output('throw new StopIteration();')
        self.deindent()
        self.output('}\n')

        self.deindent()
        self.output('};\n')

    def generator_body(self, func):
        self.output('return new __gen_%s(%s);\n' % (func.ident, ','.join([self.cpp_name(f) for f in func.formals]))) # XXX formals
        self.deindent()
        self.output('}\n')

    def visitYield(self, node, func):
        self.output('__last_yield = %d;' % func.yieldNodes.index(node))
        self.start()
        self.visitm('return ', node.value, func)
        self.eol()
        self.output('__after_yield_%d:;' % func.yieldNodes.index(node))
        self.start()
        
    def visitNot(self, node, func=None): 
        self.append('(!')
        if unboxable(self.mergeinh[node.expr]):
            self.visit(node.expr, func)
        else:
            self.visitm('___bool(', node.expr, ')', func)
        self.append(')')

    def visitBackquote(self, node, func=None):
        self.visit(inode(node.expr).fakefunc, func)

    def zeropointernone(self, node):
        return [t for t in self.mergeinh[node] if t[0].ident == 'none']

    def visitIf(self, node, func=None):
        for test in node.tests:
            self.start()
            if test == node.tests[0]:
                self.append('if (')
            else:
                self.append('else if (')

            self.bool_test(test[0], func)

            print >>self.out, self.line+') {'

            self.indent()
            self.visit(test[1], func)
            self.deindent()

            self.output('}')

        if node.else_:
            self.output('else {')
            self.indent()
            self.visit(node.else_, func)
            self.deindent()
            self.output('}')

    def visitIfExp(self, node, func=None):
        self.visitm('((', node.test, ')?(', node.then, '):(', node.else_, '))', func)

    def visitBreak(self, node, func=None):
        if getgx().loopstack[-1].else_ in getmv().tempcount:
            self.output('%s = 1;' % getmv().tempcount[getgx().loopstack[-1].else_])
        self.output('break;')

    def visitStmt(self, node, func=None):
        for b in node.nodes:
            if isinstance(b, Discard):
                if isinstance(b.expr, Const) and b.expr.value == None:
                    continue
                if isinstance(b.expr, Const) and type(b.expr.value) == str: 
                    self.do_comment(b.expr.value)
                    continue
                self.start('')
                self.visit(b, func)
                self.eol()
            else:
                self.visit(b, func)

    def visitOr(self, node, func=None):
        if not self.mixingboolean(node, '||', func): # allow type mixing, as result may not be used
            self.booleanOp(node, node.nodes, '__OR', func)

    def visitAnd(self, node, func=None):
        if not self.mixingboolean(node, '&&', func): # allow type mixing, as result may not be used
            self.booleanOp(node, node.nodes, '__AND', func)

    def mixingboolean(self, node, op, func):
        mixing = False
        for n in node.nodes:
            if self.booleancast(node, n, func) is None:
                mixing = True
        if not mixing: return False

        self.append('(')
        for n in node.nodes:
            if self.mergeinh[n] != set([(defclass('int_'),0)]):
                self.visitm('___bool(', n, ')', func)
            else:
                self.visit(n, func)
            if n != node.nodes[-1]:
                self.append(' '+op+' ')
        self.append(')')
        return True

    def booleancast(self, node, child, func=None):
        if typesetreprnew(child, func) == typesetreprnew(node, func):
            return '' # exactly the same types: no casting necessary
        elif assign_needs_cast(child, func, node, func) or (self.mergeinh[child] == set([(defclass('none'),0)]) and self.mergeinh[node] != set([(defclass('none'),0)])): # cast None or almost compatible types
            return '('+typesetreprnew(node, func)+')'
        else:
            return None # local dynamic typing

    def castup(self, node, child, func=None):
        cast = self.booleancast(node, child, func)
        if cast: self.visitm('('+cast, child, ')', func)
        else: self.visit(child, func)

    def booleanOp(self, node, nodes, op, func=None):
        if len(nodes) > 1:
            self.append(op+'(')
            self.castup(node, nodes[0], func)
            self.append(', ')
            self.booleanOp(node, nodes[1:], op, func)
            self.append(', '+getmv().tempcount[nodes[0]][2:]+')')
        else:
            self.castup(node, nodes[0], func)

    def visitCompare(self, node, func=None):
        if len(node.ops) > 1:
            self.append('(')

        self.done = set() # (tvar=fun())

        left = node.expr
        for op, right in node.ops:
            if op == '>': msg, short, pre = '__gt__', '>', None # XXX map = {}!
            elif op == '<': msg, short, pre = '__lt__', '<', None
            elif op == 'in': msg, short, pre = '__contains__', None, None
            elif op == 'not in': msg, short, pre = '__contains__', None, '!'
            elif op == '!=': msg, short, pre = '__ne__', '!=', None
            elif op == '==': msg, short, pre = '__eq__', '==', None
            elif op == 'is': msg, short, pre = None, '==', None
            elif op == 'is not': msg, short, pre = None, '!=', None
            elif op == '<=': msg, short, pre = '__le__', '<=', None
            elif op == '>=': msg, short, pre = '__ge__', '>=', None
            else: return

            # --- comparison to [], (): convert to ..->empty() # XXX {}, __ne__
            if msg in ['__eq__', '__ne__']:
                leftcl, rightcl = polymorphic_t(self.mergeinh[left]), polymorphic_t(self.mergeinh[right])

                if len(leftcl) == 1 and leftcl == rightcl and leftcl.pop().ident in ['list', 'tuple', 'tuple2', 'dict']:
                    for (a,b) in [(left, right), (right, left)]:
                        if isinstance(b, (List, Tuple, Dict)) and len(b.nodes) == 0:
                            if msg == '__ne__': self.append('!(')
                            self.visit2(a, func)
                            self.append('->empty()')
                            if msg == '__ne__': self.append(')')
                            return

            # --- 'x in range(n)' -> x > 0 && x < n # XXX not in, range(a,b)
            if msg == '__contains__':
                #op = node.ops[0][1] # XXX a in range(8): a doesn't have to be an int variable..; eval order
                if isinstance(right, CallFunc) and isinstance(right.node, Name) and right.node.name in ['range']: #, 'xrange']:
                    if len(right.args) == 1:
                        l, u = '0', right.args[0]
                    else:
                        l, u = right.args[0], right.args[1]
                    if pre: self.append(pre)
                    self.visitm('(', left, '>=', l, '&&', left, '<', u, ')', func)
                else:
                    self.visitBinary(right, left, msg, short, func, pre)

            else:
                self.visitBinary(left, right, msg, short, func, pre)

            if right != node.ops[-1][1]:
                self.append('&&')
            left = right

        if len(node.ops) > 1:
            self.append(')')

    def visitAugAssign(self, node, func=None):
        #print 'gen aug', node, inode(node).assignhop

        if isinstance(node.node, Subscript):
            self.start()
            if set([t[0].ident for t in self.mergeinh[node.node.expr] if isinstance(t[0], class_)]) in [set(['dict']), set(['defaultdict'])] and node.op == '+=':
                self.visitm(node.node.expr, '->__addtoitem__(', inode(node).subs, ', ', node.expr, ')', func)
                self.eol()
                return
            
            self.visitm(inode(node).temp1+' = ', node.node.expr, func)
            self.eol()
            self.start()
            self.visitm(inode(node).temp2+' = ', inode(node).subs, func)
            self.eol()
        self.visit(inode(node).assignhop, func)

    def visitAdd(self, node, func=None):
        str_nodes = self.rec_string_addition(node)
        if str_nodes and len(str_nodes) > 2:
            self.append('__add_strs(%d, ' % len(str_nodes))
            for (i, node) in enumerate(str_nodes):
                self.visit(node, func)
                if i < len(str_nodes)-1:
                    self.append(', ')
            self.append(')')
        else:
            self.visitBinary(node.left, node.right, augmsg(node, 'add'), '+', func)

    def rec_string_addition(self, node):
        if isinstance(node, Add):
            l, r = self.rec_string_addition(node.left), self.rec_string_addition(node.right)
            if l and r: 
                return l+r
        elif self.mergeinh[node] == set([(defclass('str_'),0)]):
            return [node]

        return None

    def visitBitand(self, node, func=None):
        self.visitBitop(node, augmsg(node, 'and'), '&', func)

    def visitBitor(self, node, func=None):
        self.visitBitop(node, augmsg(node, 'or'), '|', func)

    def visitBitxor(self, node, func=None):
        self.visitBitop(node, augmsg(node, 'xor'), '^', func)

    def visitBitop(self, node, msg, inline, func=None):
        self.visitBitpair(Bitpair(node.nodes, msg, inline), func)

    def visitBitpair(self, node, func=None):
        if len(node.nodes) == 1:
            self.visit(node.nodes[0], func)
        else:
            self.visitBinary(node.nodes[0], Bitpair(node.nodes[1:], node.msg, node.inline), node.msg, node.inline, func)

    def visitRightShift(self, node, func=None):
        self.visitBinary(node.left, node.right, augmsg(node, 'rshift'), '>>', func)

    def visitLeftShift(self, node, func=None):
        self.visitBinary(node.left, node.right, augmsg(node, 'lshift'), '<<', func)

    def visitMul(self, node, func=None):
        self.visitBinary(node.left, node.right, augmsg(node, 'mul'), '*', func)

    def visitDiv(self, node, func=None):
        self.visitBinary(node.left, node.right, augmsg(node, 'div'), '/', func)

    def visitInvert(self, node, func=None): # XXX visitUnarySub merge, template function __invert?
        if unboxable(self.mergeinh[node.expr]):
            self.visitm('~', node.expr, func)
        else:
            self.visitCallFunc(inode(node.expr).fakefunc, func)

    def visitFloorDiv(self, node, func=None):
        self.visitBinary(node.left, node.right, augmsg(node, 'floordiv'), '//', func)
        #self.visitm('__floordiv(', node.left, ', ', node.right, ')', func)

    def visitPower(self, node, func=None):
        self.power(node.left, node.right, None, func)

    def power(self, left, right, mod, func=None):
        if mod: self.visitm('__power(', left, ', ', right, ', ', mod, ')', func)
        else: 
            if self.mergeinh[left].intersection(set([(defclass('int_'),0),(defclass('float_'),0)])) and isinstance(right, Const) and type(right.value) == int and right.value in [2,3]:
                self.visitm(('__power%d(' % int(right.value)), left, ')', func)
            else:
                self.visitm('__power(', left, ', ', right, ')', func)

    def visitSub(self, node, func=None):
        self.visitBinary(node.left, node.right, augmsg(node, 'sub'), '-', func)

    def par(self, node, thingy):
        if (isinstance(node, Const) and not isinstance(node.value, (int, float))) or not isinstance(node, (Name, Const)):
            return thingy 
        return ''

    def visitBinary(self, left, right, middle, inline, func=None, prefix=''): # XXX cleanup please
        ltypes = self.mergeinh[left]
        #lclasses = set([t[0] for t in ltypes])
        origright = right
        if isinstance(right, Bitpair):
            right = right.nodes[0]
        rtypes = self.mergeinh[right]
        ul, ur = unboxable(ltypes), unboxable(rtypes)

        inttype = set([(defclass('int_'),0)]) # XXX new type?
        floattype = set([(defclass('float_'),0)]) # XXX new type?

        #print 'jow', left, right, ltypes, rtypes, middle, inline, inttype, floattype

        # --- inline mod/div
        if (floattype.intersection(ltypes) or inttype.intersection(ltypes)):
            if inline in ['%'] or (inline in ['/'] and not (floattype.intersection(ltypes) or floattype.intersection(rtypes))):
                if not defclass('complex') in [t[0] for t in rtypes]: # XXX
                    self.append({'%': '__mods', '/': '__divs'}[inline]+'(')
                    self.visit2(left, func)
                    self.append(', ')
                    self.visit2(origright, func)
                    self.append(')')
                    return

        # --- inline floordiv # XXX merge above?
        if (inline and ul and ur) and inline in ['//']:
            self.append({'//': '__floordiv'}[inline]+'(')
            self.visit2(left, func)
            self.append(',')
            self.visit2(right, func)
            self.append(')')
            return

        # --- inline other
        if (inline and ul and ur) or not middle or (isinstance(left, Name) and left.name == 'None') or (isinstance(origright, Name) and origright.name == 'None'): # XXX not middle, cleanup?
            self.append('(')
            self.visit2(left, func)
            self.append(inline)
            self.visit2(origright, func)
            self.append(')')
            return
            
        # --- prefix '!'
        postfix = '' 
        if prefix: 
            self.append('('+prefix)
            postfix = ')'

        # --- comparison
        if middle in ['__eq__', '__ne__', '__gt__', '__ge__', '__lt__', '__le__']:
            self.append(middle[:-2]+'(')
            self.visit2(left, func)
            self.append(', ')
            self.visit2(origright, func)
            self.append(')'+postfix)
            return
        
        # --- 1 +- ..j
        if inline in ['+', '-'] and isinstance(origright, Const) and isinstance(origright.value, complex):
            if floattype.intersection(ltypes) or inttype.intersection(ltypes):
                self.append('(new complex(')
                self.visit2(left, func)
                self.append(', '+{'+':'', '-':'-'}[inline]+str(origright.value.imag)+'))')
                return

        # --- 'a.__mul__(b)': use template to call to b.__mul__(a), while maintaining evaluation order
        if inline in ['+', '*', '-', '/'] and ul and not ur:
            self.append('__'+{'+':'add', '*':'mul', '-':'sub', '/':'div'}[inline]+'2(')
            self.visit2(left, func)
            self.append(', ')
            self.visit2(origright, func)
            self.append(')'+postfix)
            return

        # --- default: left, connector, middle, right
        self.append(self.par(left, '('))
        self.visit2(left, func)
        self.append(self.par(left, ')'))
        if middle == '==':
            self.append('==(')
        else:
            self.append(self.connector(left, func)+middle+'(')
        self.refer(origright, func, visit2=True) # XXX bleh
        self.append(')'+postfix)

    def visit2(self, node, func): # XXX use temp vars in comparisons, e.g. (t1=fun())
        if node in getmv().tempcount:
            if node in self.done:
                self.append(getmv().tempcount[node])
            else:
                self.visitm('('+getmv().tempcount[node]+'=', node, ')', func)
                self.done.add(node)
        else:
            self.visit(node, func)

    def visitUnarySub(self, node, func=None):
        self.visitm('(', func)
        if unboxable(self.mergeinh[node.expr]):
            self.visitm('-', node.expr, func)
        else:
            self.visitCallFunc(inode(node.expr).fakefunc, func)
        self.visitm(')', func)

    def visitUnaryAdd(self, node, func=None):
        self.visitm('(', func)
        if unboxable(self.mergeinh[node.expr]):
            self.visitm('+', node.expr, func)
        else:
            self.visitCallFunc(inode(node.expr).fakefunc, func)
        self.visitm(')', func)

    def refer(self, node, func, visit2=False):
        if isinstance(node, str):
            var = lookupvar(node, func)
            return node

        if isinstance(node, Name) and not node.name in ['None','True','False']:
            var = lookupvar(node.name, func)
        if visit2:
            self.visit2(node, func)
        else:
            self.visit(node, func)

    def library_func(self, funcs, modname, clname, funcname):
        for func in funcs:
            if not func.mv.module.builtin or func.mv.module.ident != modname:
                continue

            if clname != None:
                if not func.parent or func.parent.ident != clname:
                    continue

            return func.ident == funcname

        return False

    def add_args_arg(self, node, funcs):
        ''' append argument that describes which formals are actually filled in '''

        if self.library_func(funcs, 'datetime', 'time', 'replace') or \
           self.library_func(funcs, 'datetime', 'datetime', 'replace'):

            formals = funcs[0].formals[1:] # skip self
            formal_pos = dict([(v,k) for k,v in enumerate(formals)])
            positions = []

            for i, arg in enumerate(node.args):
                if isinstance(arg, Keyword):
                    positions.append(formal_pos[arg.name])
                else:
                    positions.append(i)

            if positions:
                self.append(str(reduce(lambda a,b: a|b, [(1<<x) for x in positions]))+', ')
            else:
                self.append('0, ')

    def visitCallFunc(self, node, func=None): 
        objexpr, ident, direct_call, method_call, constructor, mod_var, parent_constr = analyze_callfunc(node)
        funcs = callfunc_targets(node, self.mergeinh)

        if self.library_func(funcs, 're', None, 'findall') or \
           self.library_func(funcs, 're', 're_object', 'findall'):
            error("'findall' does not work with groups(use 'finditer' instead)", node, warning=True)

        if self.library_func(funcs, 'socket', 'socket', 'settimeout') or \
           self.library_func(funcs, 'socket', 'socket', 'gettimeout'):
            error("socket.set/gettimeout do not accept/return None", node, warning=True)

        if self.library_func(funcs, 'builtin', None, 'sorted'):
            if [arg for arg in node.args if isinstance(arg, Keyword) and arg.name=='key'] or \
               len([arg for arg in node.args if not isinstance(arg, Keyword)]) >= 3:
                error("'key' argument of 'sorted' is not supported", node, warning=True)

        if self.library_func(funcs, 'builtin', 'list', 'sort'):
            if [arg for arg in node.args if isinstance(arg, Keyword) and arg.name=='key'] or \
               len([arg for arg in node.args if not isinstance(arg, Keyword)]) >= 2:
                error("'key' argument of 'list.sort' is not supported", node, warning=True)

        # --- target expression

        if node.node in self.mergeinh and [t for t in self.mergeinh[node.node] if isinstance(t[0], function)]: # anonymous function
            self.visitm(node.node, '(', func)

        elif constructor:
            self.append('(new '+nokeywords(typesetreprnew(node, func)[:-2])+'(')
            if funcs and len(funcs[0].formals) == 1 and not funcs[0].mv.module.builtin: # XXX builtin
                self.append('1') # don't call default constructor

        elif parent_constr:
            cl = lookupclass(node.node.expr, getmv())
            self.append(namespaceclass(cl)+'::'+node.node.attrname+'(') 

        elif direct_call: # XXX no namespace (e.g., math.pow), check nr of args
            if ident == 'float' and node.args and self.mergeinh[node.args[0]] == set([(defclass('float_'), 0)]):
                self.visit(node.args[0], func)
                return
            if ident in ['abs', 'int', 'float', 'str', 'dict', 'tuple', 'list', 'type', 'cmp', 'sum']:
                self.append('__'+ident+'(')
            elif ident in ['iter', 'bool']:
                self.append('___'+ident+'(') # XXX
            elif ident == 'pow' and direct_call.mv.module.ident == 'builtin':
                if len(node.args)==3: third = node.args[2]
                else: third = None
                self.power(node.args[0], node.args[1], third, func)
                return
            elif ident == 'hash':
                self.append('hasher(') # XXX cleanup
            elif ident == 'isinstance' and isinstance(node.args[1], Name) and node.args[1].name in ['float','int']:
                error("'isinstance' cannot be used with ints or floats; assuming always true", node, warning=True)
                self.append('1')
                return
            elif ident == 'round':
                self.append('___round(')
            elif ident in ['min','max']:
                self.append('__'+ident+'(')
                if len(node.args) > 3:
                    self.append(str(len(node.args))+', ')
            else:
                if ident in self.module.mv.ext_funcs: # XXX using as? :P
                     ident = self.module.mv.ext_funcs[ident].ident

                if isinstance(node.node, Name): # XXX ugly
                    self.append(self.cpp_name(ident, func))
                else:
                    self.visit(node.node)
                self.append('(')

        elif method_call:
            for cl, _ in self.mergeinh[objexpr]:
                if cl.ident != 'none' and ident not in cl.funcs:
                    conv = {'int_': 'int', 'float_': 'float', 'str_': 'str', 'class_': 'class', 'none': 'none'}
                    clname = conv.get(cl.ident, cl.ident)
                    error("class '%s' has no method '%s'" % (clname, ident), node, warning=True)

            # tuple2.__getitem -> __getfirst__/__getsecond
            lcp = lowest_common_parents(polymorphic_t(self.mergeinh[objexpr]))
            if (ident == '__getitem__' and len(lcp) == 1 and lcp[0] == defclass('tuple2') and \
                isinstance(node.args[0], Const) and node.args[0].value in (0,1)):
                    self.visit(node.node.expr, func)
                    if node.args[0].value == 0:
                        self.append('->__getfirst__()')
                    else:
                        self.append('->__getsecond__()')
                    return

            self.visitm(node.node, '(', func)

        else:
            error("unbound identifier '"+ident+"'", node)

        if not funcs:
            if constructor: self.append(')')
            self.append(')')
            return

        # --- arguments 
        target = funcs[0] # XXX

        for f in funcs:
            if len(f.formals) != len(target.formals):
                error('calling functions with different numbers of arguments', node, warning=True)
                self.append(')')
                return

        if target.mv.module.builtin and target.mv.module.ident == 'path' and ident=='join': # XXX
            pairs = [(arg, target.formals[0]) for arg in node.args]
            self.append('%d, ' % len(node.args))
        elif ident in ['max','min']: 
            pairs = [(arg, target.formals[0]) for arg in node.args]
        elif target.mv.module.builtin and (ident == '__group' or ident.startswith('execl') or ident.startswith('spawnl')):
            self.append(str(len(node.args))+', ')
            pairs = [(arg, target.formals[0]) for arg in node.args]
        else:
            args = node.args
            if node.star_args:
                args = [node.star_args]+args
        
            pairs = connect_actual_formal(node, target, parent_constr, check_error=True)

            if constructor and ident=='defaultdict' and node.args:
                pairs = pairs[1:]

        double = False
        if ident in ['min', 'max']:
            for arg in node.args:
                if (defclass('float_'),0) in self.mergeinh[arg]:
                    double = True

        self.add_args_arg(node, funcs)

        for (arg, formal) in pairs:
            if isinstance(arg, tuple):
                # --- pack arguments as tuple
                self.append('new '+typesetreprnew(formal, target)[:-2]+'(')
                
                if len(arg) > 0: 
                    self.append(str(len(arg))+',')

                    # XXX merge with children args, as below
                    for a in arg:
                        self.refer(a, func)
                        if a != arg[-1]:
                            self.append(',')
                self.append(')')

            elif isinstance(formal, tuple):
                # --- unpack tuple 
                self.append(', '.join(['(*'+arg.name+')['+str(i)+']' for i in range(len(formal))]))

            else:
                # --- connect regular argument to formal
                cast = False
                if double and self.mergeinh[arg] == set([(defclass('int_'),0)]):
                    cast = True
                    self.append('((double)(')
                elif not target.mv.module.builtin and assign_needs_cast(arg, func, formal, target): # XXX builtin (dict.fromkeys?)
                    #print 'cast!', node, arg, formal
                    cast = True
                    self.append('(('+typesetreprnew(formal, target)+')(')

                if arg in target.mv.defaults: 
                    if self.mergeinh[arg] == set([(defclass('none'),0)]):
                        self.append('NULL')
                    elif target.mv.module == getmv().module:
                        self.append('default_%d' % (target.mv.defaults[arg]))
                    else:
                        self.append('%s::default_%d' % ('__'+'__::__'.join(target.mv.module.mod_path)+'__', target.mv.defaults[arg]))

                elif arg in self.consts:
                    self.append(self.consts[arg])
                else:
                    if constructor and ident in ['set', 'frozenset'] and typesetreprnew(arg, func) in ['list<void *> *', 'tuple<void *> *', 'pyiter<void *> *', 'pyseq<void *> *', 'pyset<void *>']: # XXX to needs_cast
                        pass # XXX assign_needs_cast
                    else:
                        self.refer(arg, func)

                if cast: self.append('))')

            if (arg, formal) != pairs[-1]:
                self.append(', ')

        if constructor and ident == 'frozenset':
            if pairs: self.append(',')
            self.append('1')
        self.append(')')
        if constructor:
            self.append(')')

    def visitReturn(self, node, func=None):
        if func.isGenerator:
            self.output('throw new StopIteration();')
            return

        self.start('return ')

        cast = False
        if assign_needs_cast(node.value, func, func.retnode.thing, func):
            #print 'cast!', node
            cast = True
            self.append('(('+typesetreprnew(func.retnode.thing, func)+')(')

        elif isinstance(node.value, Name) and node.value.name == 'self': # XXX integrate with assign_needs_cast!? # XXX self?
            lcp = lowest_common_parents(polymorphic_t(self.mergeinh[func.retnode.thing])) # XXX simplify
            if lcp:
                cl = lcp[0] # XXX simplify
                if not (cl == func.parent or cl in func.parent.ancestors()): 
                    self.append('('+cl.ident+' *)')

        self.visit(node.value, func)
        if cast: self.append('))')
        self.eol()

    def tuple_assign(self, lvalue, rvalue, func): 
        temp = getmv().tempcount[lvalue]

        if isinstance(lvalue, tuple): nodes = lvalue
        else: nodes = lvalue.nodes

        # --- nested unpacking assignment: a, (b,c) = d, e
        if [item for item in nodes if not isinstance(item, AssName)]:
            self.start(temp+' = ')
            if isinstance(rvalue, str):
                self.append(rvalue)
            else:
                self.visit(rvalue, func)
            self.eol()

            for i, item in enumerate(nodes):
                if i == 0: ident = '__getfirst__'
                elif i == 1: ident = '__getsecond__'
                else: ident = '__getitem__'
                arg = ''
                if ident == '__getitem__':
                    arg = str(i)
                selector = '%s->%s(%s)' % (temp, ident, arg)

                if isinstance(item, AssName):
                    if item.name != '_':
                        self.output('%s = %s;' % (item.name, selector)) 
                elif isinstance(item, (AssTuple, AssList)): # recursion
                    self.tuple_assign(item, selector, func)
                elif isinstance(item, Subscript):
                    self.assign_pair(item, selector, func) 
                elif isinstance(item, AssAttr):
                    self.assign_pair(item, selector, func) 
                    self.eol(' = '+selector)

        # --- non-nested unpacking assignment: a,b,c = d 
        else: 
            self.start()
            self.visitm(temp, ' = ', rvalue, func)
            self.eol()

            for (n, item) in enumerate(lvalue.nodes):
                if item.name != '_': 
                    self.start()
                    if isinstance(rvalue, Const): sel = '__getitem__(%d)' % n
                    elif len(lvalue.nodes) > 2: sel = '__getfast__(%d)' % n
                    elif n == 0: sel = '__getfirst__()' # XXX merge
                    else: sel = '__getsecond__()'
                    self.visitm(item, ' = ', temp, '->'+sel, func)
                    self.eol()
            
    def subs_assign(self, lvalue, func):
        if defclass('list') in [t[0] for t in self.mergeinh[lvalue.expr]]:
            #if isinstance(lvalue.expr, Name):
            self.append('ELEM((')
            self.refer(lvalue.expr, func)
            self.append('),')
            self.visit(lvalue.subs[0], func)
            self.append(')')

        else:
            if len(lvalue.subs) > 1:
                subs = inode(lvalue.expr).faketuple
            else:
                subs = lvalue.subs[0]
            self.visitm(lvalue.expr, self.connector(lvalue.expr, func), '__setitem__(', subs, ', ', func)

    def visitAssign(self, node, func=None):
        #print 'assign', node

        #temp vars
        if len(node.nodes) > 1 or isinstance(node.expr, Tuple):
            if isinstance(node.expr, Tuple):
                if [n for n in node.nodes if isinstance(n, AssTuple)]: # XXX a,b=d[i,j]=..?
                    for child in node.expr.nodes:
                        if not (child,0,0) in getgx().cnode: # (a,b) = (1,2): (1,2) never visited
                            continue
                        if not isinstance(child, Const) and not (isinstance(child, Name) and child.name == 'None'):
                            self.start(getmv().tempcount[child]+' = ')
                            self.visit(child, func)
                            self.eol()
            elif not isinstance(node.expr, Const) and not (isinstance(node.expr, Name) and node.expr.name == 'None'):
                self.start(getmv().tempcount[node.expr]+' = ')
                self.visit(node.expr, func)
                self.eol()

        # a = (b,c) = .. = expr
        right = node.expr
        for left in node.nodes:
            pairs = assign_rec(left, node.expr)
            tempvars = len(pairs) > 1

            for (lvalue, rvalue) in pairs:
                cast = None
                self.start('') # XXX remove?
                
                # expr[expr] = expr
                if isinstance(lvalue, Subscript) and not isinstance(lvalue.subs[0], Sliceobj):
                    self.assign_pair(lvalue, rvalue, func)
                    continue

                # expr.attr = expr
                elif isinstance(lvalue, AssAttr):
                    lcp = lowest_common_parents(polymorphic_t(self.mergeinh[lvalue.expr]))
                    # property
                    if len(lcp) == 1 and isinstance(lcp[0], class_) and lvalue.attrname in lcp[0].properties:
                        self.visitm(lvalue.expr, '->'+self.cpp_name(lcp[0].properties[lvalue.attrname][1])+'(', rvalue, ')', func)
                        self.eol()
                        continue
                    cast = self.var_assign_needs_cast(lvalue, rvalue, func) 
                    self.assign_pair(lvalue, rvalue, func)
                    self.append(' = ')

                # name = expr
                elif isinstance(lvalue, AssName):
                    if lvalue.name != '_': # XXX 
                        cast = self.var_assign_needs_cast(lvalue, rvalue, func) 
                        self.visit(lvalue, func)
                        self.append(' = ')

                # (a,(b,c), ..) = expr
                elif isinstance(lvalue, (AssTuple, AssList)):
                    self.tuple_assign(lvalue, rvalue, func)
                    continue
            
                # expr[a:b] = expr
                elif isinstance(lvalue, Slice):
                    if isinstance(rvalue, Slice) and lvalue.upper == rvalue.upper == None and lvalue.lower == rvalue.lower == None:
                        self.visitm(lvalue.expr, self.connector(lvalue.expr, func), 'units = ', rvalue.expr, self.connector(rvalue.expr, func), 'units', func)
                    else:
                        fakefunc = inode(lvalue.expr).fakefunc
                        self.visitm('(', fakefunc.node.expr, ')->__setslice__(', fakefunc.args[0], ',', fakefunc.args[1], ',', fakefunc.args[2], ',', fakefunc.args[3], ',', func)
                        cast = self.var_assign_needs_cast(lvalue.expr, rvalue, func)
                        if cast: self.visitm('(('+cast+')', fakefunc.args[4], '))', func) 
                        else: self.visitm(fakefunc.args[4], ')', func)
                    self.eol()
                    continue

                # expr[a:b:c] = expr
                elif isinstance(lvalue, Subscript) and isinstance(lvalue.subs[0], Sliceobj):
                    self.visit(inode(lvalue.expr).fakefunc, func)
                    self.eol()
                    continue

                # rvalue, optionally with cast
                if cast: 
                    self.append('(('+cast+')(')
                if rvalue in getmv().tempcount:
                    self.append(getmv().tempcount[rvalue])
                else:
                    self.visit(rvalue, func)
                if cast: self.append('))')

                self.eol()

    def var_assign_needs_cast(self, expr, rvalue, func):
        cast = None
        if isinstance(expr, AssName):
            var = lookupvar(expr.name, func)
            if assign_needs_cast(rvalue, func, var, func):
                cast = typesetreprnew(var, func)
        elif isinstance(expr, AssAttr):
            lcp = lowest_common_parents(polymorphic_t(self.mergeinh[expr.expr]))
            if len(lcp) == 1 and isinstance(lcp[0], class_):
                var = lookupvar(expr.attrname, lcp[0])
                if assign_needs_cast(rvalue, func, var, lcp[0]):
                    cast = typesetreprnew(var, lcp[0])
        else:
            if assign_needs_cast(rvalue, func, expr, func):
                cast = typesetreprnew(expr, func)
        return cast

    def assign_pair(self, lvalue, rvalue, func):
        self.start('')

        # expr[expr] = expr
        if isinstance(lvalue, Subscript) and not isinstance(lvalue.subs[0], Sliceobj):
            self.subs_assign(lvalue, func)
            if defclass('list') in [t[0] for t in self.mergeinh[lvalue.expr]]:
                self.append(' = ')

            if isinstance(rvalue, str):
                self.append(rvalue)
            elif rvalue in getmv().tempcount:
                self.append(getmv().tempcount[rvalue])
            else:
                self.visit(rvalue, func)

            if not defclass('list') in [t[0] for t in self.mergeinh[lvalue.expr]]:
                self.append(')')
            self.eol()

        # expr.x = expr
        elif isinstance(lvalue, AssAttr):
            self.visitAssAttr(lvalue, func)

    def listcomp_func(self, node):
        # --- [x*y for (x,y) in z if c]
        lcfunc, func = self.listcomps[node]

        # --- formals: target, z if not Name, out-of-scopes 
        args = []

        for name in lcfunc.misses:
            if lookupvar(name, func).parent:
                args.append(typesetreprnew(lookupvar(name, lcfunc), lcfunc)+self.cpp_name(name))

        ts = typesetreprnew(node, lcfunc) 
        if not ts.endswith('*'): ts += ' '
        self.output('static inline '+ts+lcfunc.ident+'('+', '.join(args)+') {')
        self.indent()

        # --- local: (x,y), result
        decl = {}
        for (name,var) in lcfunc.vars.items(): # XXX merge with visitFunction 
            name = self.cpp_name(name)
            decl.setdefault(typesetreprnew(var, lcfunc), []).append(name)
        for ts, names in decl.items():
            if ts.endswith('*'):
                self.output(ts+', *'.join(names)+';')
            else:
                self.output(ts+', '.join(names)+';')

        self.output(typesetreprnew(node, lcfunc)+'result = new '+typesetreprnew(node, lcfunc)[:-2]+'();')
        print >>self.out
         
        self.listcomp_rec(node, node.quals, lcfunc)
      
        # --- return result
        self.output('return result;')
        self.deindent();
        self.output('}\n')

    def fastfor_switch(self, node, func):
        self.start()
        for arg in node.list.args:
            if arg in getmv().tempcount:
                self.start()
                self.visitm(getmv().tempcount[arg], ' = ', arg, func)
                self.eol()
        self.start('if(')
        if node.list.args[2] in getmv().tempcount:
            self.append(getmv().tempcount[node.list.args[2]])
        else:
            self.visit(node.list.args[2])
        self.append('>0) {')
        print >>self.out, self.line

    # --- nested for loops: loop headers, if statements
    def listcomp_rec(self, node, quals, lcfunc):
        if not quals:
            if len(node.quals) == 1 and not fastfor(node.quals[0]) and not node.quals[0].ifs and not [t for t in self.mergeinh[node.quals[0].list] if t[0] not in (defclass('tuple'), defclass('list'))]:
                self.start('result->units['+getmv().tempcount[node.quals[0]]+'] = ')
                self.visit(node.expr, lcfunc)
            else:
                self.start('result->append(')
                self.visit(node.expr, lcfunc)
                self.append(')')
            self.eol()
            return

        qual = quals[0]

        # iter var
        if isinstance(qual.assign, AssName):
            if qual.assign.name != '_':
                var = lookupvar(qual.assign.name, lcfunc)
            else:
                var = lookupvar(getmv().tempcount[(qual.assign,1)], lcfunc)
        else:
            var = lookupvar(getmv().tempcount[qual.assign], lcfunc)

        iter = self.cpp_name(var.name)

        # for in
        if fastfor(qual):
            if len(qual.list.args) == 3 and not const_literal(qual.list.args[2]):
                self.fastfor_switch(qual, lcfunc)
                self.indent()
                self.fastfor(qual, iter, '', lcfunc)
                self.listcompfor_body(node, quals, iter, lcfunc)
                self.deindent()
                self.output('} else {')
                self.indent()
                self.fastfor(qual, iter, '_NEG', lcfunc)
                self.listcompfor_body(node, quals, iter, lcfunc)
                self.deindent()
                self.output('}')
            else:
                neg=''
                if len(qual.list.args) == 3 and const_literal(qual.list.args[2]) and isinstance(qual.list.args[2], UnarySub): 
                    neg = '_NEG'
                self.fastfor(qual, iter, neg, lcfunc)
                self.listcompfor_body(node, quals, iter, lcfunc)

        else:
            pref = ''
            if not [t for t in self.mergeinh[qual.list] if t[0] not in (defclass('tuple'), defclass('list'))]:
                pref = '_SEQ'

            if not isinstance(qual.list, Name):
                itervar = getmv().tempcount[qual.list]
                self.start('')
                self.visitm(itervar, ' = ', qual.list, lcfunc)
                self.eol()
            else:
                itervar = self.cpp_name(qual.list.name)

            if len(node.quals) == 1 and not qual.ifs and pref == '_SEQ':
                self.output('result->resize(len('+itervar+'));')

            if pref == '': tail = getmv().tempcount[(qual,1)][2:]
            else: tail = getmv().tempcount[qual.list][2:]+','+getmv().tempcount[qual][2:]

            self.start('FOR_IN'+pref+'('+iter+','+itervar+','+tail)
            print >>self.out, self.line+')'

            self.listcompfor_body(node, quals, iter, lcfunc)

    def listcompfor_body(self, node, quals, iter, lcfunc):
        qual = quals[0]

        self.indent()

        if isinstance(qual.assign, (AssTuple, AssList)):
            self.tuple_assign(qual.assign, iter, lcfunc)

        # if statements
        if qual.ifs: 
            self.start('if (')
            self.indent()
            for cond in qual.ifs:
                self.bool_test(cond.test, lcfunc)
                if cond != qual.ifs[-1]:
                    self.append(' && ')
            self.append(') {')
            print >>self.out, self.line

        # recurse
        self.listcomp_rec(node, quals[1:], lcfunc)

        # --- nested for loops: loop tails
        if qual.ifs: 
            self.deindent();
            self.output('}')
        self.deindent();
        self.output('END_FOR\n')

    def visitListComp(self, node, func=None): #, target=None):
        lcfunc, _ = self.listcomps[node]
        args = []
        temp = self.line

        for name in lcfunc.misses:
            var = lookupvar(name, func)
            if var.parent:
                if name == 'self' and not func.listcomp: # XXX parent?
                    args.append('this')
                else:
                    args.append(self.cpp_name(name))

        self.line = temp
        self.append(lcfunc.ident+'('+', '.join(args)+')')

    def visitSubscript(self, node, func=None):
        if node.flags == 'OP_DELETE':
            self.start()
            if isinstance(node.subs[0], Sliceobj):
                self.visitCallFunc(inode(node.expr).fakefunc, func)
                self.eol()
                return

            self.visitCallFunc(inode(node.expr).fakefunc, func)
            #self.visitm(node.expr, '->__delitem__(', node.subs[0], ')', func) # XXX
            self.eol()
            return

        self.visitCallFunc(inode(node.expr).fakefunc, func)
        return

    def visitMod(self, node, func=None):
        # --- non-str % ..
        if [t for t in getgx().merged_inh[node.left] if t[0].ident != 'str_']:
            self.visitBinary(node.left, node.right, '__mod__', '%', func)
            return

        # --- str % non-constant dict/tuple
        if not isinstance(node.right, (Tuple, Dict)) and node.right in getgx().merged_inh: # XXX
            if [t for t in getgx().merged_inh[node.right] if t[0].ident == 'dict']: 
                self.visitm('__moddict(', node.left, ', ', node.right, ')', func)
                return
            elif [t for t in getgx().merged_inh[node.right] if t[0].ident in ['tuple', 'tuple2']]: 
                self.visitm('__modtuple(', node.left, ', ', node.right, ')', func)
                return

        # --- str % constant-dict: 
        if isinstance(node.right, Dict): # XXX geen str keys
            self.visitm('__modcd(', node.left, ', ', 'new list<str *>(%d, ' % len(node.right.items), func)
            self.append(', '.join([('new str("%s")' % key.value) for key, value in node.right.items]))
            self.append(')')
            nodes = [value for (key,value) in node.right.items]
        else:
            self.visitm('__modct(', node.left, func)
            # --- str % constant-tuple
            if isinstance(node.right, Tuple):
                nodes = node.right.nodes

            # --- str % non-tuple/non-dict
            else:
                nodes = [node.right]
            self.append(', %d' % len(nodes))

        # --- visit nodes, boxing scalars
        for n in nodes: 
            if (defclass('float_'), 0) in self.mergeinh[n] or (defclass('int_'), 0) in self.mergeinh[n]:
                self.visitm(', __box(', n, ')', func)
            else:
                self.visitm(', ', n, func)
        self.append(')')

    def visitPrintnl(self, node, func=None):
        self.visitPrint(node, func, '\\n')

    def visitPrint(self, node, func=None, newline=None):
        if newline: self.start('print(')
        else: self.start('printc(')
        if node.dest:
            self.visitm(node.dest, ', ', func)
        self.append(str(len(node.nodes)))
        for n in node.nodes:
            types = [t[0].ident for t in self.mergeinh[n]]
            if 'float_' in types or 'int_' in types:
                self.visitm(', __box(', n, ')', func)
            else:
                self.visitm(', ', n, func)
        self.eol(')')

    def visitGetattr(self, node, func=None):
        cl, module = lookup_class_module(node.expr, inode(node).mv, func)

        # module.attr
        if module: 
            self.append(namespace(module)+'::') 

        # class.attr: staticmethod
        elif cl and node.attrname in cl.staticmethods: 
            ident = cl.ident
            if cl.ident in ['dict', 'defaultdict']: # own namespace because of template vars
                self.append('__'+cl.ident+'__::')
            elif isinstance(node.expr, Getattr):
                submod = lookupmodule(node.expr.expr, inode(node).mv)
                self.append(namespace(submod)+'::'+ident+'::')
            else:
                self.append(ident+'::')

        # class.attr
        elif cl: # XXX merge above?
            ident = cl.ident
            if isinstance(node.expr, Getattr):
                submod = lookupmodule(node.expr.expr, inode(node).mv)
                self.append(namespace(submod)+'::'+cl.cpp_name+'::')
            else:
                self.append(ident+'::')

        # obj.attr
        else:
            if not isinstance(node.expr, (Name)):
                self.append('(')
            if isinstance(node.expr, Name) and not lookupvar(node.expr.name, func): # XXX XXX
                self.append(node.expr.name)
            else:
                self.visit(node.expr, func)
            if not isinstance(node.expr, (Name)):
                self.append(')')

            self.append(self.connector(node.expr, func))

        ident = node.attrname

        # property
        lcp = lowest_common_parents(polymorphic_t(self.mergeinh[node.expr]))
        if len(lcp) == 1 and isinstance(lcp[0], class_) and node.attrname in lcp[0].properties:
            self.append(self.cpp_name(lcp[0].properties[node.attrname][0])+'()')
            return

        # getfast
        if ident == '__getitem__':
            lcp = lowest_common_parents(polymorphic_t(self.mergeinh[node.expr]))
            if len(lcp) == 1 and lcp[0] == defclass('list'):
                ident = '__getfast__'

        self.append(self.cpp_name(ident))

    def visitAssAttr(self, node, func=None): # XXX merge with visitGetattr
        cl, module = lookup_class_module(node.expr, inode(node).mv, func)

        # module.attr
        if module:
            self.append(namespace(module)+'::')

        # class.attr
        elif cl: 
            if isinstance(node.expr, Getattr):
                submod = lookupmodule(node.expr.expr, inode(node).mv)
                self.append(namespace(submod)+'::'+cl.cpp_name+'::')
            else:
                self.append(cl.ident+'::')

        # obj.attr
        else:
            if isinstance(node.expr, Name) and not lookupvar(node.expr.name, func): # XXX
                self.append(node.expr.name)
            else:
                self.visit(node.expr, func)
            self.append(self.connector(node.expr, func)) # XXX '->'

        self.append(self.cpp_name(node.attrname))

    def visitAssName(self, node, func=None):
        self.append(self.cpp_name(node.name))

    def visitName(self, node, func=None, add_cl=True):
        map = {'True': '1', 'False': '0', 'self': 'this'}
        if node.name == 'None':
            self.append('NULL')
        elif node.name == 'self' and ((func and func.listcomp) or not isinstance(func.parent, class_)):
            self.append('self')
        elif node.name in map:
            self.append(map[node.name])

        else: # XXX clean up
            if not self.mergeinh[node] and not inode(node).parent in getgx().inheritance_relations:
                error("variable '"+node.name+"' has no type", node, warning=True)
                self.append(node.name)
            elif singletype(node, module):
                self.append('__'+singletype(node, module).ident+'__')
            else:
                if (defclass('class_'),0) in self.mergeinh[node]:
                    self.append('cl_'+node.name)
                elif add_cl and [t for t in self.mergeinh[node] if isinstance(t[0], static_class)]:
                    self.append('cl_'+node.name)
                else:
                    self.append(self.cpp_name(node.name))
                
    def expandspecialchars(self, value):
        value = list(value)
        replace = dict(['\\\\', '\nn', '\tt', '\rr', '\ff', '\bb', '\vv', '""'])

        for i in range(len(value)):
            if value[i] in replace: 
                value[i] = '\\'+replace[value[i]]
            elif value[i] not in string.printable:
                value[i] = '\\'+oct(ord(value[i])).zfill(4)[1:]
             
        return ''.join(value)

    def visitConst(self, node, func=None):
        if not self.filling_consts and isinstance(node.value, str): 
            self.append(self.get_constant(node))
            return

        if node.value == None: 
            self.append('NULL')
            return

        t = list(inode(node).types())[0]

        if t[0].ident == 'int_':
            self.append(str(node.value)) 
        elif t[0].ident == 'float_': 
            if str(node.value) in ['inf', '1.#INF', 'Infinity']: self.append('INFINITY')
            elif str(node.value) in ['-inf', '-1.#INF', 'Infinity']: self.append('-INFINITY')
            else: self.append(str(node.value)) 
        elif t[0].ident == 'str_': 
            self.append('new str("%s"' % self.expandspecialchars(node.value))
            if '\0' in node.value: # '\0' delimiter in C
                self.append(', %d' % len(node.value))
            self.append(')')
        elif t[0].ident == 'complex': 
            self.append('new complex(%s, %s)' % (node.value.real, node.value.imag))
        else: 
            self.append('new %s(%s)' % (t[0].ident, node.value))

# --- helper functions

def singletype(node, type):
    types = [t[0] for t in inode(node).types()]
    if len(types) == 1 and isinstance(types[0], type):
        return types[0]
    return None

def singletype2(types, type):
    ltypes = list(types)
    if len(types) == 1 and isinstance(ltypes[0][0], type):
        return ltypes[0][0]
    return None

def namespace(module):
    return '__'+'__::__'.join(module.mod_path)+'__'

def namespaceclass(cl):
    module = cl.mv.module 

    if module.ident != 'builtin' and module != getmv().module and module.mod_path:  
        return namespace(module)+'::'+nokeywords(cl.ident)
    else: 
        return nokeywords(cl.ident)

# --- determine representation of node type set (within parameterized context)
def typesetreprnew(node, parent, cplusplus=True, check_extmod=False):
    orig_parent = parent
    while is_listcomp(parent): # XXX redundant with typesplit?
        parent = parent.parent

    # --- separate types in multiple duplicates, so we can do parallel template matching of subtypes..
    split = typesplit(node, parent)

    # --- use this 'split' to determine type representation
    try:
        ts = typestrnew(split, parent, cplusplus, orig_parent, node, check_extmod) 
    except RuntimeError:
        if not hasattr(node, 'lineno'): node.lineno = None # XXX
        if not getmv().module.builtin and isinstance(node, variable) and not node.name.startswith('__'): # XXX startswith
            error("variable %s has dynamic (sub)type" % repr(node), warning=True)
        ts = 'ERROR'

    if cplusplus: 
        if not ts.endswith('*'): ts += ' '
        return ts
    return '['+ts+']'

class ExtmodError(Exception):
    pass

def typestrnew(split, root_class, cplusplus, orig_parent, node=None, check_extmod=False, depth=0):
    #print 'typestrnew', split, root_class
    if depth==10:
        raise RuntimeError()

    # --- annotation or c++ code
    conv1 = {'int_': 'int', 'float_': 'double', 'str_': 'str', 'none': 'int'}
    conv2 = {'int_': 'int', 'float_': 'float', 'str_': 'str', 'class_': 'class', 'none': 'None'}
    if cplusplus: sep, ptr, conv = '<>', ' *', conv1
    else: sep, ptr, conv = '()', '', conv2

    def map(ident):
        if cplusplus: return ident+' *'
        return conv.get(ident, ident)

    # --- examine split
    alltypes = set() # XXX
    for (dcpa, cpa), types in split.items():
        alltypes.update(types)

    anon_funcs = set([t[0] for t in alltypes if isinstance(t[0], function)])
    if anon_funcs and check_extmod:
        raise ExtmodError()
    if anon_funcs:
        f = anon_funcs.pop()
        if not f in getmv().lambda_signum: # XXX method reference
            return '__method_ref_0'
        return 'lambda'+str(getmv().lambda_signum[f])

    classes = polymorphic_cl(split_classes(split))
    lcp = lowest_common_parents(classes)

    # --- multiple parent classes
    if len(lcp) > 1:              
        if set(lcp) == set([defclass('int_'),defclass('float_')]):
            return conv['float_']
        if inode(node).mv.module.builtin:
            return '***ERROR*** '
        if isinstance(node, variable):
            if not node.name.startswith('__') : # XXX startswith
                if orig_parent: varname = "%s" % node
                else: varname = "'%s'" % node
                error("variable %s has dynamic (sub)type: {%s}" % (varname, ', '.join([conv2.get(cl.ident, cl.ident) for cl in lcp])), warning=True)
        elif not isinstance(node, (Or,And)):
            error("expression has dynamic (sub)type: {%s}" % ', '.join([conv2.get(cl.ident, cl.ident) for cl in lcp]), node, warning=True)

    elif not classes:
        if cplusplus: return 'void *'
        return ''

    cl = lcp.pop() 

    if check_extmod and cl.mv.module.builtin and not (cl.mv.module.ident == 'builtin' and cl.ident in ['int_', 'float_', 'complex', 'str_', 'list', 'tuple', 'tuple2', 'dict', 'set', 'frozenset', 'none']):
        raise ExtmodError()

    # --- simple built-in types
    if cl.ident in ['int_', 'float_']:
        return conv[cl.ident]
    elif cl.ident == 'str_':
        return 'str'+ptr 
    elif cl.ident == 'none':
        if cplusplus: return 'void *'
        return 'None'
            
    # --- namespace prefix
    namespace = ''
    if cl.module not in [getmv().module, getgx().modules['builtin']] and not (cl.ident in getmv().ext_funcs or cl.ident in getmv().ext_classes):
        if cplusplus: namespace = '__'+'__::__'.join([n for n in cl.module.mod_path])+'__::'
        else: namespace = '::'.join([n for n in cl.module.mod_path])+'::'

        if cl.module.filename.endswith('__init__.py'): # XXX only pass cl.module
            include = '/'.join(cl.module.mod_path)+'/__init__.hpp'
        else:
            include = '/'.join(cl.module.mod_path)+'.hpp'
        getmv().module.prop_includes.add(include)

    template_vars = cl.tvar_names()
    if template_vars:
        subtypes = [] 
        for tvar in template_vars:
            subsplit = split_subsplit(split, tvar)
            subtypes.append(typestrnew(subsplit, root_class, cplusplus, orig_parent, node, check_extmod, depth+1))
    else:
        if cl.ident in getgx().cpp_keywords:
            return namespace+getgx().ss_prefix+map(cl.ident)
        return namespace+map(cl.ident)

    ident = cl.ident

    # --- binary tuples
    if ident == 'tuple2':
        if subtypes[0] == subtypes[1]:
            ident, subtypes = 'tuple', [subtypes[0]]
    if ident == 'tuple2' and not cplusplus:
        ident = 'tuple'
    elif ident == 'tuple' and cplusplus:
        return namespace+'tuple2'+sep[0]+subtypes[0]+', '+subtypes[0]+sep[1]+ptr

    if ident in ['frozenset', 'pyset'] and cplusplus:
        ident = 'set'
        
    if ident in getgx().cpp_keywords:
        ident = getgx().ss_prefix+ident

    # --- final type representation
    return namespace+ident+sep[0]+', '.join(subtypes)+sep[1]+ptr

# --- separate types in multiple duplicates
def typesplit(node, parent):
    split = {} 

    if isinstance(parent, function) and parent in getgx().inheritance_relations: 
        if node in getgx().merged_inh:
            split[1,0] = getgx().merged_inh[node]
        return split

    while is_listcomp(parent): 
        parent = parent.parent

    if isinstance(parent, class_): # class variables
        for dcpa in range(1, parent.dcpa):
            if (node, dcpa, 0) in getgx().cnode:
                split[dcpa, 0] = getgx().cnode[node, dcpa, 0].types()

    elif isinstance(parent, function):
        if isinstance(parent.parent, class_): # method variables/expressions (XXX nested functions)
            for dcpa in range(1, parent.parent.dcpa):
                if dcpa in parent.cp:
                    for cpa in range(len(parent.cp[dcpa])): 
                        if (node, dcpa, cpa) in getgx().cnode:
                            split[dcpa, cpa] = getgx().cnode[node, dcpa, cpa].types()

        else: # function variables/expressions
            if 0 in parent.cp:
                for cpa in range(len(parent.cp[0])): 
                    if (node, 0, cpa) in getgx().cnode:
                        split[0, cpa] = getgx().cnode[node, 0, cpa].types()
    else:
        split[0, 0] = inode(node).types()

    return split

def polymorphic_cl(classes):
    cls = set([cl for cl in classes])
    if len(cls) > 1 and defclass('none') in cls and not defclass('int_') in cls and not defclass('float_') in cls:
        cls.remove(defclass('none'))
#    if defclass('float_') in cls and defclass('int_') in cls:
#        cls.remove(defclass('int_'))
    if defclass('tuple2') in cls and defclass('tuple') in cls: # XXX hmm
        cls.remove(defclass('tuple2'))
    return cls

def split_classes(split):
    alltypes = set()
    for (dcpa, cpa), types in split.items():
        alltypes.update(types)

    return set([t[0] for t in alltypes if isinstance(t[0], class_)])
    
# --- determine lowest common parent classes (inclusive)
def lowest_common_parents(classes):
    lcp = set(classes)

    changed = 1
    while changed:
        changed = 0
        for cl in getgx().allclasses:
             desc_in_classes = [[c for c in ch.descendants(inclusive=True) if c in lcp] for ch in cl.children]
             if len([d for d in desc_in_classes if d]) > 1:
                 for d in desc_in_classes:
                     lcp.difference_update(d)
                 lcp.add(cl)
                 changed = 1

    for cl in lcp.copy():
        if isinstance(cl, class_): # XXX
            lcp.difference_update(cl.descendants())

    result = [] # XXX there shouldn't be doubles
    for cl in lcp:
        if cl.ident not in [r.ident for r in result]:
            result.append(cl)
    return result

def hmcpa(func): 
    got_one = 0
    for dcpa, cpas in func.cp.items():
        if len(cpas) > 1: return len(cpas)
        if len(cpas) == 1: got_one = 1
    return got_one
    
# --- assignment (incl. passing arguments, returning values) may require a cast 
def assign_needs_cast(arg, func, formal, target):
    argsplit = typesplit(arg, func)
    formalsplit = typesplit(formal, target)

    return assign_needs_cast_rec(argsplit, func, formalsplit, target)

def assign_needs_cast_rec(argsplit, func, formalsplit, target):
    argclasses = split_classes(argsplit)
    formalclasses = split_classes(formalsplit)
 
    # void * 
    noneset = set([defclass('none')])
    if argclasses == noneset and formalclasses != noneset:
        return True

    # no type 
    if not argclasses and formalclasses: # a = [[]]
        return True

    if defclass('none') in formalclasses:
        formalclasses.remove(defclass('none'))

    if len(formalclasses) != 1:
        return False

    cl = formalclasses.pop()

    tvars = cl.tvar_names()
    if tvars:
        for tvar in tvars:
            argsubsplit = split_subsplit(argsplit, tvar)
            formalsubsplit = split_subsplit(formalsplit, tvar)

            if assign_needs_cast_rec(argsubsplit, func, formalsubsplit, target):
                return True

    return False

def split_subsplit(split, varname):
    subsplit = {}
    for (dcpa, cpa), types in split.items():
        subsplit[dcpa, cpa] = set()
        for t in types:
            if not varname in t[0].vars: # XXX 
                continue
            var = t[0].vars[varname]
            if (var, t[1], 0) in getgx().cnode: # XXX yeah?
                subsplit[dcpa, cpa].update(getgx().cnode[var, t[1], 0].types())
    return subsplit

def polymorphic_t(types):
    return polymorphic_cl([t[0] for t in types])

# --- number classes with low and high numbers, to enable constant-time subclass check
def number_classes():
    counter = 0
    for cl in getgx().allclasses:
        if not cl.bases: 
            counter = number_class_rec(cl, counter+1)

def number_class_rec(cl, counter):
    cl.low = counter
    for child in cl.children:
        counter = number_class_rec(child, counter+1)
    cl.high = counter
    return counter

class Bitpair:
    def __init__(self, nodes, msg, inline):
        self.nodes = nodes
        self.msg = msg
        self.inline = inline

def unboxable(types):
    if not isinstance(types, set):
        types = inode(types).types()
    classes = set([t[0] for t in types])

    if [cl for cl in classes if cl.ident not in ['int_','float_']]:
        return None
    else:
        if classes:
            return classes.pop().ident
        return None

def get_includes(mod):
    imports = set()
    if mod == getgx().main_module:
        mods = getgx().modules.values()
    else:
        d = mod.mv.imports.copy()
        d.update(mod.mv.fake_imports)
        mods = d.values()

    for mod in mods:
        if mod.filename.endswith('__init__.py'): # XXX
            imports.add('/'.join(mod.mod_path)+'/__init__.hpp')
        else:
            imports.add('/'.join(mod.mod_path)+'.hpp')
    return imports

def subclass(a, b):
    if b in a.bases:
        return True
    else:
        return a.bases and subclass(a.bases[0], b) # XXX mult inh

# --- determine virtual methods and variables
def analyze_virtuals(): 
    for node in getgx().merged_inh: # XXX all:
        # --- for every message
        if isinstance(node, CallFunc) and not inode(node).mv.module.builtin: #ident == 'builtin':
            objexpr, ident, direct_call, method_call, constructor, mod_var, parent_constr = analyze_callfunc(node)
            if not method_call or objexpr not in getgx().merged_inh: 
                continue # XXX

            # --- determine abstract receiver class
            classes = polymorphic_t(getgx().merged_inh[objexpr]) 
            if not classes:
                continue

            if isinstance(objexpr, Name) and objexpr.name == 'self': 
                abstract_cl = inode(objexpr).parent.parent
            else:
                lcp = lowest_common_parents(classes)
                lcp = [x for x in lcp if isinstance(x, class_)] # XXX 
                if not lcp:
                    continue
                abstract_cl = lcp[0] 

            if not abstract_cl or not isinstance(abstract_cl, class_):
                continue 
            subclasses = [cl for cl in classes if subclass(cl, abstract_cl)] 

            # --- register virtual method
            if not ident.startswith('__'):  
                redefined = False
                for concrete_cl in classes:
                    if [cl for cl in concrete_cl.ancestors_upto(abstract_cl) if ident in cl.funcs and not cl.funcs[ident].inherited]:
                        redefined = True

                if redefined:
                    abstract_cl.virtuals.setdefault(ident, set()).update(subclasses)

            # --- register virtual var
            elif ident in ['__getattr__','__setattr__'] and subclasses:      
                var = defaultvar(node.args[0].value, abstract_cl)
                abstract_cl.virtualvars.setdefault(node.args[0].value, set()).update(subclasses)

# --- merge variables assigned to via 'self.varname = ..' in inherited methods into base class
def upgrade_variables():
    for node, inheritnodes in getgx().inheritance_relations.items():
        if isinstance(node, AssAttr): 
            baseclass = inode(node).parent.parent
            inhclasses = [inode(x).parent.parent for x in inheritnodes]
            var = defaultvar(node.attrname, baseclass)

            for inhclass in inhclasses:
                inhvar = lookupvar(node.attrname, inhclass)

                if (var, 1, 0) in getgx().cnode:
                    newnode = getgx().cnode[var,1,0]
                else:
                    newnode = cnode(var, 1, 0, parent=baseclass)
                    getgx().types[newnode] = set()

                if inhvar in getgx().merged_all: # XXX ?
                    getgx().types[newnode].update(getgx().merged_all[inhvar])

def nokeywords(name):
    if name in getgx().cpp_keywords:
        return getgx().ss_prefix+name
    return name
