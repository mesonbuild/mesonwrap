import configparser
import io


class UpstreamWrap:

    __section = 'wrap-file'
    __attrs = (
        'directory',
        'source_url',
        'source_filename',
        'source_hash',
        'patch_url',
        'patch_filename',
        'patch_hash',
    )
    __slots__ = ('_cfg')

    def __init__(self, filename=None):
        self._cfg = configparser.ConfigParser()
        if filename is not None:
            self.read_file(filename)

    def read_file(self, filename):
        with open(filename) as f:
            self._cfg.read_file(f)

    def read_string(self, value):
        self._cfg.read_string(value)

    def write(self, fp):
        self._cfg.write(fp)

    def write_file(self, filename):
        with open(filename, 'w') as fp:
            self._cfg.write(fp)

    def write_string(self):
        sio = io.StringIO()
        self._cfg.write(sio)
        return sio.getvalue()

    def __checkattr(self, name):
        if name not in self.__attrs:
            raise AttributeError('{!r} has no attribute {!r}'.format(type(self), name))

    def __getattr__(self, name):
        if name in self.__slots__:
            return super(UpstreamWrap, self).__getattr__(name)
        self.__checkattr(name)
        return self._cfg.get(self.__section, name)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            return super(UpstreamWrap, self).__setattr__(name, value)
        self.__checkattr(name)
        if not self._cfg.has_section(self.__section):
            self._cfg.add_section(self.__section)
        self._cfg.set(self.__section, name, value)
        return value
