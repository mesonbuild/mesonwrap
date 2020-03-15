import dataclasses


def _base_name(name: str, version: str, revision: int) -> str:
    return '{name}-{version}-{revision}-wrap'.format(
        name=name, version=version, revision=revision)


def wrapfile_name(name: str, version: str, revision: int) -> str:
    return _base_name(name, version, revision) + '.wrap'


def zip_name(name: str, version: str, revision: int) -> str:
    return _base_name(name, version, revision) + '.zip'


@dataclasses.dataclass
class Wrap:

    name: str
    version: str
    revision: int
    wrapfile_content: str
    zip: bytes
    commit_sha: str

    @property
    def wrapfile_name(self):
        return wrapfile_name(self.name, self.version, self.revision)

    @property
    def zip_name(self):
        return zip_name(self.name, self.version, self.revision)
