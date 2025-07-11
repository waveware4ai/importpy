# importpy

This small package is used to import at module level instead of package level.
It can also replace the standard import mechanism. Additionally, it has the ability to solve the relative import problem that occurs 
when executing unit modules located in each subdirectory without sys.path.

# History
------------
2025/07/11 v0.1.0 : initial released  

# Installation (pip install)
------------
```python
python -m pip install importpy
```

# Features
. importing modules using relative paths  
. importing modules using absolute paths  
. importing member functions from modules  
. support lazy-import avoid circular importing  
. support to import functions from module, like from x import y ...  

# Examples
```python
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
```

