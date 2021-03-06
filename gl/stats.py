# -*- coding: utf-8 -*-


"""The stats manager."""

import collections
import os
import sys
import threading

from gl.globals import exports_path, plugins_path, sys_path
from gl.logger import logger


class Stats(object):

    """This class stores, updates and gives stats."""

    def __init__(self, config=None, args=None):
        logger.debug("[GlancesStats.__init__]")
        # Set the config instance
        self.config = config

        # Set the argument instance
        self.args = args

        # Load plugins and exports modules
        self.load_modules(self.args)

        # Load the limits (for plugins)
        self.load_limits(config)

    def __getattr__(self, item):
        """Overwrite the getattr method in case of attribute is not found.

        The goal is to dynamically generate the following methods:
        - getPlugname(): return Plugname stat in JSON format
        """
        # Check if the attribute starts with 'get'
        if item.startswith('get'):
            # Get the plugin name
            plugname = item[len('get'):].lower()
            # Get the plugin instance
            plugin = self._plugins[plugname]
            if hasattr(plugin, 'get_stats'):
                # The method get_stats exist, return it
                return getattr(plugin, 'get_stats')
            else:
                # The method get_stats is not found for the plugin
                raise AttributeError(item)
        else:
            # Default behavior
            raise AttributeError(item)

    def load_modules(self, args):
        """Wrapper to load: plugins and export modules."""

        # Init the plugins dict
        self._plugins = collections.defaultdict(dict)
        # Load the plugins
        self.load_plugins(args=args)

        # Init the export modules dict
        self._exports = collections.defaultdict(dict)
        # Load the export modules
        self.load_exports(args=args)

        # Restoring system path
        sys.path = sys_path

    def load_plugins(self, args=None):
        """Load all plugins in the 'plugins' folder."""
        logger.debug("[load_plugins]")
        header = "glances_"
        for item in os.listdir(plugins_path):
            if (item.startswith(header) and
                    item.endswith(".py") and
                    item != (header + "plugin.py")):
                # Import the plugin
                logger.debug("[load_plugins] {} plugin import".format(
                    item
                ))
                plugin = __import__(os.path.basename(item)[:-3])
                # Add the plugin to the dictionary
                # The key is the plugin name
                # for example, the file glances_xxx.py
                # generate self._plugins_list["xxx"] = ...
                plugin_name = os.path.basename(item)[len(header):-3].lower()
                logger.debug("[load_plugins] {} plugin import".format(
                    plugin_name
                ))
                if plugin_name in ('help', 'amps', 'ports'):
                    self._plugins[plugin_name] = plugin.Plugin(args=args, config=self.config)
                else:
                    self._plugins[plugin_name] = plugin.Plugin(args=args)
        # Log plugins list
        logger.debug("Available plugins list: {}".format(self.getAllPlugins()))

    def load_exports(self, args=None):
        """Load all export modules in the 'exports' folder."""
        if args is None:
            return False
        header = "glances_"
        # Transform the arguments list into a dict
        # The aim is to chec if the export module should be loaded
        args_var = vars(locals()['args'])
        for item in os.listdir(exports_path):
            export_name = os.path.basename(item)[len(header):-3].lower()
            if (item.startswith(header) and
                    item.endswith(".py") and
                    item != (header + "export.py") and
                    item != (header + "history.py") and
                    args_var['export_' + export_name] is not None and
                    args_var['export_' + export_name] is not False):
                # Import the export module
                export_module = __import__(os.path.basename(item)[:-3])
                # Add the export to the dictionary
                # The key is the module name
                # for example, the file glances_xxx.py
                # generate self._exports_list["xxx"] = ...
                self._exports[export_name] = export_module.Export(args=args, config=self.config)
        # Log plugins list
        logger.debug("Available exports modules list: {}".format(self.getExportList()))
        return True

    def getAllPlugins(self):
        """Return the plugins list."""
        return [p for p in self._plugins]

    def getExportList(self):
        """Return the exports modules list."""
        return [e for e in self._exports]

    def load_limits(self, config=None):
        """Load the stats limits (except the one in the exclude list)."""
        # For each plugins, call the load_limits method
        for p in self._plugins:
            self._plugins[p].load_limits(config)

    def update(self):
        """Wrapper method to update the stats."""
        # For standalone and server modes
        # For each plugins, call the update method
        for p in self._plugins:
            # logger.debug("Update %s stats" % p)
            self._plugins[p].update()

    def export(self, input_stats=None):
        """Export all the stats.

        Each export module is ran in a dedicated thread.
        """
        # threads = []
        input_stats = input_stats or {}

        for e in self._exports:
            logger.debug("Export stats using the %s module" % e)
            thread = threading.Thread(target=self._exports[e].update,
                                      args=(input_stats,))
            # threads.append(thread)
            thread.start()

    def getAll(self):
        """Return all the stats (list)."""
        return [self._plugins[p].get_raw() for p in self._plugins]

    def getAllExports(self):
        """
        Return all the stats to be exported (list).
        Default behavor is to export all the stat
        """
        return [self._plugins[p].get_export() for p in self._plugins]

    def getAllAsDict(self):
        """Return all the stats (dict)."""
        # Python > 2.6
        # {p: self._plugins[p].get_raw() for p in self._plugins}
        ret = {}
        for p in self._plugins:
            ret[p] = self._plugins[p].get_raw()
        return ret

    def getAllLimits(self):
        """Return the plugins limits list."""
        return [self._plugins[p].limits for p in self._plugins]

    def getAllLimitsAsDict(self):
        """Return all the stats limits (dict)."""
        ret = {}
        for p in self._plugins:
            ret[p] = self._plugins[p].limits
        return ret

    def getAllViews(self):
        """Return the plugins views."""
        return [self._plugins[p].get_views() for p in self._plugins]

    def getAllViewsAsDict(self):
        """Return all the stats views (dict)."""
        ret = {}
        for p in self._plugins:
            ret[p] = self._plugins[p].get_views()
        return ret

    def get_plugin_list(self):
        """Return the plugin list."""
        return self._plugins

    def get_plugin(self, plugin_name):
        """Return the plugin name."""
        if plugin_name in self._plugins:
            return self._plugins[plugin_name]
        else:
            return None

    def end(self):
        """End of the Glances stats."""
        # Close export modules
        for e in self._exports:
            self._exports[e].exit()
        # Close plugins
        for p in self._plugins:
            self._plugins[p].exit()
