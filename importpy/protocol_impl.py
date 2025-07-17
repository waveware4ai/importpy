import os, io, sys, json, re
import urllib.request, urllib.parse
import zipfile, tarfile
import importlib.abc, importlib.util
from ftplib import FTP
from html.parser import HTMLParser
from urllib.error import URLError

import logging
LOG = logging.getLogger(__name__)

try: from . import __init__ as init # register as sys.modules['importpy'], run with package 
except: import __init__ as init     # register as sys.modules['__init__'], run with direct
init = init.__self__ if type(init).__name__ == 'method-wrapper' else init # else init is 'module'
protocol, AbstractMetaFinder = init.loader('./protocol.py', '*', 'AbstractMetaFinder')

def fetch2mem(url, buffer=8192):
    if url.startswith('file://'):
        path = url.rpartition('://')[2]
        return path
    elif url.startswith('ftp://'):
        _user, _pass, _host, _port, _path = ftp_info(url)
        ftp = ftp_connect(_host, _port, _user, _pass) 
        mem = io.BytesIO()
        ftp.retrbinary(f"RETR {_path}", mem.write)
        mem.seek(0)
        return mem

    try:
        req = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}))
        tot = int(req.headers.get("Content-Length", 0))
        LOG.debug(f"[INF] downloading: {url} ({tot} bytes)")
        mem = io.BytesIO()
        got = 0
        while True:
            chunk = req.read(buffer)
            if not chunk:
                break
            mem.write(chunk)
            got += len(chunk)
            percent = (got / tot) * 100 if tot else 0
            LOG.debug(f"\r[INF] {got}/{tot} bytes ({percent:.2f}%)")
        LOG.debug("[INF] fetch2mem complete!")
        mem.seek(0)
        return mem
    except Exception as e:
        LOG.debug(f"[ERR] fetch2mem failed: {e}")
        return None
    
def fetch2file(url, file: str) :
    mem = fetch2mem(url)
    with open(file, "wb") as f:
        f.write(mem.getbuffer())
    pass

def hasfile(url: str) -> bool :
    try:
        if False: pass
        elif url.startswith('file://'):
            path = url.rpartition('://')[2]
            return os.path.exists(path)
        elif url.startswith(('http://', 'https://')):
            with urllib.request.urlopen(url, timeout=1) as r: return r.status == 200
        elif url.startswith('ftp://'):
            _user, _pass, _host, _port, _path = ftp_info(url)
            ftp = ftp_connect(_host, _port, _user, _pass) 
            dir = _path.rpartition('/')[0]
            fle = _path.rpartition('/')[2]
            ftp.cwd(dir)
            lst = [n for n, f in ftp.mlsd() if f.get("type") == "file"]
            return any(n == fle for n in lst) # generator debuging work hard ~~~ ㅠㅠ
        elif url.startswith('sftp://'):
            pass
        pass
    except :
        raise URLError(f"[ERR] invalid url [{url}] ...")

#####################################

PROTO_FTP_RE = re.compile(r"^ftp://(?:(?P<user>[^:@]+)(?::(?P<pass>[^@]+))?@)?(?P<host>[^:/]+)(?::(?P<port>\d+))?(?P<path>/.*)$")
def ftp_info(url: str) :
    FTP_INFO = PROTO_FTP_RE.match(url) 
    _user = FTP_INFO.group("user") 
    _pass = FTP_INFO.group("pass") 
    _host = FTP_INFO.group("host") 
    _port = FTP_INFO.group("port") 
    _path = FTP_INFO.group("path") 
    return _user, _pass, _host, _port, _path.rstrip('/')

def ftp_connect(host, port='21', usr='', pwd='') -> FTP:
    _ftp = FTP()
    _ftp.connect(host, int(port) if port else 21)
    _ftp.login(user=usr if usr else 'anonymouse', passwd= pwd if pwd else 'password@')
    return _ftp

def ftp_files(_ftp, path='.', depth=0, extension=''):
    def isdir(_ftp, path):
        try: _ftp.cwd(path); return True
        except: return False
    ftp_files.isdir = isdir # tricky for access
    def source(_ftp, path='.') :
        mem = io.BytesIO()
        _ftp.retrbinary(f"RETR {path}", mem.write)
        mem.seek(0)
        return mem.read().decode("utf-8")
    ftp_files.source = source # tricky for access

    path = path if 0 < depth or isdir(_ftp, path) else path.rpartition('/')[0]
    _ftp.cwd(path)
    list = []
    list.append(path)
    for name, fact in _ftp.mlsd():
        type = fact.get('type')
        file = f'{path}/{name}' if path != '/' else f'/{name}'
        if type == 'dir': list.extend(ftp_files(_ftp, file, depth+1)); _ftp.cwd('..')
        elif type == 'file' and name.endswith(extension): list.append(file)
    return list

def http_files(path='.', depth=0, extension=''):
    def isdir(url):
        try: return "text/html" in urllib.request.urlopen(url).headers.get('Content-Type', '')
        except: return False    
    http_files.isdir = isdir # tricky for access
    def source(path) :
        code = urllib.request.urlopen(path).read().decode()
        return code
    http_files.source = source # tricky for access
    class HTTPLinkExtractor(HTMLParser):
        def __init__(self, base):
            super().__init__()
            self.link = []
            self.base = base
        def handle_starttag(self, tag, attrs):
            if tag == "a": self.link.extend(l for n, v in attrs if n == "href" and (l:=urllib.parse.urljoin(self.base, v)).startswith(self.base))

    path = path if 0 < depth or isdir(path) else path.rpartition('/')[0]
    html = urllib.request.urlopen(path).read().decode("utf-8")
    pasr = HTTPLinkExtractor(path)
    pasr.feed(html)

    files = []
    files.append(path)
    for link in pasr.link:
        if isdir(link):
            files.append(link)
            files.extend(http_files(link, depth+1, extension))
        elif link.endswith(extension):
            files.append(link)

    return files

#####################################

def strip_type(url: str) -> str :
    return url.rpartition('://')[2]
def strip_dotpy(path: str) -> str :
    return path.partition('.py')[0]
def normalized_path(path: str) -> str : # nomalized path
    return path.replace("\\", "/").rstrip('/')
def normalized_dots(path: str) -> str : # nomalized tree-key
    return normalized_path(strip_dotpy(path)).replace("/", ".")

class FleMetaFinder(AbstractMetaFinder):
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'file://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role

    def imports(self, url, clean=None):
        if not hasfile(url): raise FileNotFoundError(f"[ERR] cannot find path [{url}] ...")
        root = normalized_path(strip_type(url)) # remove file://
        base = os.path.dirname(root) # if root is a dir, it works as a package, if file as a module 
        wdir = root if os.path.isdir(root) else os.path.dirname(root) # walk dir
        self.pnme = strip_dotpy(root.split("/")[-1]) 
        self.data = [normalized_path(os.path.join(p, py)) for p, _, f in os.walk(wdir) for py in f if py.endswith('.py')] + [normalized_path(p) for p, _, _ in os.walk(wdir)]
        self.tree = {normalized_dots(os.path.relpath(f, base)):f for f in self.data} # 'pip.__init__' vs 'c:/[FILE_DIR]/pip/__init__.py'
        if clean : clean(self.pnme) 
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, dot_path):
        if not dot_path in self.tree: return ''
        if os.path.isdir(self.tree[dot_path]): return ''
        with open(self.tree[dot_path], 'r', encoding='utf-8') as f: return f.read()
            
    def custom_loader(self, file_path, is_pkg):
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

class WebMetaFinder(AbstractMetaFinder) :
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'web://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role
        self.inst = http_files # instrumentation
        self.bank = {} 

    def imports(self, url, clean=None) :
        root = url.rstrip("/") 
        base = os.path.dirname(root) # if root is a dir, it works as a package, if file, as a module 
        self.pnme = strip_dotpy(root.split("/")[-1])
        self.data = self.inst(root, extension='.py')
        self.tree = {normalized_dots(os.path.relpath(f, base)):f for f in self.data} # 'pip.__init__' vs 'http://localhost:1080/[ROOT_DIR]/pip/__init__.py'
        if clean: clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, dot_path) :
        if self.inst.isdir(self.tree[dot_path]): return ''
        path = self.tree[dot_path]
        code = self.bank.get(path)
        if code: return code
        self.bank[path] = self.inst.source(path)
        return self.bank[path]

    def custom_loader(self, file_path, is_pkg):
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

class FtpMetaFinder(AbstractMetaFinder):
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'ftp://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role
        self._ftp = None
        self.inst = ftp_files # instrumentation
        self.bank = {} 

    def imports(self, url, clean=None) :
        _user, _pass, _host, _port, _path = ftp_info(url)
        root = _path
        base = os.path.dirname(root) # if root is a dir, it works as a package, if file, as a module 
        self._ftp = ftp_connect(_host, _port, _user, _pass)
        self.data = self.inst(self._ftp, root, extension='.py')  
        self.pnme = strip_dotpy(root.split("/")[-1]) 
        self.tree = {normalized_dots(os.path.relpath(f, base)):f for f in self.data} # 'pip.__init__' vs '[ROOT_DIR]/pip/__init__.py'
        if clean: clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, dot_path) :
        if self.inst.isdir(self._ftp, self.tree[dot_path]): return ''
        path = self.tree[dot_path]
        code = self.bank.get(path)
        if code: return code
        self.bank[path] = self.inst.source(self._ftp, path)
        return self.bank[path]
    
    def custom_loader(self, file_path, is_pkg):
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

#####################################

class ZipMetaFinder(AbstractMetaFinder):
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'zip://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role
        self.inst = None # instrumentation

    def imports(self, url, clean = None):
        if not hasfile(url): raise FileNotFoundError(f"[ERR] cannot find path [{url}] ...")
        if not url.endswith('.whl') and not url.endswith('.zip'): return None
        self.inst = zipfile.ZipFile(fetch2mem(url))
        name_list = self.inst.namelist() 
        self.data = [p for p in name_list if p.endswith(".py")] + list({os.path.dirname(p) for p in name_list})
        self.tree = {normalized_dots(p):p for p in self.data} 
        self.pnme = sorted(set(p.split("/")[0] for p in self.tree))[0]  # package name
        if clean : clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, dot_path) :
        if not dot_path in self.tree: return None
        return self.inst.read(self.tree[dot_path]).decode()

    def custom_loader(self, file_path, is_pkg):
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

class TgzMetaFinder(AbstractMetaFinder) :
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True) :
        super().__init__(uselazy)
        self.type = 'tgz://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role
        self.inst = None # instrumentation
    
    def imports(self, url, clean = None) :
        if not hasfile(url): raise FileNotFoundError(f"[ERR] cannot find path [{url}] ...")
        if not url.endswith('.tar.gz') and not url.endswith('.tgz'): return None
        obj = fetch2mem(url)
        self.inst = tarfile.open(name=obj if type(obj) == str else None, fileobj=None if type(obj) == str else obj, mode="r:gz")
        self.save = {sep[1]:self.inst.extractfile(m).read().decode("utf-8")  # package tree, must always start with the package name
                     for m in self.inst.getmembers() if m.isfile() and m.name.endswith(".py") and len((sep := m.name.split("src/"))) == 2}
        self.data = [p for p in self.save if p.endswith(".py")] + list({os.path.dirname(p) for p in self.save})
        self.tree = {normalized_dots(p):(self.save.get(p, '')) for p in self.data} 
        self.pnme = sorted(set(path.split("/")[0] for path in self.tree))[0] # package name
        if clean : clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, dot_path) :
        if not dot_path in self.tree: return None
        return self.tree[dot_path]

    def custom_loader(self, file_path, is_pkg) :
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

class GitMetaFinder(AbstractMetaFinder):
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'git://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role
        self.bank = {}

    def imports(self, url, clean = None):
        part = url.rstrip("/").split("/") # ex, https://github.com/pypa/pip/tree/main/src/pip, part[3]==pypa, part[4]=pip, part[6]=main
        root = "/".join(part[7:]) # src/pip
        base = f"https://raw.githubusercontent.com/{part[3]}/{part[4]}/{part[6]}" # raw web url
        self.json = json.loads(urllib.request.urlopen(f"https://api.github.com/repos/{part[3]}/{part[4]}/git/trees/{part[6]}?recursive=1").read().decode())
        self.save = {path.replace('src/', ''):f"{base}/{path}" # package tree, must always start with the package name
                     for item in self.json.get('tree', []) if (path := item.get('path', '')).startswith(root + '/') and path.endswith('.py')}
        self.data = [p for p in self.save if p.endswith(".py")] + list({os.path.dirname(p) for p in self.save})
        self.tree = {normalized_dots(p):(self.save.get(p, '')) for p in self.data} 
        self.pnme = root.split("/")[-1]                        # package name
        if clean : clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, dot_path) :
        if not dot_path in self.tree: return None
        path = self.tree[dot_path] # ex, 'pip.__init__' to 'https://raw.githubusercontent.com/pypa/pip/main/src/pip/__init__.py'
        code = self.bank.get(path)
        if code: return code
        self.bank[path] = urllib.request.urlopen(path).read().decode()
        return self.bank[path]

    def custom_loader(self, file_path, is_pkg) :
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

