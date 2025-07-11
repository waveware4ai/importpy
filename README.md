# importpy

This small python-utility is used to import at module level instead of package level. 
It can also replace the standard import mechanism. (I'm not saying to replace everything, but to use it only when necessary :D)  
Additionally, it has the ability to solve the relative import problem that occurs 
when executing unit modules located in each subdirectory without sys.path.
  
```
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

# History
------------
2025/07/11 v0.1.0 : initial released  

# Installation (pip install)
------------
```python
python -m pip install importpy
or
python -m pip install git+https://github.com/waveware4ai/importpy
```

# Features
```
* Basic Features
  + importing modules using relative paths  
  + importing modules using absolute paths  
  + importing member functions from modules  
  + support lazy-import avoid circular importing  
  + support to import functions from module, like from x import y ...
* Import Logic  
  + caller location is traced via inspect  
  + relative path is resolved automatically  
  + module name is derived from the file path (e.g. utils/web.py → utils.web)  
  + result is cached in-memory  
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
