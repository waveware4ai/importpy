import os, io, sys, abc
import importlib.abc, importlib.util

import logging
LOG = logging.getLogger(__name__)

try: from . import __init__ as init # register as sys.modules['importpy'], run with package 
except: import __init__ as init     # register as sys.modules['__init__'], run with direct
init = init.__self__ if type(init).__name__ == 'method-wrapper' else init # else init is 'module'
impl = init.loader('./protocol_impl.py')

#####################################

class CustomResource:
    def __init__(self, name, bytes_data):
        self.name = name
        self.bytes = bytes_data
    def read_text(self, encoding='utf-8'):
        return self.bytes.decode(encoding)

class CustomResourceFinder:
    def __init__(self, module):
        self.module = module
        self.resources = self._build_resources()
    def _build_resources(self):
        loader = getattr(self.module, "__loader__", None)
        archive = getattr(loader, "archive", None)
        resources = []
        if archive:
            for name in archive.namelist():
                if name.endswith(('.exe', '.txt', '.cfg', '.json')) or ".data/" in name:
                    try:
                        resources.append(CustomResource(name, archive.read(name)))
                    except: pass
        return resources
    def iterator(self, prefix=""): return iter(self.resources)

#####################################

class AbstractMetaFinder(importlib.abc.MetaPathFinder):
    def __init__(self, uselazy: bool = True):
        self.type = None         # type ie, zip:// tgz:// url://
        self.tree = {}           # archive tree
        self.pnme = ''           # package name
        self.lazy = uselazy
        self.lodr = DefaultLoader # custom loader

    def find_spec(self, name, path, target=None):
        if not self.pnme: return None
        init_path = f"{name}.__init__" 
        modl_path = f"{name}"         
        for p in [init_path, modl_path]:
            if p in self.tree:
                ispk = '__init__' in p
                load = self.custom_loader(p, ispk) # to DefaultLoader
                load = importlib.util.LazyLoader(load) if self.lazy and not ispk else load # must be check
                spec = importlib.util.spec_from_loader(name, load, is_package=ispk)
                if ispk: spec.submodule_search_locations = [] 
                return spec
        return None

    def custom_loader(self, file_path, is_pkg):
        raise NotImplementedError

#####################################

ROT_NUM = 0
# https://www.unicode.org/emoji/charts/emoji-ordering.html
ROTTXT1 = ['⬆','↗','➡','↘','⬇','↙','⬅','↖']
ROTTXT2 = ['🌑','🌘','🌗','🌖','🌕','🌔','🌒','🌒']
ROTTXT3 = ['🕛','🕐','🕑','🕒','🕓','🕔','🕕','🕖','🕗','🕘','🕙','🕚']
def ROTATION() -> str:
    global ROT_NUM
    ROT_NUM+=1
    ROTTEXT = ROTTXT2
    return ROTTEXT[ROT_NUM%len(ROTTEXT)]

L_RESET = '\033[2K\r'
def PRINT(txt: str) :
    sys.stdout.write(L_RESET + txt + '\r')
    sys.stdout.flush()

class DefaultLoader(importlib.abc.Loader):
    def __init__(self, type, code, pnme, path, ispk): # <- self.lodr <- custom_loader 
        self.type = type # type ie, zip:// tgz:// url://
        self.code = code # func of source code
        self.pnme = pnme # pack name 
        self.path = path # file path
        self.ispk = ispk # ispackage
    def create_module(self, spec): return None # using default spec.loader.create_module(spec)
    def exec_module(self, modl):
        modl.__file__ = self.type + self.path
        modl.__path__ = None if not self.ispk else [self.type + self.path.rsplit("/" , 1)[0]]
        modl.__loader__ = self
        code = self.code(self.path) 
        LOG.debug(f"🚀 exec [{modl.__file__}] ...")
        PRINT(f" {ROTATION()} exec [{modl.__file__}] ...")
        exec(compile(code, self.path, "exec"), modl.__dict__)

#####################################

class Singleton(abc.ABCMeta):
    _instances = {}
    def __new__(cls, name, bases, namespace) :
        namespace.update(destroy=Singleton.destroy)
        return super().__new__(cls, name, bases, namespace)

    def __call__(cls, *args, **kwargs) :
        name = cls.__name__
        if name not in cls._instances:
            call = super(Singleton, cls).__call__(*args, **kwargs)
            LOG.debug(f"[INF] create {name} id[{id(call)}] ...")
            cls._instances[name] = call 
        return cls._instances[name]
    
    @staticmethod
    def destroy(self) :
        cls = self.__class__
        if cls.__name__ in cls._instances:
            name = cls.__name__
            call = cls._instances[name]
            LOG.debug(f"[INF] remove {name} id[{id(call)}] ...")
            del cls._instances[name]

class RemoteMetaImporter(importlib.abc.MetaPathFinder, metaclass=Singleton):
    def __init__(self):
        self.bank = {}

    @classmethod
    def getInstance(cls) :
        return RemoteMetaImporter()

    def clean(self, prefix): # purge from already registered
        for k in list(self.bank): self.bank.pop(k) if k.startswith(prefix) else None
        for k in list(sys.modules): sys.modules.pop(k) if k.startswith(prefix) else None

    def imports(self, url, custom_finder: AbstractMetaFinder=None, uselazy:bool = True, isolate=True):
        if self not in sys.meta_path: sys.meta_path.insert(0, self) # only one instance in meta_path
        find = self.select(url, uselazy=uselazy) if not custom_finder else custom_finder
        pnme = find.imports(url, self.clean if isolate else None)
        self.bank[pnme] = find
        modl = importlib.import_module(pnme) # --> to find_spec directly
        PRINT(f'')
        self.patch_package(find)
        return modl

    def find_spec(self, name, path, target=None):
        spec = next((f.find_spec(name, path, target=target) for f in self.bank.values() if name in f.tree), None)
        LOG.debug(f"{L_RESET}[CHK] find_spec search outside : {name}")
        return spec

    def patch_package(self, find): # various package pactch for compatibility
        try:
            from pip._vendor.distlib import resources
            resources._finder_registry[find.lodr] = lambda mod: CustomResourceFinder(mod)
            PRINT(f'')
        except: pass
        pass

    def select(self, url, uselazy=True):
        url = url.lower()
        if False: pass
        elif url.startswith(('http://', 'https://')):
            type = url.partition('://')[0]
            if False : pass
            elif url.endswith((".zip", ".whl")):    return impl.ZipMetaFinder(type=f'{type}-zip://', uselazy=uselazy, as_finder_role=False)
            elif url.endswith((".tar.gz", ".tgz")): return impl.TgzMetaFinder(type=f'{type}-tgz://', uselazy=uselazy, as_finder_role=False)
            elif "github.com" in url:               return impl.GitMetaFinder(type=f'{type}-git://', uselazy=uselazy, as_finder_role=False)
            else:                                   return impl.WebMetaFinder(type=f'{type}://'    , uselazy=uselazy, as_finder_role=False)
        elif url.startswith('file://'):             
            if False : pass
            elif url.endswith((".zip", ".whl")):    return impl.ZipMetaFinder(type='file-zip://', uselazy=uselazy, as_finder_role=False)
            elif url.endswith((".tar.gz", ".tgz")): return impl.TgzMetaFinder(type='file-tgz://', uselazy=uselazy, as_finder_role=False)
            else:                                   return impl.FleMetaFinder(uselazy=uselazy, as_finder_role=False)
        elif url.startswith('ftp://'):
            if False : pass
            elif url.endswith((".zip", ".whl")):    return impl.ZipMetaFinder(type='ftp-zip://', uselazy=uselazy, as_finder_role=False)
            elif url.endswith((".tar.gz", ".tgz")): return impl.TgzMetaFinder(type='ftp-tgz://', uselazy=uselazy, as_finder_role=False)
            else:                                   return impl.FtpMetaFinder(uselazy=uselazy, as_finder_role=False)    
        else:
            raise ValueError(f"[ERR] unknown protocol [{url}]")

##################################### test code

def import_pip_test(url: str, uselazy:bool = True, isolate=True):
    try:
        import pip #system installed # pip-25.1.1 from [W:\WinShell\bin\python\Python.v3.11.9.x64\runtime\Lib\pip\__init__.py] from installed
        print(f"---------------------------------------- pip-{pip.__version__} from [{pip.__file__}] from installed")
    except: pass

    imp = RemoteMetaImporter.getInstance()
    pip = imp.imports(url, uselazy=uselazy, isolate=isolate)
    import pip as PIP
    assert id(pip) == id(PIP) 

    print(f"---------------------------------------- pip-{pip.__version__} from [{pip.__file__}].main(['freeze'])")
    pip.main(["freeze"])
    print(f"---------------------------------------- pip-{pip.__version__} from [{pip.__file__}].main(['list'])")
    pip.main(["list"])

if __name__ == "__main__":
    import_pip_test("https://files.pythonhosted.org/packages/29/a2/d40fb2460e883eca5199c62cfc2463fd261f760556ae6290f88488c362c0/pip-25.1.1-py3-none-any.whl", isolate=True)
    import_pip_test("https://files.pythonhosted.org/packages/59/de/241caa0ca606f2ec5fe0c1f4261b0465df78d786a38da693864a116c37f4/pip-25.1.1.tar.gz", isolate=True)
    
    # manually test - copy files
    import_pip_test("file://W:/!test/pip-25.1.1-py3-none-any.whl", isolate=True)
    import_pip_test("file://W:/!test/pip-25.1.1.tar.gz", isolate=True)
    import_pip_test("file://W:/!test/pip-25.1.1-py3-none-any/pip", isolate=True)

    # manually test - turn on ftp server
    import_pip_test("ftp://user:pass@localhost/whl/pip-25.1.1-py3-none-any.whl", isolate=True)
    import_pip_test("ftp://user:pass@localhost/whl/pip-25.1.1.tar.gz", isolate=True)
    import_pip_test("ftp://user:pass@localhost/whl/pip", isolate=True)

    # import_pip_test("https://github.com/pypa/pip/tree/main/src/pip")
    import_pip_test("http://localhost:1080/whl/pip-25.1.1-py3-none-any.whl", isolate=True)
    import_pip_test("http://localhost:1080/whl/pip-25.1.1.tar.gz", isolate=True)
    import_pip_test("http://localhost:1080/whl/pip", isolate=True)

    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context # bypass ssl cert, not secure—use only for dev.
    import_pip_test("https://localhost:10443/whl/pip-25.1.1-py3-none-any.whl", isolate=True)
    import_pip_test("https://localhost:10443/whl/pip-25.1.1.tar.gz", isolate=True)
    import_pip_test("https://localhost:10443/whl/pip", isolate=True)

    pass


