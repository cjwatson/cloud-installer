#!/usr/bin/env python3
#
# test_lxc.py - LXC Api Tests
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

import unittest
import os
from pprint import pprint
import sys
sys.path.insert(0, '../cloudinstall')

from cloudinstall.node import LXC

class LXCApiTest(unittest.TestCase):
    def setUp(self):
        self.node = LXC('juju-bootstrap')

    def tearDown(self):
        self.node.destroy()

    def test_create(self):
        self.node.create()
        self.assertTrue('juju-bootstrap' in self.node.name)

if __name__ == '__main__':
    unittest.main()
