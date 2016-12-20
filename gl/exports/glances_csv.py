# -*- coding: utf-8 -*-


"""CSV interface class."""

import csv
import sys
import time

from gl.compat import PY3, iterkeys, itervalues
from gl.logger import logger
from gl.exports.glances_export import GlancesExport


class Export(GlancesExport):

    """This class manages the CSV export module."""

    def __init__(self, config=None, args=None):
        """Init the CSV export IF."""
        super(Export, self).__init__(config=config, args=args)

        # CSV file name
        self.csv_filename = args.export_csv

        # Set the CSV output file
        try:
            if PY3:
                self.csv_file = open(self.csv_filename, 'w', newline='')
            else:
                self.csv_file = open(self.csv_filename, 'wb')
            self.writer = csv.writer(self.csv_file)
        except IOError as e:
            logger.critical("Cannot create the CSV file: {}".format(e))
            sys.exit(2)

        logger.info("Stats exported to CSV file: {}".format(self.csv_filename))

        self.export_enable = True

        self.first_line = True

    def exit(self):
        """Close the CSV file."""
        logger.debug("Finalise export interface %s" % self.export_name)
        self.csv_file.close()

    def update(self, stats):
        """Update stats in the CSV output file."""
        # Get the stats
        all_stats = stats.getAllExports()
        plugins = stats.getAllPlugins()

        # Init data with timestamp (issue#708)
        csv_header = ['timestamp']
        csv_data = [time.strftime('%Y-%m-%d %H:%M:%S')]

        # Loop over available plugin
        for i, plugin in enumerate(plugins):
            if plugin in self.plugins_to_export():
                if isinstance(all_stats[i], list):
                    for stat in all_stats[i]:
                        # First line: header
                        if self.first_line:
                            csv_header += ('{}_{}_{}'.format(
                                plugin, self.get_item_key(stat), item) for item in stat)
                        # Others lines: stats
                        csv_data += itervalues(stat)
                elif isinstance(all_stats[i], dict):
                    # First line: header
                    if self.first_line:
                        fieldnames = iterkeys(all_stats[i])
                        csv_header += ('{}_{}'.format(plugin, fieldname)
                                       for fieldname in fieldnames)
                    # Others lines: stats
                    csv_data += itervalues(all_stats[i])

        # Export to CSV
        if self.first_line:
            self.writer.writerow(csv_header)
            self.first_line = False
        self.writer.writerow(csv_data)
        self.csv_file.flush()
