# run command >> python -m pytest -v ./importpy/test

import io, os, sys, types
import zipfile
from urllib.error import URLError

sys.path.append(os.path.abspath(__file__+ '/../../..'))
import pytest, tempfile
from importpy import loader as importpy

@pytest.fixture
def moduleA(tmp_path):
    code = '''
from importpy import loader as importpy
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
from importpy import loader as importpy
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


########################################

# test loading entire module
def test_importpy_basic_module(moduleA, moduleB):
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
def test_importpy_basic_attr_single(moduleA, moduleB):
    moduleA_hello = importpy(moduleA, 'hello')
    assert moduleA_hello() == 'world'

    moduleB_hello = importpy(moduleB, 'hello')
    assert moduleB_hello() == 'world'

# test importing multiple attributes
def test_importpy_basic_attr_multiple(moduleA, moduleB):
    moduleA_hello, moduleA_forwarding, ClassA = importpy(moduleA, 'hello', 'hello_forwarding', 'ClassA')
    assert moduleA_hello() == 'world'
    assert moduleA_forwarding() == 'world'
    assert ClassA().hello() == 'world'

    moduleB_hello, moduleB_forwarding, ClassB = importpy(moduleB, 'hello', 'hello_forwarding', 'ClassB')
    assert moduleB_hello() == 'world'
    assert moduleB_forwarding() == 'world'
    assert ClassB().hello() == 'world'

# test importing star attributes
def test_importpy_basic_star_attribute(moduleA, moduleB):
    a = importpy(moduleA, "*")
    assert isinstance(a, types.ModuleType)
    b = importpy(moduleB, "*")
    assert isinstance(b, types.ModuleType)

# test importing star attributes
def test_importpy_basic_star_includes_expected_attributes(moduleA, moduleB):
    a = importpy(moduleA, '*')
    assert hasattr(a, 'hello')
    assert hasattr(a, 'ClassA')
    b = importpy(moduleB, '*')
    assert hasattr(b, 'hello')
    assert hasattr(b, 'ClassB')

# test for missing attribute error
def test_importpy_basic_attr_missing(moduleA, moduleB):
    with pytest.raises(AttributeError):
        importpy(moduleA, 'not_found')
    with pytest.raises(AttributeError):
        importpy(moduleB, 'not_found')

# test for invalid argument types
def test_importpy_basic_args_invalid(moduleA, moduleB):
    with pytest.raises(AttributeError):
        importpy(moduleA, 123)
    with pytest.raises(AttributeError):
        importpy(moduleB, sys)

# test importing absolute path loading
def test_importpy_basic_absolute_path_loading(tmp_path):
    subdir = tmp_path / 'sub'
    subdir.mkdir()
    module = subdir / 'mod.py'
    module.write_text("def ping(): return 'pong'")
    result = importpy(module, 'ping')
    assert result() == 'pong'

# test for invalid file path
def test_importpy_basic_invalid_file_path():
    with pytest.raises(FileNotFoundError):
        importpy("non_existent_module.py")

# test module caching functionality
def test_importpy_basic_caching_behavior(moduleA, moduleB):
    a1 = importpy(moduleA)
    a2 = importpy(moduleA)
    b1 = importpy(moduleA, 'hello')
    b2 = importpy(moduleA, 'hello_forwarding')    
    assert a1 == a2 
    assert b1 != b2 

# test importing lazy loader functionality
def test_importpy_basic_lazy_loader_flag(moduleA, moduleB):
    lazy_mode = importpy(moduleA, uselazy=True)
    eagermode = importpy(moduleA, uselazy=False)
    assert hasattr(lazy_mode, 'hello') and hasattr(eagermode, 'hello') 

@pytest.fixture
def cyclicA(tmp_path):
    code = '''
from importpy import loader as importpy
cyclicB = importpy('cyclicB.py', uselazy=False)

def hello():
    return 'world'

'''
    path = tmp_path / "cyclicA.py"
    path.write_text(code)
    return str(path)

@pytest.fixture
def cyclicB(tmp_path):
    code = '''
from importpy import loader as importpy
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
from importpy import loader as importpy
cyclicD = importpy('cyclicD.py', uselazy=True)

def hello():
    return 'world'

'''
    path = tmp_path / "cyclicC.py"
    path.write_text(code)
    return str(path)

@pytest.fixture
def cyclicD(tmp_path):
    code = '''
from importpy import loader as importpy
cyclicC = importpy('cyclicC.py')
cyclicC.hello()

def hello():
    return 'world'

'''
    path = tmp_path / "cyclicD.py"
    path.write_text(code)
    return str(path)

# test occur circular importing
def test_importpy_basic_occur_cyclic_importing(cyclicA, cyclicB):
    with pytest.raises(ImportError):
        importpy(cyclicA, uselazy=False)

# test avoid circular importing
def test_importpy_basic_avoid_cyclic_importing(cyclicC, cyclicD):
    c = importpy(cyclicC, uselazy=False)
    assert hasattr(c, 'hello')

@pytest.fixture
def protocol_remote_wheel(tmp_path):
    code = '''
from importpy import loader as importpy
url = 'https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl'
pip = importpy(url)
pip.main(["freeze"])
def version():
    return pip.__version__

'''
    path = tmp_path / "protocol_remote_wheel.py"
    path.write_text(code)
    return str(path)

@pytest.fixture
def protocol_remote_targz(tmp_path):
    code = '''
from importpy import loader as importpy
url = 'https://files.pythonhosted.org/packages/59/de/241caa0ca606f2ec5fe0c1f4261b0465df78d786a38da693864a116c37f4/pip-25.1.1.tar.gz'
pip = importpy(url)
pip.main(["freeze"])
def version():
    return pip.__version__

'''
    path = tmp_path / "protocol_remote_targz.py"
    path.write_text(code)
    return str(path)

def test_importpy_protocol_validation_header():
    with pytest.raises(ValueError):
        imp = importpy('data://unknown/123', uselazy=False)

def test_importpy_protocol_validation_file_path():
    with pytest.raises(FileNotFoundError):
        imp = importpy('file://unknown/123', uselazy=False)

def test_importpy_protocol_validation_http_path():
    with pytest.raises(URLError):
        imp = importpy('http://unknown/123.whl', uselazy=False)

def test_importpy_protocol_remote_wheel(protocol_remote_wheel):
    pip = importpy(protocol_remote_wheel, uselazy=False).pip
    assert hasattr(pip, '__version__')

def test_importpy_protocol_remote_targz(protocol_remote_targz):
    pip = importpy(protocol_remote_targz, uselazy=False).pip
    assert hasattr(pip, '__version__')
    
def test_importpy_protocol_remote_http(tmp_path):
    pass # pytest environment needs to be created.

def test_importpy_protocol_remote_github(tmp_path):
    pass # pytest environment needs to be created.

def test_importpy_protocol_remote_ftp(tmp_path):
    pass # pytest environment needs to be created.

def test_importpy_protocol_remote_sftp(tmp_path):
    pass # pytest environment needs to be created.

def test_importpy_protocol_remote_custom_loader():
    url = 'https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl'
    pip = importpy(url, custom_finder=CustomZipMetaFinder(), uselazy=False)
    assert hasattr(pip, '__version__')

def test_importpy_protocol_local_wheel(tmp_path):
    url = 'https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl'
    import importpy.protocol_impl as impl
    whl = tmp_path.as_posix() + '/' + url.rpartition('/')[2]
    impl.fetch2file(url, whl)
    imp = importpy('file://' + whl, uselazy=False)
    assert hasattr(imp, '__version__')

def test_importpy_protocol_local_file(tmp_path):
    url = 'https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl'
    import importpy.protocol_impl as impl
    whl = tmp_path.as_posix() + '/' + url.rpartition('/')[2] # ex, c:/[tmpdir]/[pytestdir]/pip-25.1.1-py3-none-any.whl
    impl.fetch2file(url, whl)
    dir = tmp_path.as_posix() + '/' + 'whl'                  # ex, c:/[tmpdir]/[pytestdir]/whl
    os.makedirs(dir)
    with zipfile.ZipFile(whl, 'r') as zip_ref:
        zip_ref.extractall(dir)
    imp = importpy('file://' + dir + '/pip', uselazy=False)  # ex, c:/[tmpdir]/[pytestdir]/whl/pip
    assert hasattr(imp, '__version__')

def test_importpy_protocol_instance_isolation_test1(protocol_remote_wheel):
    importpy_instance = importpy(protocol_remote_wheel, isolate=True).pip
    import pip as register_instance
    assert id(register_instance) == id(sys.modules['pip'])
    assert id(importpy_instance) == id(sys.modules['pip'])

def test_importpy_protocol_instance_isolation_test2():
    import pip as register_instance
    url = 'https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl'
    importpy_instance = importpy(url, isolate=True)
    assert id(register_instance) != id(sys.modules['pip'])
    assert id(importpy_instance) == id(sys.modules['pip'])

def test_importpy_protocol_instance_isolation_test3():
    url = 'https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl'
    importpy_instance = importpy(url, isolate=True)
    import pip as register_instance
    assert id(register_instance) == id(sys.modules['pip'])
    assert id(importpy_instance) == id(sys.modules['pip'])

######################################## test method & class

import zipfile, urllib.request
from urllib.error import URLError
from importpy.protocol import AbstractMetaFinder, RemoteMetaImporter

def fetch2mem(url, buffer=8192):
    if url.startswith('file://'):
        path = url.rpartition('://')[2]
        return path
    try:
        req = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}))
        tot = int(req.headers.get("Content-Length", 0))
        print(f"[INF] Downloading: {url} ({tot} bytes)")
        mem = io.BytesIO()
        got = 0
        while True:
            chunk = req.read(buffer)
            if not chunk:
                break
            mem.write(chunk)
            got += len(chunk)
            percent = (got / tot) * 100 if tot else 0
            print(f"[INF]{got}/{tot} bytes ({percent:.2f}%)\r")
        print("\n[INF] streaming complete!")
        mem.seek(0)
        return mem
    except Exception as e:
        print(f"[ERR] streaming failed: {e}")
        return None
    
class CustomZipMetaFinder(AbstractMetaFinder):
    def __init__(self, uselazy:bool = True):
        super().__init__(uselazy)
        self.type = 'zip://'
        self.data = None # archive

    def hasfile(self, url: str) -> bool :
        try:
            if url.startswith('file://'):
                return os.path.exists(url.rpartition('://')[2])
                pass
            elif url.startswith(('http://', 'https://')):
                with urllib.request.urlopen(url, timeout=1) as r: return r.status == 200
        except :
            raise URLError(f"[ERR] invalid url [{url}] ...")

    def imports(self, url, clean = None):
        if not self.hasfile(url): raise FileNotFoundError(f"[ERR] cannot find path [{url}] ...")
        if not url.endswith('.whl') and not url.endswith('.zip'): return None
        self.data = zipfile.ZipFile(fetch2mem(url))
        self.tree = {p:'' for p in self.data.namelist() if p.endswith(".py")}  # package tree, must always start with the package name
        self.pnme = sorted(set(path.split("/")[0] for path in self.tree))[0]   # package name
        if clean : clean(self.pnme)
        return self.pnme

    def sourcecode(self, file_path) :
        return self.data.read(file_path).decode()

    def custom_loader(self, file_path, is_pkg):
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)
