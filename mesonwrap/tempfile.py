# Let's try to make it drop-in replacement for tempfile module
import platform as _platform
from tempfile import *  # noqa: F403

from mesonwrap import tempfile_helper as _tempfile_helper


# It is not desirable to maintain completely separate implementation
# of TemporaryDirectory, however it is beneficial for Windows users
# that have antivirus software that interferes with file deletion.
# As a compromise the code below tries to override standard TemporaryDirectory
# cleanup() method in order to hook _tempfile_helper.windows_proof_rmtree().
# Since _finalizer is not public this implementation may partially break
# in the future, but expected failure mode in this case is just a double
# finalization, hence possible warning.
class _WindowsTemporaryDirectory(TemporaryDirectory):  # noqa: F405

    def cleanup(self):
        # Override explicit cleanup only, don't try to hack into weakref.
        # This will get called in any explicit execution path
        # including context manager, but will not be attempted
        # on reference loss.
        if not hasattr(self, '_finalizer') or self._finalizer.detach():
            _tempfile_helper.windows_proof_rmtree(self.name)


if _platform.system() == 'Windows':
    TemporaryDirectory = _WindowsTemporaryDirectory
