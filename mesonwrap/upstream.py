import configparser
import io

_SECTION = 'wrap-file'
_ATTRS = (
    'directory',
    'lead_directory_missing',
    'source_url',
    'source_filename',
    'source_hash',
    'patch_url',
    'patch_filename',
    'patch_hash',
)


class UpstreamWrap:

    __slots__ = ('_cfg',)

    def __init__(self, **kwargs):
        self._cfg = configparser.ConfigParser()
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_string(cls, value):
        upst = cls()
        upst.read_string(value)
        return upst

    @classmethod
    def from_file(cls, filename):
        upst = cls()
        upst.read_file(filename)
        return upst

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
        if name not in _ATTRS:
            raise AttributeError('{!r} has no attribute {!r}'.format(
                type(self), name))

    def __getattr__(self, name):
        if name.startswith('has_'):
            name = name[4:]
            self.__checkattr(name)
            return self._cfg.has_option(_SECTION, name)
        self.__checkattr(name)
        try:
            return self._cfg.get(_SECTION, name)
        except (configparser.NoOptionError,
                configparser.NoSectionError) as exc:
            raise ValueError('{!r} was not defined'.format(name)) from exc

    def __setattr__(self, name, value):
        if name in self.__slots__:
            return super().__setattr__(name, value)
        self.__checkattr(name)
        if not self._cfg.has_section(_SECTION):
            self._cfg.add_section(_SECTION)
        self._cfg.set(_SECTION, name, value)
        return value
