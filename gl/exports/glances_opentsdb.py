# -*- coding: utf-8 -*-


"""OpenTSDB interface class."""

import sys
from numbers import Number

from gl.compat import NoOptionError, NoSectionError, range
from gl.logger import logger
from gl.exports.glances_export import GlancesExport

import potsdb


class Export(GlancesExport):

    """This class manages the OpenTSDB export module."""

    def __init__(self, config=None, args=None):
        """Init the OpenTSDB export IF."""
        super(Export, self).__init__(config=config, args=args)

        # Load the InfluxDB configuration file
        self.host = None
        self.port = None
        self.prefix = None
        self.tags = None
        self.export_enable = self.load_conf()
        if not self.export_enable:
            sys.exit(2)

        # Default prefix for stats is 'glances'
        if self.prefix is None:
            self.prefix = 'glances'

        # Init the OpenTSDB client
        self.client = self.init()

    def load_conf(self, section="opentsdb"):
        """Load the OpenTSDB configuration in the Glances configuration file."""
        if self.config is None:
            return False
        try:
            self.host = self.config.get_value(section, 'host')
            self.port = self.config.get_value(section, 'port')
        except NoSectionError:
            logger.critical("No OpenTSDB configuration found")
            return False
        except NoOptionError as e:
            logger.critical("Error in the OpenTSDB configuration (%s)" % e)
            return False
        else:
            logger.debug("Load OpenTSDB from the Glances configuration file")

        # Prefix is optional
        try:
            self.prefix = self.config.get_value(section, 'prefix')
        except NoOptionError:
            pass

        # Tags are optional, comma separated key:value pairs.
        try:
            self.tags = self.config.get_value(section, 'tags')
        except NoOptionError:
            pass

        return True

    def init(self):
        """Init the connection to the OpenTSDB server."""
        if not self.export_enable:
            return None

        try:
            db = potsdb.Client(self.host,
                               port=int(self.port),
                               check_host=True)
        except Exception as e:
            logger.critical("Cannot connect to OpenTSDB server %s:%s (%s)" % (self.host, self.port, e))
            sys.exit(2)

        return db

    def export(self, name, columns, points):
        """Export the stats to the Statsd server."""
        for i in range(len(columns)):
            if not isinstance(points[i], Number):
                continue
            stat_name = '{}.{}.{}'.format(self.prefix, name, columns[i])
            stat_value = points[i]
            tags = self.parse_tags(self.tags)
            try:
                self.client.send(stat_name, stat_value, **tags)
            except Exception as e:
                logger.error("Can not export stats %s to OpenTSDB (%s)" % (name, e))
        logger.debug("Export {} stats to OpenTSDB".format(name))

    def exit(self):
        """Close the OpenTSDB export module."""
        # Waits for all outstanding metrics to be sent and background thread closes
        self.client.wait()
        # Call the father method
        super(Export, self).exit()
