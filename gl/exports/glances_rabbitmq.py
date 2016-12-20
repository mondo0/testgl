# -*- coding: utf-8 -*-


"""JMS interface class."""

import datetime
import socket
import sys
from numbers import Number

from gl.compat import NoOptionError, NoSectionError, range
from gl.logger import logger
from gl.exports.glances_export import GlancesExport

# Import pika for RabbitMQ
import pika


class Export(GlancesExport):

    """This class manages the rabbitMQ export module."""

    def __init__(self, config=None, args=None):
        """Init the RabbitMQ export IF."""
        super(Export, self).__init__(config=config, args=args)

        # Load the rabbitMQ configuration file
        self.rabbitmq_host = None
        self.rabbitmq_port = None
        self.rabbitmq_user = None
        self.rabbitmq_password = None
        self.rabbitmq_queue = None
        self.hostname = socket.gethostname()
        self.export_enable = self.load_conf()
        if not self.export_enable:
            sys.exit(2)

        # Init the rabbitmq client
        self.client = self.init()

    def load_conf(self, section="rabbitmq"):
        """Load the rabbitmq configuration in the Glances configuration file."""
        if self.config is None:
            return False
        try:
            self.rabbitmq_host = self.config.get_value(section, 'host')
            self.rabbitmq_port = self.config.get_value(section, 'port')
            self.rabbitmq_user = self.config.get_value(section, 'user')
            self.rabbitmq_password = self.config.get_value(section, 'password')
            self.rabbitmq_queue = self.config.get_value(section, 'queue')
        except NoSectionError:
            logger.critical("No rabbitmq configuration found")
            return False
        except NoOptionError as e:
            logger.critical("Error in the RabbitM configuration (%s)" % e)
            return False
        else:
            logger.debug("Load RabbitMQ from the Glances configuration file")
        return True

    def init(self):
        """Init the connection to the rabbitmq server."""
        if not self.export_enable:
            return None
        try:
            parameters = pika.URLParameters(
                'amqp://' + self.rabbitmq_user +
                ':' + self.rabbitmq_password +
                '@' + self.rabbitmq_host +
                ':' + self.rabbitmq_port + '/')
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            return channel
        except Exception as e:
            logger.critical("Connection to rabbitMQ failed : %s " % e)
            return None

    def export(self, name, columns, points):
        """Write the points in RabbitMQ."""
        data = ('hostname=' + self.hostname + ', name=' + name +
                ', dateinfo=' + datetime.datetime.utcnow().isoformat())
        for i in range(len(columns)):
            if not isinstance(points[i], Number):
                continue
            else:
                data += ", " + columns[i] + "=" + str(points[i])
        logger.debug(data)
        try:
            self.client.basic_publish(exchange='', routing_key=self.rabbitmq_queue, body=data)
        except Exception as e:
            logger.error("Can not export stats to RabbitMQ (%s)" % e)
