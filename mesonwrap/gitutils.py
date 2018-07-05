import git
import os.path


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


def get_revision(repo: git.Repo, commit=None):
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
