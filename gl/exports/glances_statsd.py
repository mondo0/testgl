# -*- coding: utf-8 -*-


"""Statsd interface class."""

import sys
from numbers import Number

from gl.compat import NoOptionError, NoSectionError, range
from gl.logger import logger
from gl.exports.glances_export import GlancesExport

from statsd import StatsClient


class Export(GlancesExport):

    """This class manages the Statsd export module."""

    def __init__(self, config=None, args=None):
        """Init the Statsd export IF."""
        super(Export, self).__init__(config=config, args=args)

        # Load the InfluxDB configuration file
        self.host = None
        self.port = None
        self.prefix = None
        self.export_enable = self.load_conf()
        if not self.export_enable:
            sys.exit(2)

        # Default prefix for stats is 'glances'
        if self.prefix is None:
            self.prefix = 'glances'

        # Init the Statsd client
        self.client = StatsClient(self.host,
                                  int(self.port),
                                  prefix=self.prefix)

    def load_conf(self, section="statsd"):
        """Load the Statsd configuration in the Glances configuration file."""
        if self.config is None:
            return False
        try:
            self.host = self.config.get_value(section, 'host')
            self.port = self.config.get_value(section, 'port')
        except NoSectionError:
            logger.critical("No Statsd configuration found")
            return False
        except NoOptionError as e:
            logger.critical("Error in the Statsd configuration (%s)" % e)
            return False
        else:
            logger.debug("Load Statsd from the Glances configuration file")
        # Prefix is optional
        try:
            self.prefix = self.config.get_value(section, 'prefix')
        except NoOptionError:
            pass
        return True

    def init(self, prefix='glances'):
        """Init the connection to the Statsd server."""
        if not self.export_enable:
            return None
        return StatsClient(self.host,
                           self.port,
                           prefix=prefix)

    def export(self, name, columns, points):
        """Export the stats to the Statsd server."""
        for i in range(len(columns)):
            if not isinstance(points[i], Number):
                continue
            stat_name = '{}.{}'.format(name, columns[i])
            stat_value = points[i]
            try:
                self.client.gauge(stat_name, stat_value)
            except Exception as e:
                logger.error("Can not export stats to Statsd (%s)" % e)
        logger.debug("Export {} stats to Statsd".format(name))
