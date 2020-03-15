import os.path

import git


class GitFile:

    def __init__(self, filename, file, index):
        self.filename = filename
        self.file = file
        self.index = index

    def __enter__(self):
        return self.file.__enter__()

    def __exit__(self, type, value, traceback):
        self.file.__exit__(type, value, traceback)
        self.index.add([self.filename])

    @classmethod
    def open(cls, repo: git.Repo, path, mode='r'):
        abspath = os.path.join(repo.working_dir, path)
        f = open(abspath, mode)
        if f.writable():
            return cls(path, f, repo.index)
        return f


class GitProject:

    def __init__(self, repo: git.Repo):
        self.repo = repo

    def close(self):
        self.repo.close()

    def open(self, path, mode='r'):
        return GitFile.open(self.repo, path, mode)

    def commit(self, message: str):
        return self.repo.index.commit(message)

    def merge_commit(self, message, parent):
        return self.repo.index.commit(
            message, parent_commits=(self.repo.head.commit, parent))

    def create_version(self, version: str):
        self.repo.head.reference = self.repo.create_head(version)
        return self.repo.head.reference

    @property
    def git_dir(self):
        return self.repo.git_dir

    @property
    def head_hexsha(self) -> str:
        return self.repo.head.commit.hexsha


def get_revision(repo: git.Repo, commit: git.Commit = None):
    """Get revision from repo and commit.

    Revision is a number of commits between specified commit
    and first commit with upstream.wrap or commit tagged with [wrap version]
    in message."""
    # BFS over acyclic graph
    # revision is number of commits we visit
    # we cut off BFS by '[wrap revision]' and 'upstream.wrap'
    cur = commit or repo.head.commit
    commits = set()
    todo = [cur]
    while todo:
        cur = todo.pop()
        if 'upstream.wrap' not in cur.tree:
            # Must be first test, just cut off BFS.
            pass
        elif '[wrap version]' in cur.message:
            # Count commit but cut off BFS.
            commits.add(cur.hexsha)
        else:
            # Do not repeat work, we already visited this subtree.
            if cur.hexsha not in commits:
                commits.add(cur.hexsha)
                todo.extend(cur.parents)
    return len(commits)
