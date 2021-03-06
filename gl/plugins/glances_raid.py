# -*- coding: utf-8 -*-


"""RAID plugin."""

from gl.compat import iterkeys
from gl.logger import logger
from gl.plugins.glances_plugin import GlancesPlugin

# pymdstat only available on GNU/Linux OS
try:
    from pymdstat import MdStat
except ImportError:
    logger.debug("pymdstat library not found. Glances cannot grab RAID info.")


class Plugin(GlancesPlugin):

    """Glances RAID plugin.

    stats is a dict (see pymdstat documentation)
    """

    def __init__(self, args=None):
        """Init the plugin."""
        super(Plugin, self).__init__(args=args)

        # We want to display the stat in the curse interface
        self.display_curse = True

        # Init the stats
        self.reset()

    def reset(self):
        """Reset/init the stats."""
        self.stats = {}

    @GlancesPlugin._log_result_decorator
    def update(self):
        """Update RAID stats using the input method."""
        # Reset stats
        self.reset()

        if self.input_method == 'local':
            # Update stats using the PyMDstat lib (https://github.com/nicolargo/pymdstat)
            try:
                mds = MdStat()
                self.stats = mds.get_stats()['arrays']
            except Exception as e:
                logger.debug("Can not grab RAID stats (%s)" % e)
                return self.stats

        elif self.input_method == 'snmp':
            # Update stats using SNMP
            # No standard way for the moment...
            pass

        # Update the view
        self.update_views()

        return self.stats

    def msg_curse(self, args=None):
        """Return the dict to display in the curse interface."""
        # Init the return message
        ret = []

        # Only process if stats exist and display plugin enable...
        if not self.stats or args.disable_raid:
            return ret

        # Build the string message
        # Header
        msg = '{:11}'.format('RAID disks')
        ret.append(self.curse_add_line(msg, "TITLE"))
        msg = '{:>6}'.format('Used')
        ret.append(self.curse_add_line(msg))
        msg = '{:>6}'.format('Avail')
        ret.append(self.curse_add_line(msg))
        # Data
        arrays = sorted(iterkeys(self.stats))
        for array in arrays:
            # New line
            ret.append(self.curse_new_line())
            # Display the current status
            status = self.raid_alert(self.stats[array]['status'], self.stats[array]['used'], self.stats[array]['available'])
            # Data: RAID type name | disk used | disk available
            array_type = self.stats[array]['type'].upper() if self.stats[array]['type'] is not None else 'UNKNOWN'
            msg = '{:<5}{:>6}'.format(array_type, array)
            ret.append(self.curse_add_line(msg))
            if self.stats[array]['status'] == 'active':
                msg = '{:>6}'.format(self.stats[array]['used'])
                ret.append(self.curse_add_line(msg, status))
                msg = '{:>6}'.format(self.stats[array]['available'])
                ret.append(self.curse_add_line(msg, status))
            elif self.stats[array]['status'] == 'inactive':
                ret.append(self.curse_new_line())
                msg = '└─ Status {}'.format(self.stats[array]['status'])
                ret.append(self.curse_add_line(msg, status))
                components = sorted(iterkeys(self.stats[array]['components']))
                for i, component in enumerate(components):
                    if i == len(components) - 1:
                        tree_char = '└─'
                    else:
                        tree_char = '├─'
                    ret.append(self.curse_new_line())
                    msg = '   {} disk {}: '.format(tree_char, self.stats[array]['components'][component])
                    ret.append(self.curse_add_line(msg))
                    msg = '{}'.format(component)
                    ret.append(self.curse_add_line(msg))
            if self.stats[array]['used'] < self.stats[array]['available']:
                # Display current array configuration
                ret.append(self.curse_new_line())
                msg = '└─ Degraded mode'
                ret.append(self.curse_add_line(msg, status))
                if len(self.stats[array]['config']) < 17:
                    ret.append(self.curse_new_line())
                    msg = '   └─ {}'.format(self.stats[array]['config'].replace('_', 'A'))
                    ret.append(self.curse_add_line(msg))

        return ret

    def raid_alert(self, status, used, available):
        """RAID alert messages.

        [available/used] means that ideally the array may have _available_
        devices however, _used_ devices are in use.
        Obviously when used >= available then things are good.
        """
        if status == 'inactive':
            return 'CRITICAL'
        if used < available:
            return 'WARNING'
        return 'OK'
