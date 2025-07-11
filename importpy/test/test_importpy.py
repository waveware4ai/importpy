# run command >> python -m pytest -v ./importpy/test

import os, sys, types
sys.path.append(os.path.abspath(__file__+ '/../../..'))
import pytest, tempfile
import importpy

@pytest.fixture
def moduleA(tmp_path):
    code = '''
import importpy
moduleB = importpy('moduleB.py')

def hello():
    return 'world'

def hello_forwarding():
    return moduleB.hello()    

class ClassA:
    def hello(self):
        return 'world'
'''
    path = tmp_path / "moduleA.py"
    path.write_text(code)
    return str(path)

@pytest.fixture
def moduleB(tmp_path):
    code = '''
import importpy
moduleA = importpy('moduleA.py')
    
def hello():
    return 'world'

def hello_forwarding():
    return moduleA.hello()

class ClassB:
    def hello(self):
        return 'world'
'''
    path = tmp_path / "moduleB.py"
    path.write_text(code)
    return str(path)

@pytest.fixture
def cyclicA(tmp_path):
    code = '''
import importpy
cyclicB = importpy('cyclicB.py', use_lazy=False)

def hello():
    return 'world'

'''
    path = tmp_path / "cyclicA.py"
    path.write_text(code)
    return str(path)

@pytest.fixture
def cyclicB(tmp_path):
    code = '''
import importpy
cyclicA = importpy('cyclicA.py')
cyclicA.hello()

def hello():
    return 'world'

'''
    path = tmp_path / "cyclicB.py"
    path.write_text(code)
    return str(path)

@pytest.fixture
def cyclicC(tmp_path):
    code = '''
import importpy
cyclicD = importpy('cyclicD.py', use_lazy=True)

def hello():
    return 'world'

'''
    path = tmp_path / "cyclicC.py"
    path.write_text(code)
    return str(path)

@pytest.fixture
def cyclicD(tmp_path):
    code = '''
import importpy
cyclicC = importpy('cyclicC.py')
cyclicC.hello()

def hello():
    return 'world'

'''
    path = tmp_path / "cyclicD.py"
    path.write_text(code)
    return str(path)

########################################

# test loading entire module
def test_import_module(moduleA, moduleB):
    a = importpy(moduleA)
    b = importpy(moduleB)

    assert hasattr(a, 'hello')
    assert callable(a.hello)
    assert a.hello() == 'world'
    assert a.hello_forwarding() == 'world'

    assert hasattr(b, 'hello')
    assert callable(b.hello)
    assert b.hello() == 'world'
    assert b.hello_forwarding() == 'world'

# test importing a single attribute
def test_import_attr_single(moduleA, moduleB):
    moduleA_hello = importpy(moduleA, 'hello')
    assert moduleA_hello() == 'world'

    moduleB_hello = importpy(moduleB, 'hello')
    assert moduleB_hello() == 'world'

# test importing multiple attributes
def test_import_attr_multiple(moduleA, moduleB):
    moduleA_hello, moduleA_forwarding, ClassA = importpy(moduleA, 'hello', 'hello_forwarding', 'ClassA')
    assert moduleA_hello() == 'world'
    assert moduleA_forwarding() == 'world'
    assert ClassA().hello() == 'world'

    moduleB_hello, moduleB_forwarding, ClassB = importpy(moduleB, 'hello', 'hello_forwarding', 'ClassB')
    assert moduleB_hello() == 'world'
    assert moduleB_forwarding() == 'world'
    assert ClassB().hello() == 'world'

# test importing star attributes
def test_import_star_attribute(moduleA, moduleB):
    a = importpy(moduleA, "*")
    assert isinstance(a, types.ModuleType)
    b = importpy(moduleB, "*")
    assert isinstance(b, types.ModuleType)

# test importing star attributes
def test_import_star_includes_expected_attributes(moduleA, moduleB):
    a = importpy(moduleA, '*')
    assert hasattr(a, 'hello')
    assert hasattr(a, 'ClassA')
    b = importpy(moduleB, '*')
    assert hasattr(b, 'hello')
    assert hasattr(b, 'ClassB')

# test for missing attribute error
def test_import_attr_missing(moduleA, moduleB):
    with pytest.raises(AttributeError):
        importpy(moduleA, 'not_found')
    with pytest.raises(AttributeError):
        importpy(moduleB, 'not_found')

# test for invalid argument types
def test_import_args_invalid(moduleA, moduleB):
    with pytest.raises(ImportError):
        importpy(moduleA, 123)
    with pytest.raises(ImportError):
        importpy(moduleB, sys)

# test importing absolute path loading
def test_import_absolute_path_loading(tmp_path):
    subdir = tmp_path / 'sub'
    subdir.mkdir()
    module = subdir / 'mod.py'
    module.write_text("def ping(): return 'pong'")
    result = importpy(module, 'ping')
    assert result() == 'pong'

# test for invalid file path
def test_import_invalid_file_path():
    with pytest.raises(FileNotFoundError):
        importpy("non_existent_module.py")

# test module caching functionality
def test_import_caching_behavior(moduleA, moduleB):
    a1 = importpy(moduleA)
    a2 = importpy(moduleA)
    b1 = importpy(moduleA, 'hello')
    b2 = importpy(moduleA, 'hello_forwarding')    
    assert a1 == a2 
    assert b1 != b2 

# test importing lazy loader functionality
def test_import_lazy_loader_flag(moduleA, moduleB):
    lazy_mode = importpy(moduleA, use_lazy=True)
    eagermode = importpy(moduleA, use_lazy=False)
    assert hasattr(lazy_mode, 'hello') and hasattr(eagermode, 'hello') 

# test occur circular importing
def test_import_occur_cyclic_importing(cyclicA, cyclicB):
    with pytest.raises(ImportError):
        importpy(cyclicA, use_lazy=False)

# test avoid circular importing
def test_import_avoid_cyclic_importing(cyclicC, cyclicD):
    c = importpy(cyclicC, use_lazy=False)
    assert hasattr(c, 'hello')
