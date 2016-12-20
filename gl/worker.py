# -*- coding: utf-8 -*-


"""Manage the Worker session."""

from time import sleep

from gl.logger import logger
from gl.processes import gl_processes
from gl.stats import Stats
from gl.outputs.screen import Screen


class Worker(object):

    """This class creates and manages the worker"""

    def __init__(self, config=None, args=None):
        logger.debug("[Worker.__init__]")
        # Quiet mode
        self._quiet = args.quiet
        self.refresh_time = args.time

        # Init stats
        self.stats = Stats(config=config, args=args)

        # If process extended stats is disabled by user
        if not args.enable_process_extended:
            logger.debug("Extended stats for top process are disabled")
            gl_processes.disable_extended()
        else:
            logger.debug("Extended stats for top process are enabled")
            gl_processes.enable_extended()

        # Manage optionnal process filter
        if args.process_filter is not None:
            gl_processes.process_filter = args.process_filter

        if args.no_kernel_threads:
            # Ignore kernel threads in process list
            gl_processes.disable_kernel_threads()

        try:
            if args.process_tree:
                # Enable process tree view
                gl_processes.enable_tree()
        except AttributeError:
            pass

        # Initial system informations update
        self.stats.update()

        if self.quiet:
            logger.info("Quiet mode is ON: Nothing will be displayed")
            # In quiet mode, nothing is displayed
            gl_processes.max_processes = 0
        else:
            # Default number of processes to displayed is set to 50
            gl_processes.max_processes = 50

            # Init screen
            self.screen = Screen(config=config, args=args)

        # Check the latest Glances version
        #self.outdated = Outdated(config=config, args=args)

    @property
    def quiet(self):
        return self._quiet

    def __run(self):
        """Main loop for the CLI."""
        while True:
            # Update system informations
            self.stats.update()

            if not self.quiet:
                # Update the screen
                self.screen.update(self.stats)
            else:
                # Wait...
                sleep(self.refresh_time)

            # Export stats using export modules
            self.stats.export(self.stats)

    def run(self):
        """Wrapper to the serve_forever function.

        This function will restore the terminal to a sane state
        before re-raising the exception and generating a traceback.
        """
        try:
            return self.__run()
        finally:
            self.end()

    def end(self):
        """End of the standalone CLI."""
        if not self.quiet:
            self.screen.end()

        # Exit from export modules
        self.stats.end()

