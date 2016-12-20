# -*- coding: utf-8 -*-

"""Init the Glances software."""

import locale
import platform
import signal
import sys

# Global name
__appname__ = 'gl'
__version__ = '1.0.1'

# Check Linux platform
from gl.globals import LINUX
if not LINUX:
    print('This is not LINUX platform. Glances cannot start.')
    sys.exit(1)

# Import psutil
try:
    from psutil import __version__ as psutil_version
except ImportError:
    print('PSutil library not found. Glances cannot start.')
    sys.exit(1)

from gl.logger import logger
from gl.main import GlMain
from gl.worker import Worker

try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    print("Warning: Unable to set locale. Expect encoding problems.")

# Check Python version
if sys.version_info[:2] == (2, 6):
    import warnings
    warnings.warn('Python 2.6 support is dropped. Please switch to at '
                  'least Python 2.7/3.3+ or downgrade to Glances 2.6.2.')
if sys.version_info < (2, 7) or (3, 0) <= sys.version_info < (3, 3):
    print('Glances requires at least Python 2.7 or 3.3 to run.')
    sys.exit(1)

# Check PSutil version
psutil_min_version = (2, 0, 0)
psutil_version_info = tuple([int(num) for num in psutil_version.split('.')])
if psutil_version_info < psutil_min_version:
    print('PSutil 2.0 or higher is needed. Glances cannot start.')
    sys.exit(1)


def __signal_handler(signal, frame):
    """Callback for CTRL-C."""
    end()


def end():
    """Stop Glances."""
    worker.end()
    logger.info("Stop Glances (with CTRL-C)")

    # The end...
    sys.exit(0)


def main():
    """Main entry point for Glances.

    Select the mode (standalone, client or server)
    Run it...
    """
    # Log Glances and PSutil version
    logger.info('Start Glances {}'.format(__version__))
    logger.info('{} {} and PSutil {} detected'.format(
        platform.python_implementation(),
        platform.python_version(),
        psutil_version))

    # Share global var
    global core, worker

    # Create the Glances main instance
    core = GlMain()

    # Catch the CTRL-C signal
    signal.signal(signal.SIGINT, __signal_handler)

    # Init the worker
    worker = Worker(config=core.get_config(),
                    args=core.get_args())

    # Start the standalone (CLI) loop
    worker.run()

