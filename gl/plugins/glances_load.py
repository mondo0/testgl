# -*- coding: utf-8 -*-

"""Load plugin."""

import os

from gl.plugins.glances_core import Plugin as CorePlugin
from gl.plugins.glances_plugin import GlancesPlugin


# Define the history items list
# All items in this list will be historised if the --enable-history tag is set
# 'color' define the graph color in #RGB format
items_history_list = [{'name': 'min1',
                       'description': '1 minute load',
                       'color': '#0000FF'},
                      {'name': 'min5',
                       'description': '5 minutes load',
                       'color': '#0000AA'},
                      {'name': 'min15',
                       'description': '15 minutes load',
                       'color': '#000044'}]


class Plugin(GlancesPlugin):

    """Glances load plugin.

    stats is a dict
    """

    def __init__(self, args=None):
        """Init the plugin."""
        super(Plugin, self).__init__(args=args, items_history_list=items_history_list)

        # We want to display the stat in the curse interface
        self.display_curse = True

        # Init stats
        self.reset()

        # Call CorePlugin in order to display the core number
        try:
            self.nb_log_core = CorePlugin(args=self.args).update()["log"]
        except Exception:
            self.nb_log_core = 1

    def reset(self):
        """Reset/init the stats."""
        self.stats = {}

    @GlancesPlugin._log_result_decorator
    def update(self):
        """Update load stats."""
        # Reset stats
        self.reset()

        # Update stats using the standard system lib

        # Get the load using the os standard lib
        try:
            load = os.getloadavg()
        except (OSError, AttributeError):
            self.stats = {}
        else:
            self.stats = {'min1': load[0],
                          'min5': load[1],
                          'min15': load[2],
                          'cpucore': self.nb_log_core}

        # Update the history list
        self.update_stats_history()

        # Update the view
        self.update_views()

        return self.stats

    def update_views(self):
        """Update stats views."""
        # Call the father's method
        super(Plugin, self).update_views()

        # Add specifics informations
        try:
            # Alert and log
            self.views['min15']['decoration'] = self.get_alert_log(self.stats['min15'], maximum=100 * self.stats['cpucore'])
            # Alert only
            self.views['min5']['decoration'] = self.get_alert(self.stats['min5'], maximum=100 * self.stats['cpucore'])
        except KeyError:
            # try/except mandatory for Windows compatibility (no load stats)
            pass

    def msg_curse(self, args=None):
        """Return the dict to display in the curse interface."""
        # Init the return message
        ret = []

        # Only process if stats exist, not empty (issue #871) and plugin not disabled
        if not self.stats or (self.stats == {}) or args.disable_load:
            return ret

        # Build the string message
        # Header
        msg = '{:8}'.format('LOAD')
        ret.append(self.curse_add_line(msg, "TITLE"))
        # Core number
        if 'cpucore' in self.stats and self.stats['cpucore'] > 0:
            msg = '{}-core'.format(int(self.stats['cpucore']))
            ret.append(self.curse_add_line(msg))
        # New line
        ret.append(self.curse_new_line())
        # 1min load
        msg = '{:8}'.format('1 min:')
        ret.append(self.curse_add_line(msg))
        msg = '{:>6.2f}'.format(self.stats['min1'])
        ret.append(self.curse_add_line(msg))
        # New line
        ret.append(self.curse_new_line())
        # 5min load
        msg = '{:8}'.format('5 min:')
        ret.append(self.curse_add_line(msg))
        msg = '{:>6.2f}'.format(self.stats['min5'])
        ret.append(self.curse_add_line(
            msg, self.get_views(key='min5', option='decoration')))
        # New line
        ret.append(self.curse_new_line())
        # 15min load
        msg = '{:8}'.format('15 min:')
        ret.append(self.curse_add_line(msg))
        msg = '{:>6.2f}'.format(self.stats['min15'])
        ret.append(self.curse_add_line(
            msg, self.get_views(key='min15', option='decoration')))

        return ret
