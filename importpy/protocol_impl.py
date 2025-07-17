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
    ftp = FTP()
    ftp.connect(host, int(port) if port else 21)
    ftp.login(user=usr if usr else 'anonymouse', passwd= pwd if pwd else 'password@')
    return ftp

def ftp_files(ftp, path='.', extension=''):
    files = []
    ftp.cwd(path)
    for name, fact in ftp.mlsd():
        type = fact.get('type')
        file = f'{path}/{name}' if path != '/' else f'/{name}'
        if type == 'dir': files.extend(ftp_files(ftp, file)); ftp.cwd('..')
        elif type == 'file' and name.endswith(extension): files.append(file)
    return files

def http_files(path='.', extension=''):
    def isdir(url):
        try: return "text/html" in urllib.request.urlopen(url).headers.get('Content-Type', '')
        except: return False    
    class HTTPLinkExtractor(HTMLParser):
        def __init__(self, base):
            super().__init__()
            self.link = []
            self.base = base
        def handle_starttag(self, tag, attrs):
            if tag == "a": self.link.extend(l for n, v in attrs if n == "href" and (l:=urllib.parse.urljoin(self.base, v)).startswith(self.base))
    files = []
    html = urllib.request.urlopen(path).read().decode("utf-8")
    pasr = HTTPLinkExtractor(path)
    pasr.feed(html)
    
    for link in pasr.link:
        if isdir(link):
            files.extend(http_files(link, extension))
        elif link.endswith(extension):
            files.append(link)

    return files

#####################################

class FleMetaFinder(AbstractMetaFinder):
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'file://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role

    def imports(self, url, clean=None):
        if not hasfile(url): raise FileNotFoundError(f"[ERR] cannot find path [{url}] ...")
        pdir = url.rpartition('://')[2] # package dir
        base = os.path.dirname(pdir)    # package dir's parents
        if not os.path.isdir(pdir): raise ValueError(f"[ERR] not a directory: {pdir}")
        self.pnme = os.path.basename(pdir.rstrip("/\\"))                 # package name
        self.tree = {os.path.relpath(fpth, base).replace("\\", "/"):fpth # package tree, must always start with the package name 
                     for p, d, f in os.walk(pdir) for py in f if py.endswith('.py') and (fpth := os.path.join(p, py).replace("\\", "/"))} 
        if clean : clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, file_path):
        with open(self.tree[file_path], 'r', encoding='utf-8') as f: return f.read()
            
    def custom_loader(self, file_path, is_pkg):
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

class ZipMetaFinder(AbstractMetaFinder):
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'zip://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role

    def imports(self, url, clean = None):
        if not hasfile(url): raise FileNotFoundError(f"[ERR] cannot find path [{url}] ...")
        if not url.endswith('.whl') and not url.endswith('.zip'): return None
        self.data = zipfile.ZipFile(fetch2mem(url))
        self.tree = {p:'' for p in self.data.namelist() if p.endswith(".py")} # package tree, must always start with the package name
        self.pnme = sorted(set(path.split("/")[0] for path in self.tree))[0]  # package name
        if clean : clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, file_path) :
        return self.data.read(file_path).decode()

    def custom_loader(self, file_path, is_pkg):
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

class TgzMetaFinder(AbstractMetaFinder) :
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True) :
        super().__init__(uselazy)
        self.type = 'tgz://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role
    
    def imports(self, url, clean = None) :
        if not hasfile(url): raise FileNotFoundError(f"[ERR] cannot find path [{url}] ...")
        if not url.endswith('.tar.gz') and not url.endswith('.tgz'): return None
        obj = fetch2mem(url)
        self.data = tarfile.open(name=obj if type(obj) == str else None, fileobj=None if type(obj) == str else obj, mode="r:gz")
        self.tree = {sep[1]:self.data.extractfile(m).read().decode("utf-8")  # package tree, must always start with the package name
                     for m in self.data.getmembers() if m.isfile() and m.name.endswith(".py") and len((sep := m.name.split("src/"))) == 2}
        self.pnme = sorted(set(path.split("/")[0] for path in self.tree))[0] # package name
        if clean : clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, file_path) :
        return self.tree[file_path]

    def custom_loader(self, file_path, is_pkg) :
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

class WebMetaFinder(AbstractMetaFinder) :
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'web://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role
        self.bank = {} 

    def imports(self, url, clean=None) :
        root = url.rstrip("/")
        self.pnme = root.split("/")[-1]
        self.data = http_files(root, '.py')
        self.tree = {self.pnme + f.replace(root, ''):f for f in self.data} # 'pip/__init__.py' vs 'http://localhost:1080/[ROOT_DIR]/pip/__init__.py'
        if clean: clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, file_path) :
        path = self.tree[file_path]
        code = self.bank.get(path)
        if not code:
            code = urllib.request.urlopen(path).read().decode()
            self.bank[path] = code
        return code

    def custom_loader(self, file_path, is_pkg):
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
        root = "/".join(part[7:])    # src/pip
        base = f"https://raw.githubusercontent.com/{part[3]}/{part[4]}/{part[6]}" # raw web url
        self.data = json.loads(urllib.request.urlopen(f"https://api.github.com/repos/{part[3]}/{part[4]}/git/trees/{part[6]}?recursive=1").read().decode())
        self.tree = {path.replace('src/', ''):f"{base}/{path}" # package tree, must always start with the package name
                     for item in self.data.get('tree', []) if (path := item.get('path', '')).startswith(root + '/') and path.endswith('.py')}
        self.pnme = root.split("/")[-1]                        # package name
        if clean : clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, file_path) :
        path = self.tree[file_path] # ex, 'pip/__init__.py' to 'https://raw.githubusercontent.com/pypa/pip/main/src/pip/__init__.py'
        code = self.bank.get(path)
        if not code:
            code = urllib.request.urlopen(path).read().decode()
            self.bank[path] = code
        return code

    def custom_loader(self, file_path, is_pkg) :
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)

class FtpMetaFinder(AbstractMetaFinder):
    def __init__(self, type:str = None, uselazy:bool = True, as_finder_role:bool = True):
        super().__init__(uselazy)
        self.type = 'ftp://' if not type else type
        self.data = None # archive
        self.as_finder_role = as_finder_role
        self.ftp = None

    def imports(self, url, clean=None) :
        _user, _pass, _host, _port, _path = ftp_info(url)
        root = _path
        self.ftp = ftp_connect(_host, _port, _user, _pass) 
        self.pnme = root.rstrip("/").split("/")[-1]
        self.data = ftp_files(self.ftp, root, '.py')   
        self.tree = {self.pnme + f.replace(root, ''):f for f in self.data} # 'pip/__init__.py' vs '[ROOT_DIR]/pip/__init__.py'
        if clean: clean(self.pnme)
        return self.pnme if not self.as_finder_role else importlib.import_module(self.pnme)

    def sourcecode(self, file_path) :
        path = self.tree[file_path]
        mem = io.BytesIO()
        self.ftp.retrbinary(f"RETR {path}", mem.write)
        mem.seek(0)
        return mem.read().decode("utf-8")

    def custom_loader(self, file_path, is_pkg):
        return self.lodr(self.type, self.sourcecode, self.pnme, file_path, is_pkg)
