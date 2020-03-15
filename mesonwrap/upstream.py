import configparser
import io

_SECTION = 'wrap-file'


class _ConfigDescriptor:

    def __set_name__(self, owner, name):
        del owner  # unused
        self._name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            raise AttributeError('{}.{} is not supported'.format(
                owner.__name__, self._name))
        try:
            return instance._cfg.get(_SECTION, self._name)
        except (configparser.NoOptionError,
                configparser.NoSectionError) as e:
            raise ValueError('{!r} is not defined'.format(self._name)) from e

    def __set__(self, instance, value):
        if not instance._cfg.has_section(_SECTION):
            instance._cfg.add_section(_SECTION)
        instance._cfg.set(_SECTION, self._name, value)
        return value


class _ConfigHasDescriptor:

    def __set_name__(self, owner, name):
        del owner  # unused
        assert name.startswith('has_')
        self._name = name
        self._sname = name[4:]

    def __get__(self, instance, owner=None):
        if instance is None:
            raise AttributeError('{}.{} is not supported'.format(
                owner.__name__, self._name))
        return instance._cfg.has_option(_SECTION, self._sname)


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

    def has(self, attr: str, /) -> bool:
        return getattr(self, 'has_' + attr)

    directory = _ConfigDescriptor()
    has_directory = _ConfigHasDescriptor()

    lead_directory_missing = _ConfigDescriptor()
    has_lead_directory_missing = _ConfigHasDescriptor()

    source_url = _ConfigDescriptor()
    has_source_url = _ConfigHasDescriptor()

    source_filename = _ConfigDescriptor()
    has_source_filename = _ConfigHasDescriptor()

    source_hash = _ConfigDescriptor()
    has_source_hash = _ConfigHasDescriptor()

    patch_url = _ConfigDescriptor()
    has_patch_url = _ConfigHasDescriptor()

    patch_filename = _ConfigDescriptor()
    has_patch_filename = _ConfigHasDescriptor()

    patch_hash = _ConfigDescriptor()
    has_patch_hash = _ConfigHasDescriptor()
