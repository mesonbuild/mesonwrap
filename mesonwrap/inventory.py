_ORGANIZATION = 'mesonbuild'
_RESTRICTED_PROJECTS = [
    'meson',
    'meson-ci',
    'mesonwrap',
    'wrapweb',
]
_RESTRICTED_ORG_PROJECTS = [
    _ORGANIZATION + '/' + proj for proj in _RESTRICTED_PROJECTS
]


def is_wrap_project_name(project: str) -> bool:
    return project not in _RESTRICTED_PROJECTS


def is_wrap_full_project_name(full_project: str) -> bool:
    return full_project not in _RESTRICTED_ORG_PROJECTS
