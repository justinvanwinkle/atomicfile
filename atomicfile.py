from __future__ import unicode_literals

from tempfile import mkstemp as _mkstemp
import os as _os
import shutil as _shutil


class AtomicFile(object):
    def __init__(self,
                 name,
                 mode='w+b',
                 bufsize=-1,
                 chmod=None,
                 copy_existing=True,
                 fsync=True):
        self.name = name
        self.copy_existing = copy_existing
        self.fsync = fsync
        abs_fn = _os.path.abspath(name)
        path, fn = _os.path.split(abs_fn)

        prefix = '.' + fn
        fd, self.tmp_name = _mkstemp(prefix=prefix, dir=path)
        self.file = _os.fdopen(fd, mode, bufsize)
        if self.copy_existing and _os.path.exists(abs_fn):
            _shutil.copystat(abs_fn, self.tmp_name)
            with open(abs_fn) as existing_f:
                while 1:
                    buf = existing_f.read(16 * 1024)
                    if not buf:
                        break
                    _os.write(fd, buf)
                _os.lseek(fd, 0, _os.SEEK_SET)
        if chmod is not None:
            _os.fchmod(fd, chmod)

        self.close_called = False

    def __getattr__(self, name):
        # Attribute lookups are delegated to the underlying file
        # and cached for non-numeric results
        # (i.e. methods are cached, closed and friends are not)
        file = self.__dict__['file']
        a = getattr(file, name)
        if not issubclass(type(a), type(0)):
            setattr(self, name, a)
        return a

    # The underlying __enter__ method returns the wrong object
    # (self.file) so override it to return the wrapper
    def __enter__(self):
        print 'enter'
        self.file.__enter__()
        return self

    rename = _os.rename
    unlink = _os.unlink

    def abort(self):
        if not self.close_called:
            self.file.close()
        self.unlink(self.tmp_name)

    def close(self):
        if not self.close_called:
            self.close_called = True
            if self.fsync:
                self.file.flush()
                _os.fsync(self.file.fileno())
            self.file.close()
            try:
                self.rename(self.tmp_name, self.name)
            except OSError:
                self.abort()
                raise

    def __del__(self):
        self.abort()

    # Need to trap __exit__ as well to ensure the file gets
    # deleted when used in a with statement
    def __exit__(self, exc, value, tb):
        if exc is not None:
            self.abort()
        else:
            self.close()
        result = self.file.__exit__(exc, value, tb)
        return result
