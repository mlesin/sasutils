#!/usr/bin/python
#
# Copyright (C) 2016
#      The Board of Trustees of the Leland Stanford Junior University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build a useful udev alias from a SAS (array) block device.

The alias is built from the associated enclosure nickname (must be set)
and the array device bay identifier.

Example of udev rule:

KERNEL=="sd*", PROGRAM="/usr/bin/sas_blkdev_snic_alias %k", SYMLINK+="%c"
"""

from __future__ import print_function
from subprocess import check_output
import re
import sys

from sasutils.sas import SASBlockDevice
from sasutils.sysfs import sysfs


ALIAS_FORMAT = '{nickname}-bay{bay_identifier}'


def sas_blkdev_snic_alias(blkdev):
    """Use sasutils library to get the alias name from the block device."""
    # Instantiate SASBlockDevice object from block device sysfs node
    #   eg. /sys/block/sdx/device
    blkdev = SASBlockDevice(sysfs.node('block').node(blkdev).node('device'))

    # Retrieve bay_identifier from matching sas_device
    bay = int(blkdev.end_device.sas_device.attrs.bay_identifier)

    # Use links to array_device and enclosure to retrieve the ses sg device
    ses_sg = blkdev.array_device.enclosure.scsi_generic.sg_devname

    # SES nickname is not available through sysfs, use sg_ses tool instead
    result = check_output(['sg_ses', '--page=snic', '-I0', '/dev/' + ses_sg])
    for line in result.splitlines():
        mobj = re.match(r'\s+nickname:\s*([^ ]+)', line)
        if mobj:
            return ALIAS_FORMAT.format(nickname=mobj.group(1),
                                       bay_identifier=bay)

def main():
    """Entry point for sas_blkdev_snic_alias command-line."""
    if len(sys.argv) != 2:
        print('Usage: %s <blkdev>' % sys.argv[0], file=sys.stderr)
        sys.exit(1)
    try:
        print(sas_blkdev_snic_alias(sys.argv[1]))
    except KeyError as err:
        print("Not found: {0}".format(err), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()