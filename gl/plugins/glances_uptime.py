# -*- coding: utf-8 -*-

"""Uptime plugin."""

from datetime import datetime

from gl.plugins.glances_plugin import GlancesPlugin

import psutil



class Plugin(GlancesPlugin):

    """Glances uptime plugin.

    stats is date (string)
    """

    def __init__(self, args=None):
        """Init the plugin."""
        super(Plugin, self).__init__(args=args)

        # We want to display the stat in the curse interface
        self.display_curse = True

        # Set the message position
        self.align = 'right'

        # Init the stats
        self.reset()

    def reset(self):
        """Reset/init the stats."""
        self.stats = {}

    def update(self):
        """Update uptime stat using the input method."""
        # Reset stats
        self.reset()

        # Update stats using the standard system lib
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())

        # Convert uptime to string (because datetime is not JSONifi)
        self.stats = str(uptime).split('.')[0]

        # Return the result
        return self.stats

    def msg_curse(self, args=None):
        """Return the string to display in the curse interface."""
        return [self.curse_add_line('Uptime: {}'.format(self.stats))]
