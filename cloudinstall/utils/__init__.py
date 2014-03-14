#
# utils/__init__.py - Helper utilies for cloud installer
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

from subprocess import Popen, PIPE, DEVNULL, call, STDOUT
from contextlib import contextmanager
import os
import re
import string
import random
import pwd
import tempita

# String with number of minutes, or None.
blank_len = None


def get_install_user():
    """ Query install user for ID

    @return: (user name, user home directory)
    """
    _user = pwd.getpwuid(1000)
    return (_user.pw_name, _user.pw_dir)

def get_share_dir():
    """ Returns share data dir """
    return "/usr/share/cloud-installer"

def get_command_output(command, timeout=300):
    """ Execute command through system shell

    @return: returncode, stdout, 0
    """
    cmd_env = os.environ.copy()
    # set consistent locale
    cmd_env['LC_ALL'] = 'C'
    if timeout:
        command = "timeout %ds %s" % (timeout, command)

    p = Popen(command, shell=True,
              stdout=PIPE, stderr=STDOUT,
              bufsize=-1, env=cmd_env, close_fds=True)
    stdout, stderr = p.communicate()
    return (p.returncode, stdout.decode('utf-8'), 0)

def run_command(command, timeout=300):
    """ Execute command through system shell

    @return: returncode
    """
    cmd_env = os.environ.copy()
    # set consistent locale
    cmd_env['LC_ALL'] = 'C'
    if timeout:
        command = "timeout %ds %s" % (timeout, command)

    p = Popen(command, shell=True,
              stdout=DEVNULL, stderr=DEVNULL,
              bufsize=-1, env=cmd_env, close_fds=True)
    return p.returncode


def get_network_interface(iface):
    """ Get network interface properties

    @param iface: Interface to query (ex. eth0)
    @return: dict of interface properties or None if no properties
    """
    (status, output, runtime) = get_command_output('ifconfig %s' % (iface,))
    line = output.split('\n')[1:2][0].lstrip()
    regex = re.compile('^inet addr:([0-9]+(?:\.[0-9]+){3})\s+Bcast:([0-9]+(?:\.[0-9]+){3})\s+Mask:([0-9]+(?:\.[0-9]+){3})')
    match = re.match(regex, line)
    if match:
        return {'address': match.group(1),
                'broadcast': match.group(2),
                'netmask': match.group(3)}
    return None


def get_network_interfaces():
    """ Get network interfaces

    @return: list of available interfaces and their properties
    """
    interfaces = []
    (status, output, runtime) = get_command_output('ifconfig -s')
    _ifconfig = output.split('\n')[1:-1]
    for i in _ifconfig:
        name = i.split(' ')[0]
        if 'lo' not in name:
            interfaces.append({name: get_network_interface(name)})
    return interfaces


def get_install_dir():
    """ Returns install dir path"""
    return os.path.join(get_install_user()[1], ".cloud-install")

def gen_ssh_keys():
    """ Generate ssh keys

    @return: True on success False on failure
    """
    (user, home) = get_install_user()
    ssh_path = os.path.join(home, '.ssh/id_rsa')
    ret = run_command("sudo -u %s ssh-keygen -N '' -f %s" % (user, ssh_path))
    if ret:
        return False
    return True

def prep_install_dir():
    """ Preps the cloud-install directory

    """
    _path = get_install_dir()
    if not os.path.exists(_path):
        os.makedirs(_path)

def is_prepped():
    """ Test for install directory """
    return os.path.exists(get_install_dir())

def install_pkgs(pkgs=[]):
    """ Install pkgs

    @param pkgs: List of packages to install
    """
    ret = run_command("DEBIAN_FRONTEND=noninteractive apt-get install -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' -f -q -y %s </dev/null" % (' '.join(pkgs),))
    if ret:
        return False
    return True

def set_openstack_password():
    """ Sets initial openstack password

    @return: True on write False on failed to write
    """
    if is_prepped():
        with open(os.path.join(get_install_dir(), 'openstack.passwd'), 'w') as f:
            f.write(random_string())
            return True
    return False

def partition(pred, iterable):
    yes, no = [], []
    for i in iterable:
        (yes if pred(i) else no).append(i)
    return (yes, no)


def reset_blanking():
    global blank_len
    if blank_len is not None:
        call(('setterm', '-blank', blank_len))


@contextmanager
def console_blank():
    global blank_len
    try:
        with open('/sys/module/kernel/parameters/consoleblank') as f:
            blank_len = f.read()
    except (IOError, FileNotFoundError):
        blank_len = None
    else:
        # Cannot use anything that captures stdout, because it is needed
        # by the setterm command to write to the console.
        call(('setterm', '-blank', '0'))
        # Convert the interval from seconds to minutes.
        blank_len = str(int(blank_len)//60)

    yield

    reset_blanking()


def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    """ Generate a random string

    @param size: number of string characters
    @param chars: range of characters (optional)
    @return: a random string
    """
    return ''.join(random.choice(chars) for x in range(size))


def render(tmpl, data):
    """ processes a template file with substitution

    @param tmpl: path to template file
    @param data: variables to substitute in template
    """
    _tmpl = tempita.Template.from_filename(tmpl, data)
    return _tmpl.substitute()
