import configparser
import dataclasses
import io
from typing import Type, TypeVar

_HAS_PREFIX = 'has_'


@dataclasses.dataclass(frozen=True)
class IniField:

    section: str
    name: str = ''


class _IniDescriptor:

    def __init__(self, field: IniField):
        self._section = field.section
        self._name = field.name

    def __get__(self, instance, owner=None):
        if instance is None:
            raise AttributeError(
                f'{owner.__name__}.{self._name} is not supported')
        try:
            return instance._cfg.get(self._section, self._name)
        except (configparser.NoOptionError,
                configparser.NoSectionError) as e:
            raise ValueError(f'{self._name!r} is not defined') from e

    def __set__(self, instance, value):
        if not instance._cfg.has_section(self._section):
            instance._cfg.add_section(self._section)
        instance._cfg.set(self._section, self._name, value)
        return value


class _IniHasDescriptor:

    def __init__(self, field: IniField):
        self._section = field.section
        self._name = field.name

    def __get__(self, instance, owner=None):
        if instance is None:
            raise AttributeError(
                f'{owner.__name__}.{_HAS_PREFIX}{self._name} is not supported')
        return instance._cfg.has_option(self._section, self._name)


class _IniMeta(type):

    def __new__(cls, name, bases, dct):
        patched_dct = {}
        for k, v in dct.items():
            if not isinstance(v, IniField):
                patched_dct[k] = v
                continue
            field = v if v.name else dataclasses.replace(v, name=k)
            patched_dct[k] = _IniDescriptor(field)
            patched_dct[_HAS_PREFIX + k] = _IniHasDescriptor(field)
        return super().__new__(cls, name, bases, patched_dct)


# https://github.com/python/typing/issues/254#issuecomment-235618152
IniFileType = TypeVar('IniFileType', bound='IniFile')


class IniFile(metaclass=_IniMeta):

    __slots__ = ('_cfg',)

    def __init__(self, **kwargs):
        self._cfg = configparser.ConfigParser()
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_string(cls: Type[IniFileType], value: str) -> IniFileType:
        inst = cls()
        inst.read_string(value)
        return inst

    @classmethod
    def from_file(cls: Type[IniFileType], filename: str) -> IniFileType:
        inst = cls()
        inst.read_file(filename)
        return inst

    def read_file(self, filename) -> None:
        with open(filename) as f:
            self._cfg.read_file(f)

    def read_string(self, value) -> None:
        self._cfg.read_string(value)

    def write(self, fp) -> None:
        self._cfg.write(fp)

    def write_file(self, filename) -> None:
        with open(filename, 'w') as fp:
            self._cfg.write(fp)

    def write_string(self) -> str:
        sio = io.StringIO()
        self._cfg.write(sio)
        return sio.getvalue()

    def has(self, attr: str) -> bool:
        # TODO: Python 3.8 make positional only
        return getattr(self, 'has_' + attr)


class WrapFile(IniFile):

    _SECTION = 'wrap-file'

    directory = IniField(_SECTION)
    lead_directory_missing = IniField(_SECTION)
    source_url = IniField(_SECTION)
    source_filename = IniField(_SECTION)
    source_hash = IniField(_SECTION)
    patch_url = IniField(_SECTION)
    patch_filename = IniField(_SECTION)
    patch_hash = IniField(_SECTION)
