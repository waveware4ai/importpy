r"""
# importpy v0.1.0 20250711
by 14mhz@hanmail.net, zookim@waveware.co.kr

This small package is used to import at module level instead of package level.
It can also replace the standard import mechanism. Additionally, 
it has the ability to solve the relative import problem that occurs 
when executing unit modules located in each subdirectory without sys.path.

# features
. importing modules using relative paths
. importing modules using absolute paths
. importing member functions from modules
. support lazy-import avoid circular importing
. support to import functions from module, like from x import y ...

# examples
import importpy
aaaa = importpy('aaaa.py') 
aaaa = importpy('./aaaa.py') 
bbbb = importpy('../util/test/bbbb.py') 
bbbb = importpy('../util/test/bbbb.py', '*')
cccc = importpy('c:/project/cccc.py') 
lazy_on = importpy('lazy_on.py', use_lazy = False) # default action
lazyoff = importpy('lazyoff.py', use_lazy = True) 
a_member_of_x, b_member_of_x = importpy('./pathto/x.py', 'a_member_of_x', 'b_member_of_x') 
x, a_member_of_x, b_member_of_x = importpy('./pathto/x.py', '*', 'a_member_of_x', 'b_member_of_x') 
ClassA, ClassB = importpy('./pathto/impl.py', 'ClassA', 'ClassB)
"""
__version__ = '0.1.0'


import os, sys
if sys.version_info < (3,8): raise Exception(f"[ERR] importpy requires Python 3.8 or greater ...")

'''
example)

'''

import types, typing, inspect, importlib.util
def loader(file: str, *args, use_lazy: bool = True) -> typing.Union[types.ModuleType, typing.Any] : return imports(file, args, use_lazy)
sys.modules[__name__] = loader

def imports(file: str, args:tuple = (), use_lazy: bool = True) -> typing.Union[types.ModuleType, typing.Any] : # @14mhz 20250710, lazy-style custrom importer
    def stacks(frame) : # with stacks(inspect.currentframe())
        return [] if not frame else [frame] + stacks(frame.f_back)
    def verify(modl: types.ModuleType, args) :
        return all(hasattr(modl, n) or n == '*' for n in args)
    def attrib(modl: types.ModuleType, args) -> typing.Tuple :
        if not verify(modl, args): raise AttributeError(f"[ERR] cannot found attribute {args} in [{modl.__name__}] ...")
        _a = tuple(getattr(modl, n) if has else modl for n in args if (has := hasattr(modl, n)) or n == '*')
        return _a if 1 < len(_a) else _a[0]

    stck = [s for s in stacks(inspect.currentframe())]
    stid = next((i+2 for i, p in enumerate(stck) if __file__ == p.f_code.co_filename), None) # .py caller, c+0 is me, c+1 is loader, c+2 is target !
    cpth = stck[stid].f_code.co_filename.replace('\\', '/') # caller path
    cpkg = stck[stid].f_globals.get("__package__")          # caller package name
    cpkg = cpkg if cpkg else ''
    if not cpth: raise IndexError(f"[ERR] cannot found call stack [{stck}] ...")
    if False: print(f"[INF] stid[{stid}] cpkg[{cpkg}] cpth[{cpth}]")
    
    path = os.path.abspath(os.path.join(os.path.dirname(cpth), file)).replace('\\', '/')   # .py to absolute path
    _pkg = os.path.normpath(os.path.join(cpkg.replace('.', '/'), file))                    # ex) 'wdep/pack\\../util/web.py' to 'wdep\\util\\web.py'
    pack = _pkg.replace('\\', '/').replace('../', '').replace('/', '.').replace('.py', '') # ex) wdep.pack.web
    if not os.path.exists(path): raise FileNotFoundError(f"[ERR] cannot found .py path [{path}] ...")

    if False: print(f"[INF] caller [{cpth.rpartition('/')[2]}] imports [{file}] → module [{pack}] ...")

    if pack in sys.modules: return sys.modules[pack] if not args else attrib(sys.modules[pack], args)
    spec = importlib.util.spec_from_file_location(pack, path)
    if spec.loader is None: raise ImportError(f"[ERR] cannot found loader: {path}")
    modl = importlib.util.module_from_spec(spec)
    load = spec.loader if not use_lazy else importlib.util.LazyLoader(spec.loader) 
    sys.modules[pack] = modl
    load.exec_module(modl) 
    return modl if not args else attrib(modl, args)

pass
