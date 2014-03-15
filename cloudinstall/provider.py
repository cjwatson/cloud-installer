#
# node.py - Node manage interface for cloud installer
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

import lxc
import uuid

class LXC(object):
    def __init__(self, name=uuid.uuid1(), arch="amd64"):
        self.name = name
        self.arch = arch
        self.container = lxc.Container(self.name)

    def create(self):
        """ Create lxc container """
        self.container.create("ubuntu-cloud", 0,
                              {'release': "trusty",
                               'arch': self.arch})

    @property
    def list(self):
        self.container.list_containers()

    def destroy(self):
        self.container.destroy()

    def clone(self, name=uuid.uuid1()):
        return self.container.clone(name)

    def start(self):
        self.container.start()
