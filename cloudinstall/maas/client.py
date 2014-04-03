#
# client.py - Client routines for MAAS API
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

import cloudinstall.maas
import cloudinstall.maas.auth
from requests_oauthlib import OAuth1
import requests
import json

from subprocess import check_call, CalledProcessError, DEVNULL


class Client:
    """ Client Class
    """

    def _oauth(self):
        """ Generates OAuth attributes for protected resources

        @return: OAuth class
        """
        oauth = OAuth1(self.auth.consumer_key,
                       client_secret=self.auth.consumer_secret,
                       resource_owner_key=self.auth.token_key,
                       resource_owner_secret=self.auth.token_secret,
                       signature_method='PLAINTEXT',
                       signature_type='query')
        return oauth

    @cloudinstall.maas.auth.authenticated
    def get(self, url, params=None):
        """ Performs a authenticated GET against a MAAS endpoint

        @param url: MAAS endpoint
        @param params: extra data sent with the HTTP request
        """
        return requests.get(url=self.auth.api_url + url,
                            auth=self._oauth(),
                            params=params)

    @cloudinstall.maas.auth.authenticated
    def post(self, url, params=None):
        """ Performs a authenticated POST against a MAAS endpoint

        @param url: MAAS endpoint
        @param params: extra data sent with the HTTP request
        """
        return requests.post(url=self.auth.api_url + url,
                             auth=self._oauth(),
                             data=params)

    @cloudinstall.maas.auth.authenticated
    def delete(self, url, params=None):
        """ Performs a authenticated DELETE against a MAAS endpoint

        @param url: MAAS endpoint
        @param params: extra data sent with the HTTP request
        """
        return requests.delete(url=self.auth.api_url + url,
                               auth=self._oauth())

    ###########################################################################
    # Node API
    ###########################################################################
    @property
    def nodes(self):
        """ Nodes managed by MAAS

        @return list: List of managed nodes
        """
        res = self.get('/nodes/', dict(op='list'))
        if res.ok:
            return json.loads(res.text)
        return []

    def nodes_accept_all(self):
        """ Accept all commissioned nodes

        @return: Status/Fail boolean
        res = self.post('/nodes/', dict(op='accept_all'))
        if res.ok:
            return True
        return False
        """
        try:
            check_call(['maas', 'maas', 'nodes', 'accept-all'])
        except CalledProcessError:
            pass

    def node_commission(self, system_id):
        """ (Re)commission a node

        @param system_id: machine identification
        @return: True on success False on failure
        """
        res = self.post('/nodes/%s' % (system_id,), dict(op='commission'))
        if res.ok:
            return True
        return False

    def node_start(self, system_id):
        """ Power up a node

        @param system_id: machine identification
        @return: True on success False on failure
        """
        res = self.post('/nodes/%s' % (system_id,), dict(op='start'))
        if res.ok:
            return True
        return False

    def node_stop(self, system_id):
        """ Shutdown a node

        @param system_id: machine identification
        @return: True on success False on failure
        """
        res = self.post('/nodes/%s' % (system_id,), dict(op='stop'))
        if res.ok:
            return True
        return False

    def node_remove(self, system_id):
        """ Delete a node

        @param system_id: machine identification
        @return: True and success False on failure
        """
        res = self.delete('/nodes/%s' % (system_id,))
        if res.ok:
            return True
        return False

    ###########################################################################
    # Tag API
    ###########################################################################
    @property
    def tags(self):
        """ List tags known to MAAS

        @return: List of tags or empty list
        """
        res = self.get('/tags/', dict(op='list'))
        if res.ok:
            return json.loads(res.text)
        return []

    def tag_new(self, tag):
        """ Create tag if it doesn't exist.

        @param tag: Tag name
        @return: Success/Fail boolean
        tags = {tagmd['name'] for tagmd in self.tags}
        if tag not in tags:
            res = self.post('/tags/', dict(op='new',name=tag))
            return res.ok
        return False
        """
        try:
            check_call(['maas', 'maas', 'tags',
                        'new', 'name=' + tag],
                       stdout=DEVNULL,
                       stderr=DEVNULL)
        except CalledProcessError:
            pass

    def tag_delete(self, tag):
        """ Delete a tag

        @param tag: tag id
        @return: True on success False on failure
        """
        res = self.delete('/tags/%s' % (tag,))
        if res.ok:
            return True
        return False

    def tag_machine(self, tag, system_id):
        """ Tag the machine with the specified tag.

        @param tag: Tag name
        @param system_id: ID of node
        @return: Success/Fail boolean
        res = self.post('/tags/%s/' % (tag,), dict(op='update_nodes',
                                                   add=system_id))
        if res.ok:
            return True
        return False
        """
        try:
            check_call(['maas', 'maas', 'tag', 'update-nodes',
                        tag, 'add=' + system_id],
                       stdout=DEVNULL,
                       stderr=DEVNULL)
        except CalledProcessError:
            pass

    def tag_name(self, maas):
        """ Tag each node as its hostname.

        This is a bit ugly. Since we want to be able to juju deploy to
        a particular node that the user has selected, we use juju's
        constraints support for maas. Unfortunately, juju didn't
        implement maas-name directly, we have to tag each node with
        its hostname for now so that we can pass that tag as a
        constraint to juju.

        @param maas: MAAS object representing all managed nodes
        """
        for machine in maas:
            tag = machine['system_id']
            if 'tag_names' not in machine or tag not in machine['tag_names']:
                self.tag_new(tag)
                self.tag_machine(tag, tag)

    def tag_fpi(self, maas):
        """ Tag each DECLARED host with the FPI tag.

        Also a little strange: we could define a tag with
        'definition=true()' and automatically tag each node. However,
        each time we un-tag a node, maas evaluates the xpath
        expression again and re-tags it. So, we do it once, manually,
        when the machine is in the DECLARED state (also to avoid
        re-tagging things that have already been tagged).

        @param maas: MAAS object representing all managed nodes
        """
        FPI_TAG = 'use-fastpath-installer'
        self.tag_new(FPI_TAG)
        for machine in maas:
            if machine['status'] == cloudinstall.maas.MaasState.DECLARED:
                self.tag_machine(FPI_TAG, machine['system_id'])

    ###########################################################################
    # Users API
    ###########################################################################
    @property
    def users(self):
        """ List users on MAAS

        @return: List of registered users or an empty list
        """
        res = self.get('/users/')
        if res.ok:
            return json.loads(res.text)
        return []

    ###########################################################################
    # Zone API
    ###########################################################################
    @property
    def zones(self):
        """ List physical zones

        @return: List of managed zones or empty list
        """
        res = self.get('/zones/')
        if res.ok:
            return json.loads(res.text)
        return []

    def zone_new(self, name, description="Zone created by API"):
        """ Create a physical zone

        @param name: Name of the zone
        @param description: Description of zone.
        @return: True on success False on failure
        """
        res = self.post('/zones/', dict(name=name,
                                        description=description))
        if res.ok:
            return True
        return False
