# -*- coding: utf-8 -*-


"""Glances main class."""

import argparse
import os
import sys
import tempfile

from gl import __appname__, __version__, psutil_version
from gl.config import Config
from gl.globals import LINUX
from gl.logger import logger


class GlMain(object):

    """Main class to manage Glances instance."""

    # Default stats' refresh time is 3 seconds
    refresh_time = 3

    # Set the default cache lifetime to 1 second (only for server)
    # !!! Todo: To be configurable (=> https://github.com/nicolargo/glances/issues/901)
    cached_time = 1
    # By default, Glances is ran in standalone mode (no client/server)

    # Exemple of use
    example_of_use = "\
Examples of use:\n\
\n\
Monitor local machine:\n\
  $ gl\n\
\n\
Monitor local machine and export stats to a CSV file:\n\
  $ gl --export-csv\n\
    "

    def __init__(self):
        """Manage the command line arguments."""
        self.args = self.parse_args()

    def init_args(self):
        """Init all the command line arguments."""
        version = "gl v" + __version__ + " with psutil v" + psutil_version
        parser = argparse.ArgumentParser(
            prog=__appname__,
            conflict_handler='resolve',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self.example_of_use)
        parser.add_argument(
            '-V', '--version', action='version', version=version)
        parser.add_argument('-d', '--debug', action='store_true', default=False,
                            dest='debug', help='enable debug mode')
        parser.add_argument('-C', '--config', dest='conf_file',
                            help='path to the configuration file')
        # Enable or disable option on startup
        parser.add_argument('-3', '--disable-quicklook', action='store_true', default=False,
                            dest='disable_quicklook', help='disable quick look module')
        parser.add_argument('-4', '--full-quicklook', action='store_true', default=False,
                            dest='full_quicklook', help='disable all but quick look and load')
        parser.add_argument('--disable-cpu', action='store_true', default=False,
                            dest='disable_cpu', help='disable CPU module')
        parser.add_argument('--disable-mem', action='store_true', default=False,
                            dest='disable_mem', help='disable memory module')
        parser.add_argument('--disable-swap', action='store_true', default=False,
                            dest='disable_swap', help='disable swap module')
        parser.add_argument('--disable-load', action='store_true', default=False,
                            dest='disable_load', help='disable load module')
        parser.add_argument('--disable-network', action='store_true', default=False,
                            dest='disable_network', help='disable network module')
        parser.add_argument('--disable-ports', action='store_true', default=False,
                            dest='disable_ports', help='disable ports scanner module')
        parser.add_argument('--disable-ip', action='store_true', default=False,
                            dest='disable_ip', help='disable IP module')
        parser.add_argument('--disable-diskio', action='store_true', default=False,
                            dest='disable_diskio', help='disable disk I/O module')
        parser.add_argument('--disable-irq', action='store_true', default=False,
                            dest='disable_irq', help='disable IRQ module'),
        parser.add_argument('--disable-fs', action='store_true', default=False,
                            dest='disable_fs', help='disable filesystem module')
        parser.add_argument('--disable-folder', action='store_true', default=False,
                            dest='disable_folder', help='disable folder module')
        parser.add_argument('--disable-sensors', action='store_true', default=False,
                            dest='disable_sensors', help='disable sensors module')
        parser.add_argument('--disable-hddtemp', action='store_true', default=False,
                            dest='disable_hddtemp', help='disable HD temperature module')
        parser.add_argument('--disable-raid', action='store_true', default=False,
                            dest='disable_raid', help='disable RAID module')
        parser.add_argument('--disable-docker', action='store_true', default=False,
                            dest='disable_docker', help='disable Docker module')
        parser.add_argument('-5', '--disable-top', action='store_true',
                            default=False, dest='disable_top',
                            help='disable top menu (QL, CPU, MEM, SWAP and LOAD)')
        parser.add_argument('-2', '--disable-left-sidebar', action='store_true',
                            default=False, dest='disable_left_sidebar',
                            help='disable network, disk I/O, FS and sensors modules')
        parser.add_argument('--disable-process', action='store_true', default=False,
                            dest='disable_process', help='disable process module')
        parser.add_argument('--disable-amps', action='store_true', default=False,
                            dest='disable_amps', help='disable applications monitoring process (AMP) module')
        parser.add_argument('--disable-log', action='store_true', default=False,
                            dest='disable_log', help='disable log module')
        parser.add_argument('--disable-history', action='store_true', default=False,
                            dest='disable_history', help='disable stats history')
        parser.add_argument('--disable-bold', action='store_true', default=False,
                            dest='disable_bold', help='disable bold mode in the terminal')
        parser.add_argument('--disable-bg', action='store_true', default=False,
                            dest='disable_bg', help='disable background colors in the terminal')
        parser.add_argument('--enable-process-extended', action='store_true', default=False,
                            dest='enable_process_extended', help='enable extended stats on top process')
        # Export modules feature
        parser.add_argument('--export-graph', action='store_true', default=None,
                            dest='export_graph', help='export stats to graphs')
        parser.add_argument('--path-graph', default=tempfile.gettempdir(),
                            dest='path_graph', help='set the export path for graphs (default is {0})'.format(tempfile.gettempdir()))
        parser.add_argument('--export-csv', default=None,
                            dest='export_csv', help='export stats to a CSV file')
        parser.add_argument('--export-influxdb', action='store_true', default=False,
                            dest='export_influxdb', help='export stats to an InfluxDB server (influxdb lib needed)')
        parser.add_argument('--export-cassandra', action='store_true', default=False,
                            dest='export_cassandra', help='export stats to a Cassandra or Scylla server (cassandra lib needed)')
        parser.add_argument('--export-opentsdb', action='store_true', default=False,
                            dest='export_opentsdb', help='export stats to an OpenTSDB server (potsdb lib needed)')
        parser.add_argument('--export-statsd', action='store_true', default=False,
                            dest='export_statsd', help='export stats to a StatsD server (statsd lib needed)')
        parser.add_argument('--export-elasticsearch', action='store_true', default=False,
                            dest='export_elasticsearch', help='export stats to an ElasticSearch server (elasticsearch lib needed)')
        parser.add_argument('--export-rabbitmq', action='store_true', default=False,
                            dest='export_rabbitmq', help='export stats to rabbitmq broker (pika lib needed)')
        parser.add_argument('--export-riemann', action='store_true', default=False,
                            dest='export_riemann', help='export stats to riemann broker (bernhard lib needed)')
        # Display options
        parser.add_argument('-q', '--quiet', default=False, action='store_true',
                            dest='quiet', help='do not display the curses interface')
        parser.add_argument('-f', '--process-filter', default=None, type=str,
                            dest='process_filter', help='set the process filter pattern (regular expression)')
        parser.add_argument('--process-short-name', action='store_true', default=False,
                            dest='process_short_name', help='force short name for processes name')
        parser.add_argument('-0', '--disable-irix', action='store_true', default=False,
                            dest='disable_irix', help='task\'s cpu usage will be divided by the total number of CPUs')
        parser.add_argument('--hide-kernel-threads', action='store_true', default=False,
                            dest='no_kernel_threads', help='hide kernel threads in process list')
        if LINUX:
            parser.add_argument('--tree', action='store_true', default=False,
                                dest='process_tree', help='display processes as a tree')
        parser.add_argument('-b', '--byte', action='store_true', default=False,
                            dest='byte', help='display network rate in byte per second')
        parser.add_argument('--diskio-show-ramfs', action='store_true', default=False,
                            dest='diskio_show_ramfs', help='show RAM Fs in the DiskIO plugin')
        parser.add_argument('--diskio-iops', action='store_true', default=False,
                            dest='diskio_iops', help='show IO per second in the DiskIO plugin')
        parser.add_argument('--fahrenheit', action='store_true', default=False,
                            dest='fahrenheit', help='display temperature in Fahrenheit (default is Celsius)')
        parser.add_argument('-1', '--percpu', action='store_true', default=False,
                            dest='percpu', help='start Glances in per CPU mode')
        parser.add_argument('--fs-free-space', action='store_true', default=False,
                            dest='fs_free_space', help='display FS free space instead of used')
        parser.add_argument('--theme-white', action='store_true', default=False,
                            dest='theme_white', help='optimize display colors for white background')
        parser.add_argument('-t', '--time', default=self.refresh_time, type=float,
                            dest='time', help='set refresh time in seconds [default: {} sec]'.format(self.refresh_time))
        # Globals options
        parser.add_argument('--disable-check-update', action='store_true', default=False,
                            dest='disable_check_update', help='disable online Glances version ckeck')
        return parser

    def parse_args(self):
        """Parse command line arguments."""
        args = self.init_args().parse_args()

        # Load the configuration file, if it exists
        self.config = Config(args.conf_file)

        # Debug mode
        if args.debug:
            from logging import DEBUG
            logger.setLevel(DEBUG)

        # By default help is hidden
        args.help_tag = False

        # Display Rx and Tx, not the sum for the network
        args.network_sum = False
        args.network_cumul = False

        # Manage full quicklook option
        if args.full_quicklook:
            logger.info("Disable QuickLook menu")
            args.disable_quicklook = False
            args.disable_cpu = True
            args.disable_mem = True
            args.disable_swap = True
            args.disable_load = False

        # Manage disable_top option
        if args.disable_top:
            logger.info("Disable top menu")
            args.disable_quicklook = True
            args.disable_cpu = True
            args.disable_mem = True
            args.disable_swap = True
            args.disable_load = True

        # Control parameter and exit if it is not OK
        self.args = args


        # Check graph output path
        if args.export_graph and args.path_graph is not None:
            if not os.access(args.path_graph, os.W_OK):
                logger.critical("Graphs output path {0} do not exist or is not writable".format(args.path_graph))
                sys.exit(2)
            logger.debug("Graphs output path is set to {0}".format(args.path_graph))

        # For export graph, history is mandatory
        if args.export_graph and args.disable_history:
            logger.critical("Can not export graph if history is disabled")
            sys.exit(2)

        # Disable HDDTemp if sensors are disabled
        if args.disable_sensors:
            args.disable_hddtemp = True
            logger.debug("Sensors and HDDTemp are disabled")

        return args

    def get_config(self):
        """Return configuration file object."""
        return self.config

    def get_args(self):
        """Return the arguments."""
        return self.args
