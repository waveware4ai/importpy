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

# test loading entire module
def test_import_module(moduleA, moduleB):
    moduleA = importpy(moduleA)
    moduleB = importpy(moduleB)

    assert hasattr(moduleA, 'hello')
    assert callable(moduleA.hello)
    assert moduleA.hello() == 'world'
    assert moduleA.hello_forwarding() == 'world'

    assert hasattr(moduleB, 'hello')
    assert callable(moduleB.hello)
    assert moduleB.hello() == 'world'
    assert moduleB.hello_forwarding() == 'world'

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
    moduleA = importpy(moduleA, "*")
    assert isinstance(moduleA, types.ModuleType)
    moduleB = importpy(moduleB, "*")
    assert isinstance(moduleB, types.ModuleType)

# test importing star attributes
def test_import_star_includes_expected_attributes(moduleA, moduleB):
    moduleA = importpy(moduleA, '*')
    assert hasattr(moduleA, 'hello')
    assert hasattr(moduleA, 'ClassA')
    moduleB = importpy(moduleB, '*')
    assert hasattr(moduleB, 'hello')
    assert hasattr(moduleB, 'ClassB')

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
def test_invalid_file_path():
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

def test_import_lazy_loader_flag(moduleA, moduleB):
    lazy_mode = importpy(moduleA, use_lazy=True)
    eagermode = importpy(moduleA, use_lazy=False)
    assert hasattr(lazy_mode, 'hello') and hasattr(eagermode, 'hello') 
