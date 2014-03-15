#
# juju/__init__.py - Juju utilies for cloud installer
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

import os
from cloudinstall import utils

def ensure_juju_dir():
    """ Makes sure our .juju directory exists """
    _juju_dir = os.path.join(utils.get_install_user()[1], '.juju')
    if not os.path.exists(_juju_dir):
        os.makedirs(_juju_dir)
    return

def configure_manual_provider(admin_secret, storage_auth_key):
    """ Creates necessary yaml file for a manual provider

    @param admin_secret: Administrator password for juju bootstrap
    @param storage_auth_key: storage key for bootstrap
    """
    ensure_juju_dir()
    out_file = os.path.join(utils.get_install_user()[1], '.juju/environments.yaml')
    out = utils.render('environments.yaml', juju_env='manual',
                       admin_secret=admin_secret,
                       storage_auth_key=storage_auth_key)
    with open(out_file, 'w') as f:
        f.write(out)
        return True
    return False

def configure_maas_provider(address, maas_creds, admin_secret):
    """ Creates maas environments.yaml

    @param address: address of maas server
    @param maas_creds: maas oauth credentials
    @param admin_secret: admin secret
    """
    ensure_juju_dir()
    out_file = os.path.join(utils.get_install_user()[1], '.juju/environments.yaml')
    out = utils.render('environments.yaml', juju_env='maas',
                                                 admin_secret=admin_secret,
                                                 maas_address=address,
                                                 maas_creds=maas_creds)
    with open(out_file, 'w') as f:
        f.write(out)
        return True
    return False
