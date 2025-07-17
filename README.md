# importpy
Dynamic, lazy-style support importer for Python. It lets you import individual .py files directly at the module level, while still replicating standard package semantics (including automatic \_\_init\_\_.py execution) and resolving relative-import issues in nested directories—no changes to sys.path required. Use it to override Python’s built-in import mechanism only when you need that extra flexibility.

## Use Relative Path
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

## Use URL Path
import Remote Package
```python
remote_package = importpy('file://example.com/remote_package')
remote_package = importpy('http://example.com/remote_package')
remote_package = importpy('https://example.com/remote_package')
remote_package = importpy('ftp://user:pass@example.com/remote_package')
import remote_package # You can use it as a general import.
remote_package.__version__
```
import Remote Module
```python
remote_module = importpy('file://example.com/remote_module.py')
remote_module = importpy('http://example.com/remote_module.py')
remote_module = importpy('https://example.com/remote_module.py')
remote_module = importpy('ftp://user:pass@example.com/remote_module.py')
```
import Remote wheel/sdist
```python
pip_package = importpy('https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl')
pip_package = importpy('https://files.pythonhosted.org/packages/59/de/241caa0ca606f2ec5fe0c1f4261b0465df78d786a38da693864a116c37f4/pip-25.1.1.tar.gz')
import pip # You can use it as a general import.
pip.__version__
```
import github direct
```python
pip_package = importpy('https://github.com/pypa/pip/tree/main/src/pip')
import pip # You can use it as a general import.
pip.__version__
```
import module/function with arguments
```python
a, b, c = importpy('file://example.com/remote_package', 'a', 'b', 'c') # member module a,b,c
a, b, c = importpy('file://example.com/remote_module.py', 'a', 'b', 'c') # member function a,b,c
```
import using custom loader
```python
remote_package = importpy('userdefined://abc/efg/package', CustomMetaFinder())
CustomMetaFinder(AbstractMetaFinder) # See protocol.py for the format of AbstractMetaFinder.
  .
  .
  .

```

# History
2025/07/11 v0.1.0 : initial released  
2025/07/13 v0.1.1 : some minor bug fix, support pytest  
2025/07/17 v0.1.2 : some minor bug fix, support remote url 

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
    + importing package using url paths  
    + importing modules using url paths  
    + importing member functions from modules  
    + support lazy-import avoid circular importing  
    + support to import functions from module, like from x import y ...
* Import Logic  
    + caller location is traced via inspect  
    + relative path is resolved automatically  
    + module name is derived from the file path (e.g. utils/web.py → utils.web)  
    + result is cached in-memory  
# Examples
## Relative Path
```python
from importpy import loader as importpy
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
module_x, a_member_of_x, b_member_of_x = importpy('./pathto/x.py', '*', 'a_member_of_x', 'b_member_of_x')  # wildcard include module x self

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
## URL Path
To do this example, you no longer need pip installed locally. Move it somewhere else or delete it.
```python
def import_pip_test(url: str, custom_finder=None, uselazy:bool = True, isolate=True):
    from importpy import loader as importpy
    pip = importpy(url, custom_finder=custom_finder, uselazy=uselazy, isolate=isolate)
    import pip as PIP # must be the same instance.
    assert id(pip) == id(PIP) 

    print(f"---------- pip-{pip.__version__} from [{pip.__file__}].main(['freeze'])")
    pip.main(["freeze"])
    print(f"---------- pip-{pip.__version__} from [{pip.__file__}].main(['list'])")
    pip.main(["list"])
```
pypi sdist/wheel remote access test
```python
    import_pip_test("https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl")
    import_pip_test("https://files.pythonhosted.org/packages/59/de/241caa0ca606f2ec5fe0c1f4261b0465df78d786a38da693864a116c37f4/pip-25.1.1.tar.gz")
```
pypi sdist/wheel local access test using file://
```python
    import_pip_test("file://[TEST_DIR]/pip-25.1.1-py3-none-any.whl")
    import_pip_test("file://[TEST_DIR]/pip-25.1.1.tar.gz")
    import_pip_test("file://[TEST_DIR]/pip-25.1.1-py3-none-any/pip") # extract to dir
```
pypi sdist/wheel remote access using ftp://
```python
    import_pip_test("ftp://user:pass@localhost/whl/pip-25.1.1-py3-none-any.whl")
    import_pip_test("ftp://user:pass@localhost/whl/pip-25.1.1.tar.gz")
    import_pip_test("ftp://user:pass@localhost/whl/pip") # extract to dir
```
pypi sdist/wheel remote access using http/https://
```python
    import_pip_test("http://localhost:1080/whl/pip-25.1.1-py3-none-any.whl")
    import_pip_test("http://localhost:1080/whl/pip-25.1.1.tar.gz")
    import_pip_test("http://localhost:1080/whl/pip") # extract to dir
    import_pip_test("https://localhost:10443/whl/pip-25.1.1-py3-none-any.whl")
    import_pip_test("https://localhost:10443/whl/pip-25.1.1.tar.gz")
    import_pip_test("https://localhost:10443/whl/pip") # extract to dir
```
github direct access using https://
```python
    import_pip_test("http://github.com/pypa/pip/tree/main/src/pip")
```
# Testing
```
python -m pytest -v ./importpy/tests
collected 30 items
importpy/tests/test_importpy.py::test_importpy_basic_module PASSED                                       [  3%]
importpy/tests/test_importpy.py::test_importpy_basic_attr_single PASSED                                  [  6%]
importpy/tests/test_importpy.py::test_importpy_basic_attr_multiple PASSED                                [ 10%]
importpy/tests/test_importpy.py::test_importpy_basic_star_attribute PASSED                               [ 13%]
importpy/tests/test_importpy.py::test_importpy_basic_star_includes_expected_attributes PASSED            [ 16%]
importpy/tests/test_importpy.py::test_importpy_basic_attr_missing PASSED                                 [ 20%]
importpy/tests/test_importpy.py::test_importpy_basic_args_invalid PASSED                                 [ 23%]
importpy/tests/test_importpy.py::test_importpy_basic_absolute_path_loading PASSED                        [ 26%]
importpy/tests/test_importpy.py::test_importpy_basic_invalid_file_path PASSED                            [ 30%]
importpy/tests/test_importpy.py::test_importpy_basic_caching_behavior PASSED                             [ 33%]
importpy/tests/test_importpy.py::test_importpy_basic_lazy_loader_flag PASSED                             [ 36%]
importpy/tests/test_importpy.py::test_importpy_basic_occur_cyclic_importing PASSED                       [ 40%]
importpy/tests/test_importpy.py::test_importpy_basic_avoid_cyclic_importing PASSED                       [ 43%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_file_import_as_module PASSED              [ 46%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_file_import_as_package PASSED             [ 50%]
importpy/tests/test_importpy.py::test_importpy_protocol_validation_header PASSED                         [ 53%]
importpy/tests/test_importpy.py::test_importpy_protocol_validation_file_path PASSED                      [ 56%]
importpy/tests/test_importpy.py::test_importpy_protocol_validation_http_path PASSED                      [ 60%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_wheel PASSED                              [ 63%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_targz PASSED                              [ 66%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_http PASSED                               [ 70%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_github PASSED                             [ 73%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_ftp PASSED                                [ 76%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_sftp PASSED                               [ 80%]
importpy/tests/test_importpy.py::test_importpy_protocol_remote_custom_loader PASSED                      [ 83%]
importpy/tests/test_importpy.py::test_importpy_protocol_local_wheel PASSED                               [ 86%]
importpy/tests/test_importpy.py::test_importpy_protocol_local_file PASSED                                [ 90%]
importpy/tests/test_importpy.py::test_importpy_protocol_instance_isolation_test1 PASSED                  [ 93%]
importpy/tests/test_importpy.py::test_importpy_protocol_instance_isolation_test2 PASSED                  [ 96%]
importpy/tests/test_importpy.py::test_importpy_protocol_instance_isolation_test3 PASSED                  [100%]

============================================= 30 passed in 9.15s ==============================================
```
