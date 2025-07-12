r"""
# importpy v0.1.1 202507xx
by 14mhz@hanmail.net, zookim@waveware.co.kr

# importpy

This small python-utility is used to import at module level instead of package level. 
It can also replace the standard import mechanism. (I'm not saying to replace everything, but to use it only when necessary :D)  
Additionally, it has the ability to solve the relative import problem that occurs 
when executing unit modules located in each subdirectory without sys.path.

root package
    │
    ├─── __init__.py
    │
    ├─── packageA/
    │       │
    │       ├─── __init__.py
    │       ├─── moduleA1.py
    │       └─── moduleA2.py
    │       
    ├─── packageB/
    │       │
    │       ├───── packageC/
    │       │         │
    │       │         ├─── __init__.py
    │       │         ├─── moduleC1.py
    │       │         └─── moduleC2.py
    │       │
    │       ├─── __init__.py
    │       ├─── moduleB1.py
    │       └─── moduleB2.py

```
Now you can import regardless of path.  
For example, you can import moduleB1 of packageB from moduleA1 of packageA as follows.  
```
moduleA1.py of packageA
moduleB1 = importpy('../packageB/moduleB1.py')
```
likewise, can import moduleA2 of packageA from moduleC2 of packageC as follows.  
Of course, absolute paths are also possible.  
```
moduleC2.py of packageC
moduleA1 = importpy('../../packageA/moduleA2.py')
or
moduleA1 = importpy('c:/program files/python/project/test/package_root/packageA/moduleA2.py')
```
```
moduleC2.py of packageC
member1, member2, classC = importpy('../../packageA/moduleA2.py', 'member1', 'member2', 'classC')
```
I came up with this approach because I usually put unit tests in '\_\_main\_\_' of each module.  
Additionally, modules imported in this way can be executed independently regardless of the package structure. That's it....  
   
# Installation (pip install)
------------
```python
python -m pip install importpy
```

# Features
```
. importing modules using relative paths  
. importing modules using absolute paths  
. importing member functions from modules  
. support lazy-import avoid circular importing  
. support to import functions from module, like from x import y ...  
```

# Examples
```python
import importpy
aaaa = importpy('aaaa.py') 
aaaa = importpy('./aaaa.py') 
bbbb = importpy('../util/test/bbbb.py') 
bbbb = importpy('../util/test/bbbb.py', '*')
cccc = importpy('C:/program files/python/project/cccc.py') 
lazy_on = importpy('lazy_on.py', use_lazy = True) # default action
lazyoff = importpy('lazyoff.py', use_lazy = False) 
a_member_of_x, b_member_of_x = importpy('./pathto/x.py', 'a_member_of_x', 'b_member_of_x') 
x, a_member_of_x, b_member_of_x = importpy('./pathto/x.py', '*', 'a_member_of_x', 'b_member_of_x') 
ClassA, ClassB = importpy('./pathto/impl.py', 'ClassA', 'ClassB')
```
The following perform the same role:  
```python
import aaaa
aaaa = importpy('aaaa.py')
```
```python
from x import a_member_of_x, b_member_of_x
a_member_of_x, b_member_of_x = importpy('x.py', 'a_member_of_x', 'b_member_of_x') 
```
```python
from impl import ClassA, ClassB
ClassA, ClassB = importpy('impl.py', 'ClassA', 'ClassB')
```
"""
import os, sys, pathlib
if sys.version_info < (3,8): raise Exception(f"[ERR] importpy requires Python 3.8 or greater ...")

__version__ = '0.1.1'

import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s') # logging.INFO, logging.DEBUG
LOG = logging.getLogger(__name__)

import types, typing, inspect, importlib.util as imp_util                  
from os.path import abspath as absopath, normpath, join as joinpath, dirname as superdir, exists as hasfile
def loader(file: str, *args, use_lazy: bool = True) -> typing.Union[types.ModuleType, typing.Any] : return imports(file, *args, use_lazy=use_lazy)
sys.modules[__name__] = loader

module_bank = {} 
def imports(file: str, *args, use_lazy: bool = True) -> typing.Union[types.ModuleType, typing.Tuple[typing.Any, ...]] : # @14mhz, lazy-style custrom importer
    def stacks(frame) -> list : # with stacks(inspect.currentframe())
        return [] if not frame else [frame] + stacks(frame.f_back)
    def module(pack: str, path: str, iseager: bool = False) -> types.ModuleType :
        spec = imp_util.spec_from_file_location(pack, path, submodule_search_locations = None if not iseager else [superdir(path)] )
        if spec.loader is None: raise ImportError(f"[ERR] cannot find loader [{path}]")
        modl = imp_util.module_from_spec(spec)
        load = spec.loader if iseager or not use_lazy else imp_util.LazyLoader(spec.loader) 
        try: load.exec_module(modl) 
        except Exception as e: raise ImportError(f"[ERR] execution error loader [{path}] {e}")
        return modl
    def verify(modl: types.ModuleType, args) -> bool :
        if any(not isinstance(n, str) for n in args): raise AttributeError(f"[ERR] args must be str type {args} in [{modl.__name__}] ...")
        return all(hasattr(modl, n) or n == '*' for n in args)
    def attrib(modl: types.ModuleType, args) -> typing.Tuple :
        if not verify(modl, args): raise AttributeError(f"[ERR] cannot find attribute {args} in [{modl.__name__}] ...")
        _a = tuple(getattr(modl, n) if has else modl for n in args if (has := hasattr(modl, n)) or n == '*') # walrus op with above p3.8
        return _a if 1 < len(_a) else _a[0]
    
    file = file if not isinstance(file, pathlib.Path) else file.as_posix() 
    if not file.endswith('.py'): raise ValueError(f"[ERR] import path must end with .py [maybe {file}.py?] ...")
    stck = [s for s in stacks(inspect.currentframe())] # .py caller ie, c+0 is me, c+1 is loader, c+2 is caller !, use inspect.stack()???
    stid = next((i+2 for i, p in enumerate(stck) if __file__ == p.f_code.co_filename), None) 
    cpth = stck[stid].f_code.co_filename.replace('\\', '/') # caller path
    cpkg = stck[stid].f_globals.get("__package__") or ''    # caller package name
    if not cpth: raise RuntimeError(f"[ERR] cannot found call stack [{stck}] ...")
    LOG.debug(f"traced stid[{stid}] → cpkg[{cpkg}] → cpth[{cpth}]")
    
    path = absopath(joinpath(superdir(cpth), file)).replace('\\', '/') # .py to absolute path
    ppth = normpath(joinpath(cpkg.replace('.', '/'), file))            # ex) 'wdep/pack\\../util/web.py' to 'wdep\\util\\web.py'
    pack = ppth.replace('\\', '/').replace('../', '').replace('/', '.').replace('.py', '') # ex) wdep.pack.web
    if not hasfile(path): raise FileNotFoundError(f"[ERR] cannot find .py path [{path}] ...")
    LOG.debug(f"caller [{cpth.rpartition('/')[2]}] imports [{file}] → module [{pack}]{args}")

    bank_key = (path, args)
    initpack = pack.rpartition('.')[0] # a.b.c → a.b, load package '__init__.py'
    initpath = '' if initpack in sys.modules else joinpath(os.path.dirname(path), '__init__.py').replace('\\', '/')
    if initpack and hasfile(initpath): LOG.debug(f"load package init → [{initpath}]"); sys.modules[initpack] = module(initpack, initpath, True) 

    if bank_key in module_bank: return module_bank[bank_key]
    if not pack in sys.modules: sys.modules[pack] = module(pack, path)
    module_bank[bank_key] = sys.modules[pack] if not args else attrib(sys.modules[pack], args)
    return module_bank[bank_key]
pass
