# -*- coding: utf-8 -*-


from datetime import datetime

from gl.plugins.glances_plugin import GlancesPlugin


class Plugin(GlancesPlugin):

    """Plugin to get the current date/time.

    stats is (string)
    """

    def __init__(self, args=None):
        """Init the plugin."""
        super(Plugin, self).__init__(args=args)

        # We want to display the stat in the curse interface
        self.display_curse = True

        # Set the message position
        self.align = 'bottom'

    def update(self):
        """Update current date/time."""
        # Had to convert it to string because datetime is not JSON serializable
        self.stats = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return self.stats

    def msg_curse(self, args=None):
        """Return the string to display in the curse interface."""
        # Init the return message
        ret = []

        # Build the string message
        # 23 is the padding for the process list
        msg = '{:23}'.format(self.stats)
        ret.append(self.curse_add_line(msg))

        return ret
