# importpy
Dynamic, lazy-style module importer for Python. It lets you import individual .py files directly at the module level, while still replicating standard package semantics (including automatic \_\_init\_\_.py execution) and resolving relative-import issues in nested directories—no changes to sys.path required. Use it to override Python’s built-in import mechanism only when you need that extra flexibility.
  
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
2025/07/11 v0.1.0 : initial released  
2025/07/13 v0.1.1 : some minor bug fix, support pytest  

# Installation (pip install)
```python
python -m pip install importpy
or
python -m pip install git+https://github.com/waveware4ai/importpy
```
# Requirements
```python
Python 3.8+
No external dependencies
```
# Features
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
# Testing
```
python -m pytest -v ./importpy/test
importpy/test/test_importpy.py::test_importpy_basic_module PASSED                                                      [  3%]
importpy/test/test_importpy.py::test_importpy_basic_attr_single PASSED                                                 [  7%]
importpy/test/test_importpy.py::test_importpy_basic_attr_multiple PASSED                                               [ 10%]
importpy/test/test_importpy.py::test_importpy_basic_star_attribute PASSED                                              [ 14%]
importpy/test/test_importpy.py::test_importpy_basic_star_includes_expected_attributes PASSED                           [ 17%]
importpy/test/test_importpy.py::test_importpy_basic_attr_missing PASSED                                                [ 21%]
importpy/test/test_importpy.py::test_importpy_basic_args_invalid PASSED                                                [ 25%]
importpy/test/test_importpy.py::test_importpy_basic_absolute_path_loading PASSED                                       [ 28%]
importpy/test/test_importpy.py::test_importpy_basic_invalid_file_path PASSED                                           [ 32%]
importpy/test/test_importpy.py::test_importpy_basic_caching_behavior PASSED                                            [ 35%]
importpy/test/test_importpy.py::test_importpy_basic_lazy_loader_flag PASSED                                            [ 39%]
importpy/test/test_importpy.py::test_importpy_basic_occur_cyclic_importing PASSED                                      [ 42%]
importpy/test/test_importpy.py::test_importpy_basic_avoid_cyclic_importing PASSED                                      [ 46%]
importpy/test/test_importpy.py::test_importpy_protocol_validation_header PASSED                                        [ 50%]
importpy/test/test_importpy.py::test_importpy_protocol_validation_file_path PASSED                                     [ 53%]
importpy/test/test_importpy.py::test_importpy_protocol_validation_http_path PASSED                                     [ 57%]
importpy/test/test_importpy.py::test_importpy_protocol_remote_wheel PASSED                                             [ 60%]
importpy/test/test_importpy.py::test_importpy_protocol_remote_targz PASSED                                             [ 64%]
importpy/test/test_importpy.py::test_importpy_protocol_remote_http PASSED                                              [ 67%]
importpy/test/test_importpy.py::test_importpy_protocol_remote_github PASSED                                            [ 71%]
importpy/test/test_importpy.py::test_importpy_protocol_remote_ftp PASSED                                               [ 75%]
importpy/test/test_importpy.py::test_importpy_protocol_remote_sftp PASSED                                              [ 78%]
importpy/test/test_importpy.py::test_importpy_protocol_remote_custom_loader PASSED                                     [ 82%]
importpy/test/test_importpy.py::test_importpy_protocol_local_wheel PASSED                                              [ 85%]
importpy/test/test_importpy.py::test_importpy_protocol_local_file PASSED                                               [ 89%]
importpy/test/test_importpy.py::test_importpy_protocol_instance_isolation_test1 PASSED                                 [ 92%]
importpy/test/test_importpy.py::test_importpy_protocol_instance_isolation_test2 PASSED                                 [ 96%]
importpy/test/test_importpy.py::test_importpy_protocol_instance_isolation_test3 PASSED                                 [100%]

==================================================== 28 passed in 8.82s =====================================================
```
# Examples
```python
import importpy
# simple relative import
aaaa = importpy('aaaa.py') # same to below
aaaa = importpy('./aaaa.py')

# wildcard import
bbbb = importpy('../util/test/bbbb.py') # same to below
bbbb = importpy('../util/test/bbbb.py', '*') 

# absolute path
cccc = importpy('/home/user/project/cccc.py')
cccc = importpy('C:/program files/python/project/cccc.py') 

# turn on/off lazy-loading
lazy_on = importpy('lazy_on.py', use_lazy = True) # default action
lazyoff = importpy('lazyoff.py', use_lazy = False)

# import specific attributes
a_member_of_x, b_member_of_x = importpy('./pathto/x.py', 'a_member_of_x', 'b_member_of_x') 
module_x, a_member_of_x, b_member_of_x = importpy('./pathto/x.py', '*', 'a_member_of_x', 'b_member_of_x')  # wildcard include module x

# class import
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
from impl import ClassA, ClassB, funcX
ClassA, ClassB, funcX = importpy('impl.py', 'ClassA', 'ClassB', 'funcX')
```
