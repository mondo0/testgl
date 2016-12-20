# -*- coding: utf-8 -*-

"""File system plugin."""

import operator

from gl.plugins.glances_plugin import GlancesPlugin

import psutil


# Define the history items list
# All items in this list will be historised if the --enable-history tag is set
# 'color' define the graph color in #RGB format
items_history_list = [{'name': 'percent',
                       'description': 'File system usage in percent',
                       'color': '#00FF00'}]


class Plugin(GlancesPlugin):

    """Glances file system plugin.

    stats is a list
    """

    def __init__(self, args=None):
        """Init the plugin."""
        super(Plugin, self).__init__(args=args, items_history_list=items_history_list)

        # We want to display the stat in the curse interface
        self.display_curse = True

        # Init the stats
        self.reset()

    def get_key(self):
        """Return the key of the list."""
        return 'mnt_point'

    def reset(self):
        """Reset/init the stats."""
        self.stats = []

    @GlancesPlugin._log_result_decorator
    def update(self):
        """Update the FS stats using the input method."""
        # Reset the list
        self.reset()

        # Update stats using the standard system lib

        # Grab the stats using the PsUtil disk_partitions
        # If 'all'=False return physical devices only (e.g. hard disks, cd-rom drives, USB keys)
        # and ignore all others (e.g. memory partitions such as /dev/shm)
        try:
            fs_stat = psutil.disk_partitions(all=False)
        except UnicodeDecodeError:
            return self.stats

        # Optionnal hack to allow logicals mounts points (issue #448)
        # Ex: Had to put 'allow=zfs' in the [fs] section of the conf file
        #     to allow zfs monitoring
        for fstype in self.get_conf_value('allow'):
            try:
                fs_stat += [f for f in psutil.disk_partitions(all=True) if f.fstype.find(fstype) >= 0]
            except UnicodeDecodeError:
                return self.stats

        # Loop over fs
        for fs in fs_stat:
            # Do not take hidden file system into account
            if self.is_hide(fs.mountpoint):
                continue
            # Grab the disk usage
            try:
                fs_usage = psutil.disk_usage(fs.mountpoint)
            except OSError:
                # Correct issue #346
                # Disk is ejected during the command
                continue
            fs_current = {
                'device_name': fs.device,
                'fs_type': fs.fstype,
                'mnt_point': fs.mountpoint,
                'size': fs_usage.total,
                'used': fs_usage.used,
                'free': fs_usage.free,
                'percent': fs_usage.percent,
                'key': self.get_key()}
            self.stats.append(fs_current)

        # Update the history list
        self.update_stats_history('mnt_point')

        # Update the view
        self.update_views()

        return self.stats

    def update_views(self):
        """Update stats views."""
        # Call the father's method
        super(Plugin, self).update_views()

        # Add specifics informations
        # Alert
        for i in self.stats:
            self.views[i[self.get_key()]]['used']['decoration'] = self.get_alert(
                i['used'], maximum=i['size'], header=i['mnt_point'])

    def msg_curse(self, args=None, max_width=None):
        """Return the dict to display in the curse interface."""
        # Init the return message
        ret = []

        # Only process if stats exist and display plugin enable...
        if not self.stats or args.disable_fs:
            return ret

        # Max size for the fsname name
        if max_width is not None and max_width >= 23:
            # Interface size name = max_width - space for interfaces bitrate
            fsname_max_width = max_width - 14
        else:
            fsname_max_width = 9

        # Build the string message
        # Header
        msg = '{:{width}}'.format('FILE SYS', width=fsname_max_width)
        ret.append(self.curse_add_line(msg, "TITLE"))
        if args.fs_free_space:
            msg = '{:>7}'.format('Free')
        else:
            msg = '{:>7}'.format('Used')
        ret.append(self.curse_add_line(msg))
        msg = '{:>7}'.format('Total')
        ret.append(self.curse_add_line(msg))

        # Filesystem list (sorted by name)
        for i in sorted(self.stats, key=operator.itemgetter(self.get_key())):
            # New line
            ret.append(self.curse_new_line())
            if i['device_name'] == '' or i['device_name'] == 'none':
                mnt_point = i['mnt_point'][-fsname_max_width + 1:]
            elif len(i['mnt_point']) + len(i['device_name'].split('/')[-1]) <= fsname_max_width - 3:
                # If possible concatenate mode info... Glances touch inside :)
                mnt_point = i['mnt_point'] + \
                    ' (' + i['device_name'].split('/')[-1] + ')'
            elif len(i['mnt_point']) > fsname_max_width:
                # Cut mount point name if it is too long
                mnt_point = '_' + i['mnt_point'][-fsname_max_width + 1:]
            else:
                mnt_point = i['mnt_point']
            msg = '{:{width}}'.format(mnt_point, width=fsname_max_width)
            ret.append(self.curse_add_line(msg))
            if args.fs_free_space:
                msg = '{:>7}'.format(self.auto_unit(i['free']))
            else:
                msg = '{:>7}'.format(self.auto_unit(i['used']))
            ret.append(self.curse_add_line(msg, self.get_views(item=i[self.get_key()],
                                                               key='used',
                                                               option='decoration')))
            msg = '{:>7}'.format(self.auto_unit(i['size']))
            ret.append(self.curse_add_line(msg))

        return ret
