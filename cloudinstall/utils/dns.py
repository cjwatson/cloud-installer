#
# utils/dns.py - DNS Helper utilies for cloud installer
#
# Copyright 2014 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from cloudinstall import utils

def configure_manual_dns():
    """ Sets the dns configuration
    """
    ret = utils.run_command('cp /etc/resolv.conf /etc/resolv.dnsmasq')
    if ret:
        print("Could not copy resolv.conf")
        return False

    with open('/etc/lxc/dnsmasq.conf', 'w') as f:
        f.write('resolv-file=/etc/resolv.dnsmasq')

    with open('/etc/default/lxc-net', 'w') as f:
        f.write('LXC_DHCP_CONFILE=/etc/lxc/dnsmasq.conf')

    ret = utils.run_command('service lxc-net restart')
    if ret:
        print("Could not restart lxc-net service")
        return False

    with open('/etc/network/interfaces', 'r') as f:
        _tmp = f.readlines()
        #sed -e '/^iface lo inet loopback$/a\
        #\ dns-nameservers 10.0.3.1' -i /etc/network/interfaces

    ret = utils.run_command('ifdown lo; ifup lo')
    if ret:
        print("Could not turn off/on lo")
        return False

    return True
