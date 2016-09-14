# Copyright 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from io import open
import os

from oslo_log import log as logging

from fuel_agent import errors
from fuel_agent.utils import utils

LOG = logging.getLogger(__name__)


def udev_nic_naming_rules(chroot, udevrules):
    """Generates NIC naming rules for udev.

    Expected string formatting: "(macaddrX)_(nicX)" comma separated.
    Eg.: "08:00:27:79:da:80_eth0,08:00:27:46:43:60_eth1"
    """
    # FIXME(agordeev) There's no convenient way to perfrom NIC
    # remapping in Ubuntu, so injecting files prior the first boot
    # should work
    with open(chroot + '/etc/udev/rules.d/70-persistent-net.rules',
              'wt', encoding='utf-8') as f:
        f.write(u'# Generated by fuel-agent during provisioning: '
                u'BEGIN\n')
        # pattern is aa:bb:cc:dd:ee:ff_eth0,aa:bb:cc:dd:ee:ff_eth1
        for mapping in udevrules.split(','):
            mac_addr, nic_name = mapping.split('_')
            f.write(u'SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", '
                    u'ATTR{address}=="%s", ATTR{type}=="1", '
                    u'KERNEL=="eth*", NAME="%s"\n' % (mac_addr,
                                                      nic_name))
        f.write(
            u'# Generated by fuel-agent during provisioning: END\n')
    # FIXME(agordeev): Disable net-generator that will add new entries
    # to 70-persistent-net.rules
    with open(chroot + '/etc/udev/rules.d/'
                       '75-persistent-net-generator.rules', 'wt',
              encoding='utf-8') as f:
        f.write(u'# Generated by fuel-agent during provisioning:\n'
                u'# DO NOT DELETE. It is needed to disable '
                u'net-generator\n')


def configure_admin_nic(chroot, iface, ip, netmask, gw):
    debian_conf = '/etc/network/interfaces'
    redhat_conf = '/etc/sysconfig/network-scripts'
    if os.path.exists(chroot + debian_conf):
        configure_admin_nic_ubuntu(chroot, iface, ip, netmask, gw)
    elif os.path.exists(chroot + redhat_conf):
        configure_admin_nic_centos(chroot, iface, ip, netmask, gw)
    else:
        raise errors.UnsupportedNetworkConfiguration(
            "Can't find suitable configuration files for admin NIC")


def configure_admin_nic_ubuntu(chroot, iface, ip, netmask, gw):
    ifaces_dir = '/etc/network/interfaces.d'
    ifcfg_path = os.path.join(ifaces_dir, 'ifcfg-{0}'.format(iface))
    utils.makedirs_if_not_exists(ifaces_dir)
    with open(chroot + '/etc/network/interfaces', 'wt', encoding='utf-8') as f:
        f.write(u'# Generated by fuel-agent during provisioning:\n'
                u'source-directory /etc/network/interfaces.d\n')
    with open(chroot + ifcfg_path, 'wt', encoding='utf-8') as f:
        f.write(u'# Generated by fuel-agent during provisioning:\n'
                u'auto {iface}\n'
                u'iface {iface} inet static\n'
                u'\taddress {ip}\n'
                u'\tnetmask {netmask}\n'
                u'\tgateway {gw}\n'.format(iface=iface,
                                           ip=ip,
                                           netmask=netmask,
                                           gw=gw))


def configure_admin_nic_centos(chroot, iface, ip, netmask, gw):
    ifcfg_path = '/etc/sysconfig/network-scripts/ifcfg-{0}'.format(iface)
    with open(chroot + ifcfg_path, 'wt', encoding='utf-8') as f:
        f.write(u'# Generated by fuel-agent during provisioning:\n'
                u'DEVICE={iface}\n'
                u'IPADDR={ip}\n'
                u'NETMASK={netmask}\n'
                u'BOOTPROTO=none\n'
                u'ONBOOT=yes\n'
                u'USERCTL=no\n'.format(iface=iface, ip=ip, netmask=netmask))
    with open(chroot + '/etc/sysconfig/network', 'at', encoding='utf-8') as f:
        f.write(u'GATEWAY="{gw}"\n'.format(gw=gw))
