# -*- coding: utf-8 -*-


from gl import psutil_version_info
from gl.plugins.glances_plugin import GlancesPlugin


class Plugin(GlancesPlugin):
    """Get the psutil version for client/server purposes.

    stats is a tuple
    """

    def __init__(self, args=None):
        """Init the plugin."""
        super(Plugin, self).__init__(args=args)

        self.reset()

    def reset(self):
        """Reset/init the stats."""
        self.stats = None

    def update(self):
        """Update the stats."""
        # Reset stats
        self.reset()

        # Return PsUtil version as a tuple
        if self.input_method == 'local':
            # PsUtil version only available in local
            try:
                self.stats = psutil_version_info
            except NameError:
                pass
        else:
            pass

        return self.stats
