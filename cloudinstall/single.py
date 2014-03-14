#!/usr/bin/env python3
# -*- mode: python; -*-
#
# single.py - Single installer
#
# Copyright 2014 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This package is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
from cloudinstall import utils
from cloudinstall.utils import dns
from cloudinstall.provider import LXC
from cloudinstall.juju import configure_manual_provider

def main(args):
    """ Single installer entrypoint """
    admin_secret = utils.random_string(size=32)
    storage_auth_key = utils.random_string(size=32)
    # TODO: make this configurable
    num_nodes = 3

    if not utils.is_prepped():
        ret = utils.prep_install_dir()
        if not ret:
            print("Could not prep install directory")
            return 1

    ret = utils.install_pkgs(['cloud-install-single'])
    if not ret:
        print("Unable to install cloud-install-single package.")
        return 1

    ret = utils.gen_ssh_keys()
    if not ret:
        print("Could not generate ssh keys")
        return 1

    #ret = dns.configure_manual_dns()
    #if not ret:
        #print("Unable to configure dns")
        #return 1

    ret = configure_manual_provider(admin_secret, storage_auth_key)
    if not ret:
        print("Unable to render environments.yaml")
        return 1

    lxc = LXC('juju-bootstrap')
    lxc.create()
    lxc.start()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
