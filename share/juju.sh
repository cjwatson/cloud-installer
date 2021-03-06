#
# juju.sh - Shell routines for Juju
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

configMaasEnvironment()
{
	cat <<-EOF
		default: maas

		environments:
		  maas:
		    type: maas
		    maas-server: 'http://$1/MAAS/'
		    maas-oauth: '$2'
		    admin-secret: $3
		    default-series: trusty
		    authorized-keys-path: ~/.ssh/id_rsa.pub
		    apt-http-proxy: 'http://$1:8000/'
		    lxc-use-clone: true
		EOF
}

configLocalEnvironment()
{
	cat <<-EOF
		default: local

		environments:
		  local:
		    type: local
		    container: kvm
		    lxc-use-clone: true
		EOF
}

configCharmOptions()
{
	cat <<-EOF
                keystone:
                  admin-password: $1
                  admin-user: 'admin'
                juju-gui:
                  password: $1
                mysql:
                  dataset-size: 512M
                swift-proxy:
                  zone-assignment: auto
                  replicas: 3
                swift-storage:
                  zone: 1
                  block-device: /etc/swift/storage.img|2G
		EOF
}

configureJuju()
{
	env_type=$1
	shift

	if [ ! -e "/home/$INSTALL_USER/.juju" ]; then
		mkdir -m 0700 "/home/$INSTALL_USER/.juju"
		chown "$INSTALL_USER:$INSTALL_USER" "/home/$INSTALL_USER/.juju"
	fi
	(umask 0077; $env_type $@ > "/home/$INSTALL_USER/.juju/environments.yaml")
	chown "$INSTALL_USER:$INSTALL_USER" \
	    "/home/$INSTALL_USER/.juju/environments.yaml"
}

# TODO break this function into smaller ones
jujuBootstrap()
{
	cluster_uuid=$1

	lxc-create -n juju-bootstrap -t ubuntu-cloud -- -r trusty
	sed -e "s/^lxc.network.link.*$/lxc.network.link = br0/" -i \
	    /var/lib/lxc/juju-bootstrap/config
	printf "\n%s\n%s\n" "# Autostart on reboot" "lxc.start.auto = 1" \
	    >> /var/lib/lxc/juju-bootstrap/config

	# We need to allow nested LXCs in case people want to deploy --to lxc:0 (as
	# landscape-dense-maas does).
	printf "\n%s\n%s\n%s\n" "# Allow nested containers" "lxc.mount.auto = cgroup" \
	    "lxc.aa_profile = lxc-container-default-with-nesting" \
	    >> /var/lib/lxc/juju-bootstrap/config

	# lxc has to look like vanilla maas ubuntu for juju cloud-init script
	# to run
	rm /var/lib/lxc/juju-bootstrap/rootfs/etc/network/interfaces.d/eth0.cfg
	printf "%s\n%s\n" "auto eth0" "iface eth0 inet dhcp" \
	    >> /var/lib/lxc/juju-bootstrap/rootfs/etc/network/interfaces

	mac=$(grep lxc.network.hwaddr /var/lib/lxc/juju-bootstrap/config \
	    | cut -d " " -f 3)
	# TODO dynamic architecture selection
	maas maas nodes new architecture=amd64/generic mac_addresses=$mac \
	    hostname=juju-bootstrap nodegroup=$cluster_uuid power_type=virsh
	system_id=$(nodeSystemId $mac)
	wget -O $TMP/maas.creds \
	    "http://localhost/MAAS/metadata/latest/by-id/$system_id/?op=get_preseed"
	python2 /etc/maas/templates/commissioning-user-data/snippets/maas_signal.py \
	    --config $TMP/maas.creds OK || true

	(cd "/home/$INSTALL_USER"; sudo -H -u "$INSTALL_USER" juju --show-log sync-tools)
	(cd "/home/$INSTALL_USER"; sudo -H -u "$INSTALL_USER" juju bootstrap --upload-tools) &
	waitForNodeStatus $system_id 6
	rm -rf /var/lib/lxc/juju-bootstrap/rootfs/var/lib/cloud/seed/*
	cp $TMP/maas.creds \
	    /var/lib/lxc/juju-bootstrap/rootfs/etc/cloud/cloud.cfg.d/91_maas.cfg
	lxc-start -n juju-bootstrap -d
	wait $!
}
