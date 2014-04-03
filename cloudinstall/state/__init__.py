#
# __init__.py - Provider state interface
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

import yaml
from io import StringIO
from collections import defaultdict


# - Juju State Representation -------------------------------------------------
class Juju:
    def __init__(self, raw_yaml=None):
        self._yaml = yaml.load(StringIO(raw_yaml))

    def id_for_machine_no(self, no):
        """ Returns instance-id of a machine

        @param no: Machine number
        @return: instance-id string
        """
        return self._yaml['machines'][no]['instance-id']

    def machine(self, id):
        for no, m in self._yaml['machines'].items():
            if m['instance-id'] == id:
                m['machine_no'] = no
                return m

    @property
    def services(self):
        """ Map of {servicename: nodecount}. """
        ret = {}
        for svc, contents in self._yaml.get('services', {}).items():
            ret[svc] = len(contents.get('units', []))
        return ret

    def _build_unit_map(self, compute_id, allow_id):
        """ Return a map of compute_id(unit): ([charm name], [unit name]),
        useful for defining maps between properties of units and what is
        deployed to them. """
        charms = defaultdict(lambda: ([], []))
        for name, service in self._yaml.get('services', {}).items():
            for unit_name, unit in service.get('units', {}).items():
                if 'machine' not in unit or not allow_id(str(unit['machine'])):
                    continue
                cs, us = charms[compute_id(unit)]
                cs.append(name)
                us.append(unit_name)
        return charms

    @property
    def assignments(self):
        """ Return a map of instance-id: ([charm name], [unit name]), useful
        for figuring out what is deployed where. Note that these are physical
        machines, and containers are not included. """
        def by_instance_id(unit):
            return self._yaml['machines'][unit['machine']]['instance-id']

        def not_lxc(id_):
            return 'lxc' not in id_
        return self._build_unit_map(by_instance_id, not_lxc)

    @property
    def containers(self):
        """ A map of container-id (e.g. "1/lxc/0") to ([charm name], [unit
        name]) """
        def by_machine_name(unit):
            return unit['machine']

        def is_lxc(id_):
            return 'lxc' in id_
        return self._build_unit_map(by_machine_name, allow_id=is_lxc)

    def container(self, machine, id_):
        lxc = "%s/lxc/%s" % (machine, id_)
        return self._yaml["machines"][machine]["containers"][lxc]


# - MAAS State Representation -------------------------------------------------
class Maas:
    DECLARED = 0
    COMMISSIONING = 1
    FAILED_TESTS = 2
    MISSING = 3
    READY = 4
    RESERVED = 5
    ALLOCATED = 6
    RETIRED = 7

    def __init__(self, data):
        self._maas = data

    def __iter__(self):
        return iter(self._maas)

    def hostname_for_instance_id(self, id):
        for machine in self:
            if machine['resource_uri'] == id:
                return machine['hostname']

    @property
    def machines(self):
        return len(self._maas)

    def num_in_state(self, state):
        return len(list(filter(lambda m: int(m["status"]) == state,
                               self._maas)))
