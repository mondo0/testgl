# -*- coding: utf-8 -*-


"""Process count plugin."""

from gl.processes import gl_processes
from gl.plugins.glances_plugin import GlancesPlugin

# Note: history items list is not compliant with process count
#       if a filter is applyed, the graph will show the filtered processes count


class Plugin(GlancesPlugin):

    """Glances process count plugin.

    stats is a list
    """

    def __init__(self, args=None):
        """Init the plugin."""
        super(Plugin, self).__init__(args=args)

        # We want to display the stat in the curse interface
        self.display_curse = True

        # Note: 'gl_processes' is already init in the gl_processes.py script

    def reset(self):
        """Reset/init the stats."""
        self.stats = {}

    def update(self):
        """Update processes stats using the input method."""
        # Reset stats
        self.reset()

        if self.input_method == 'local':
            # Update stats using the standard system lib
            # Here, update is call for processcount AND processlist
            gl_processes.update()

            # Return the processes count
            self.stats = gl_processes.getcount()
        elif self.input_method == 'snmp':
            # Update stats using SNMP
            # !!! TODO
            pass

        return self.stats

    def msg_curse(self, args=None):
        """Return the dict to display in the curse interface."""
        # Init the return message
        ret = []

        # Only process if stats exist and display plugin enable...
        if args.disable_process:
            msg = "PROCESSES DISABLED (press 'z' to display)"
            ret.append(self.curse_add_line(msg))
            return ret

        if not self.stats:
            return ret

        # Display the filter (if it exists)
        if gl_processes.process_filter is not None:
            msg = 'Processes filter:'
            ret.append(self.curse_add_line(msg, "TITLE"))
            msg = ' {} '.format(gl_processes.process_filter)
            if gl_processes.process_filter_key is not None:
                msg += 'on column {} '.format(gl_processes.process_filter_key)
            ret.append(self.curse_add_line(msg, "FILTER"))
            msg = '(\'ENTER\' to edit, \'E\' to reset)'
            ret.append(self.curse_add_line(msg))
            ret.append(self.curse_new_line())

        # Build the string message
        # Header
        msg = 'TASKS'
        ret.append(self.curse_add_line(msg, "TITLE"))
        # Compute processes
        other = self.stats['total']
        msg = '{:>4}'.format(self.stats['total'])
        ret.append(self.curse_add_line(msg))

        if 'thread' in self.stats:
            msg = ' ({} thr),'.format(self.stats['thread'])
            ret.append(self.curse_add_line(msg))

        if 'running' in self.stats:
            other -= self.stats['running']
            msg = ' {} run,'.format(self.stats['running'])
            ret.append(self.curse_add_line(msg))

        if 'sleeping' in self.stats:
            other -= self.stats['sleeping']
            msg = ' {} slp,'.format(self.stats['sleeping'])
            ret.append(self.curse_add_line(msg))

        msg = ' {} oth '.format(other)
        ret.append(self.curse_add_line(msg))

        # Display sort information
        if gl_processes.auto_sort:
            msg = 'sorted automatically'
            ret.append(self.curse_add_line(msg))
            msg = ' by {}'.format(gl_processes.sort_key)
            ret.append(self.curse_add_line(msg))
        else:
            msg = 'sorted by {}'.format(gl_processes.sort_key)
            ret.append(self.curse_add_line(msg))
        ret[-1]["msg"] += ", %s view" % ("tree" if gl_processes.is_tree_enabled() else "flat")
        # if args.disable_irix:
        #     ret[-1]["msg"] += " - IRIX off"

        # Return the message with decoration
        return ret
