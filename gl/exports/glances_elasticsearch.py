# -*- coding: utf-8 -*-


"""ElasticSearch interface class."""

import sys
from datetime import datetime

from gl.compat import NoOptionError, NoSectionError
from gl.logger import logger
from gl.exports.glances_export import GlancesExport

from elasticsearch import Elasticsearch, helpers


class Export(GlancesExport):

    """This class manages the ElasticSearch (ES) export module."""

    def __init__(self, config=None, args=None):
        """Init the ES export IF."""
        super(Export, self).__init__(config=config, args=args)

        # Load the ES configuration file
        self.host = None
        self.port = None
        self.index = None
        self.export_enable = self.load_conf()
        if not self.export_enable:
            sys.exit(2)

        # Init the ES client
        self.client = self.init()

    def load_conf(self, section="elasticsearch"):
        """Load the ES configuration in the Glances configuration file."""
        if self.config is None:
            return False
        try:
            self.host = self.config.get_value(section, 'host')
            self.port = self.config.get_value(section, 'port')
            self.index = self.config.get_value(section, 'index')
        except NoSectionError:
            logger.critical("No ElasticSearch configuration found")
            return False
        except NoOptionError as e:
            logger.critical("Error in the ElasticSearch configuration (%s)" % e)
            return False
        else:
            logger.debug("Load ElasticSearch from the Glances configuration file")

        return True

    def init(self):
        """Init the connection to the ES server."""
        if not self.export_enable:
            return None

        try:
            es = Elasticsearch(hosts=['{}:{}'.format(self.host, self.port)])
        except Exception as e:
            logger.critical("Cannot connect to ElasticSearch server %s:%s (%s)" % (self.host, self.port, e))
            sys.exit(2)
        else:
            logger.info("Connected to the ElasticSearch server %s:%s" % (self.host, self.port))

        try:
            index_count = es.count(index=self.index)['count']
        except Exception as e:
            # Index did not exist, it will be created at the first write
            # Create it...
            es.indices.create(self.index)
        else:
            logger.info("There is already %s entries in the ElasticSearch %s index" % (index_count, self.index))

        return es

    def export(self, name, columns, points):
        """Write the points to the ES server."""
        logger.debug("Export {} stats to ElasticSearch".format(name))

        # Create DB input
        # https://elasticsearch-py.readthedocs.io/en/master/helpers.html
        actions = []
        for c, p in zip(columns, points):
            action = {
                "_index": self.index,
                "_type": name,
                "_id": c,
                "_source": {
                    "value": str(p),
                    "timestamp": datetime.now()
                }
            }
            actions.append(action)

        # Write input to the ES index
        try:
            helpers.bulk(self.client, actions)
        except Exception as e:
            logger.error("Cannot export {} stats to ElasticSearch ({})".format(name, e))
