# -*- coding: utf-8 -*-


"""Riemann interface class."""

import socket
import sys
from numbers import Number

from gl.compat import NoOptionError, NoSectionError, range
from gl.logger import logger
from gl.exports.glances_export import GlancesExport

# Import bernhard for Riemann
import bernhard


class Export(GlancesExport):

    """This class manages the Riemann export module."""

    def __init__(self, config=None, args=None):
        """Init the Riemann export IF."""
        super(Export, self).__init__(config=config, args=args)

        # Load the Riemann configuration
        self.riemann_host = None
        self.riemann_port = None
        self.hostname = socket.gethostname()
        self.export_enable = self.load_conf()
        if not self.export_enable:
            sys.exit(2)

        # Init the Riemann client
        self.client = self.init()

    def load_conf(self, section="riemann"):
        """Load the Riemann configuration in the Glances configuration file."""
        if self.config is None:
            return False
        try:
            self.riemann_host = self.config.get_value(section, 'host')
            self.riemann_port = int(self.config.get_value(section, 'port'))
        except NoSectionError:
            logger.critical("No riemann configuration found")
            return False
        except NoOptionError as e:
            logger.critical("Error in the Riemann configuration (%s)" % e)
            return False
        else:
            logger.debug("Load Riemann from the Glances configuration file")
        return True

    def init(self):
        """Init the connection to the Riemann server."""
        if not self.export_enable:
            return None
        try:
            client = bernhard.Client(host=self.riemann_host, port=self.riemann_port)
            return client
        except Exception as e:
            logger.critical("Connection to Riemann failed : %s " % e)
            return None

    def export(self, name, columns, points):
        """Write the points in Riemann."""
        for i in range(len(columns)):
            if not isinstance(points[i], Number):
                continue
            else:
                data = {'host': self.hostname, 'service': name + " " + columns[i], 'metric': points[i]}
                logger.debug(data)
                try:
                    self.client.send(data)
                except Exception as e:
                    logger.error("Cannot export stats to Riemann (%s)" % e)
