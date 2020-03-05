RESTRICTED_PROJECTS = [
    'dubtestproject',
    'meson',
    'meson-ci',
    'mesonbuild.github.io',
    'mesonwrap',
    'wrapdb',
    'wrapdevtools',
    'wrapweb',
]
ISSUE_TRACKER = 'wrapdb'


class Inventory:

    def __init__(self, organization):
        self.organization = organization
        self.restricted_projects = [
            organization + '/' + proj for proj in RESTRICTED_PROJECTS
        ]
        self.issue_tracker = organization + '/' + ISSUE_TRACKER


DEFAULT = Inventory('mesonbuild')


def is_wrap_project_name(project: str) -> bool:
    return project not in RESTRICTED_PROJECTS


def is_wrap_full_project_name(full_project: str) -> bool:
    return full_project not in DEFAULT.restricted_projects
