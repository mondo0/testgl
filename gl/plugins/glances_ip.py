# -*- coding: utf-8 -*-


"""IP plugin."""

import threading
from json import loads

from gl.compat import iterkeys, urlopen, URLError, queue
from gl.logger import logger
from gl.timer import Timer
from gl.plugins.glances_plugin import GlancesPlugin

# Also used in the ports_list script
try:
    import netifaces
    netifaces_tag = True
except ImportError:
    netifaces_tag = False

# List of online services to retreive public IP address
# List of tuple (url, json, key)
# - url: URL of the Web site
# - json: service return a JSON (True) or string (False)
# - key: key of the IP addresse in the JSON structure
urls = [('http://ip.42.pl/raw', False, None),
        ('http://httpbin.org/ip', True, 'origin'),
        ('http://jsonip.com', True, 'ip'),
        ('https://api.ipify.org/?format=json', True, 'ip')]


class Plugin(GlancesPlugin):

    """Glances IP Plugin.

    stats is a dict
    """

    def __init__(self, args=None):
        """Init the plugin."""
        super(Plugin, self).__init__(args=args)

        # We want to display the stat in the curse interface
        self.display_curse = True

        # Get the public IP address once
        self.public_address = PublicIpAddress().get()

        # Init the stats
        self.reset()

    def reset(self):
        """Reset/init the stats."""
        self.stats = {}

    @GlancesPlugin._log_result_decorator
    def update(self):
        """Update IP stats using the input method.

        Stats is dict
        """
        # Reset stats
        self.reset()

        if self.input_method == 'local' and netifaces_tag:
            # Update stats using the netifaces lib
            try:
                default_gw = netifaces.gateways()['default'][netifaces.AF_INET]
            except (KeyError, AttributeError) as e:
                logger.debug("Cannot grab the default gateway ({})".format(e))
            else:
                try:
                    self.stats['address'] = netifaces.ifaddresses(default_gw[1])[netifaces.AF_INET][0]['addr']
                    self.stats['mask'] = netifaces.ifaddresses(default_gw[1])[netifaces.AF_INET][0]['netmask']
                    self.stats['mask_cidr'] = self.ip_to_cidr(self.stats['mask'])
                    self.stats['gateway'] = netifaces.gateways()['default'][netifaces.AF_INET][0]
                    # !!! SHOULD be done once, not on each refresh
                    self.stats['public_address'] = self.public_address
                except (KeyError, AttributeError) as e:
                    logger.debug("Cannot grab IP information: {}".format(e))
        elif self.input_method == 'snmp':
            # Not implemented yet
            pass

        # Update the view
        self.update_views()

        return self.stats

    def update_views(self):
        """Update stats views."""
        # Call the father's method
        super(Plugin, self).update_views()

        # Add specifics informations
        # Optional
        for key in iterkeys(self.stats):
            self.views[key]['optional'] = True

    def msg_curse(self, args=None):
        """Return the dict to display in the curse interface."""
        # Init the return message
        ret = []

        # Only process if stats exist and display plugin enable...
        if not self.stats or args.disable_ip:
            return ret

        # Build the string message
        msg = ' - '
        ret.append(self.curse_add_line(msg))
        msg = 'IP '
        ret.append(self.curse_add_line(msg, 'TITLE'))
        msg = '{}'.format(self.stats['address'])
        ret.append(self.curse_add_line(msg))
        if 'mask_cidr' in self.stats:
            # VPN with no internet access (issue #842)
            msg = '/{}'.format(self.stats['mask_cidr'])
            ret.append(self.curse_add_line(msg))
        try:
            msg_pub = '{}'.format(self.stats['public_address'])
        except UnicodeEncodeError:
            pass
        else:
            if self.stats['public_address'] is not None:
                msg = ' Pub '
                ret.append(self.curse_add_line(msg, 'TITLE'))
                ret.append(self.curse_add_line(msg_pub))

        return ret

    @staticmethod
    def ip_to_cidr(ip):
        """Convert IP address to CIDR.

        Example: '255.255.255.0' will return 24
        """
        return sum([int(x) << 8 for x in ip.split('.')]) // 8128


class PublicIpAddress(object):
    """Get public IP address from online services"""

    def __init__(self, timeout=2):
        self.timeout = timeout

    def get(self):
        """Get the first public IP address returned by one of the online services"""
        q = queue.Queue()

        for u, j, k in urls:
            t = threading.Thread(target=self._get_ip_public, args=(q, u, j, k))
            t.daemon = True
            t.start()

        t = Timer(self.timeout)
        ip = None
        while not t.finished() and ip is None:
            if q.qsize() > 0:
                ip = q.get()

        return ip

    def _get_ip_public(self, queue_target, url, json=False, key=None):
        """Request the url service and put the result in the queue_target"""
        try:
            response = urlopen(url, timeout=self.timeout).read().decode('utf-8')
        except Exception as e:
            logger.debug("IP plugin - Can not open URL {0} ({1})".format(url, e))
            queue_target.put(None)
        else:
            # Request depend on service
            try:
                if not json:
                    queue_target.put(response)
                else:
                    queue_target.put(loads(response)[key])
            except ValueError:
                queue_target.put(None)
