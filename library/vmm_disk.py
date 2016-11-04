#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Jasper Lievisse Adriaanse <j@jasper.la>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

import os
import re
from pwd import getpwuid
from grp import getgrgid

DOCUMENTATION = '''
---
module: vmm_disk
short_description: Manage vmm disk images
description:
    - Manage disk images for use with vmm(4)
version_added: "2.3"
author: Jasper Lievisse Adriaanse (@jasper_la)
options:
    path:
        required: true
        description:
        - Absolute path to the disk image.
    state:
        required: true
        choices: [ present, absent ]
        description:
        - C(present) will make sure the image is created or present.
        - C(absent) will make sure the image is removed.
    size:
        required: false
        description:
        - Define the size for the image. It is only applied when creating
         the image. Once the image has been created the size cannot be
         changed anymore. Images need to be at least 1MB. Use the format
         described in C(fmt_scaled(3)), e.g. 1G, 4.5T, etc.
    owner:
        required: false
        default: _vmd
        description:
        - Change the ownership of the on-disk image.
    group:
        required: false
        default: _vmd
        description:
        - Change the group ownership of the on-disk image.
'''

EXAMPLES = '''
# Create a 4.5G image
- vmm_disk: path=/vms/web.img state=present size="4.5G"

# Remove an image
- vmm_disk: path=/vms/web.img state=absent
'''

def vmm_disk_create(module, path, size, owner, group):
    rc = 0
    stdout = stderr = ''
    changed = False

    # First check if the image already exists.
    if not os.access(path, os.F_OK):
        vmctl_cmd = "vmctl create %s -s %s" % (path, size)
        (rc, stdout, stderr) = module.run_command(vmctl_cmd)

        if rc == 0:
            changed = True
        else:
            changed = False

    changed = module.set_owner_if_different(path, owner, changed)
    changed = module.set_group_if_different(path, group, changed)

    return (rc, stdout, stderr, changed)

# Try to emove the disk image, if it doesn't exist then os.unlink()
# will fail, we catch the exception and report that nothing has changed.
def vmm_disk_remove(path):
    try:
        os.unlink(path)
	return (0, '', True)
    except OSError, e:
        # File not present, so nothing changed.
    	if re.match('.*No such file or directory:.*', str(e)):
            return (0, '', False)
        else:
            return (1, "Failed to remove %s: %s" % (path, str(e)), False)

def main():
    module = AnsibleModule(
	argument_spec = dict(
            path  = dict(required=True),
            state = dict(required=True, choices=['absent', 'removed', 'present', 'created']),
            size  = dict(default=None),
            owner = dict(default='_vmd'),
            group = dict(default='_vmd')
        )
    )

    path  = module.params['path']
    state = module.params['state']
    size  = module.params['size']
    owner = module.params['owner']
    group = module.params['group']

    rc = 0
    stdout = stderr = ''
    result = { 'path': path }

    # Let's check upfront the required binaries are present. If they're
    # missing we're either not on OpenBSD or the release is too old.
    for v in ['vmd', 'vmctl']:
        if not os.access(os.path.join('/usr/sbin', v), os.X_OK):
            module.fail_json(msg="Could not find %s, unable to continue" % (b))

    # Ensure the image path is specified as an absolute path.
    if not os.path.isabs(path):
        module.fail_json(msg="main(): image path must be absolute for %s" % (path))

    # Now perform the actual creation/removal
    if state in ['absent', 'removed']:
        (rc, stderr, changed) = vmm_disk_remove(path)
    elif state in ['present', 'created']:
	# Perform input validation on size to ensure it adheres to what
    	# fmt_scaled(3) can handle.
    	match = re.match('\d+(\.?\d*)(B|K|M|G|T|P|E)$', size)
    	if not match:
        	module.fail_json(msg="main(): invalid image size specified: %s for %s" % (size, path))
        (rc, stdout, stderr, changed) = vmm_disk_create(module, path, size, owner, group)

    if rc != 0:
        if stderr:
            module.fail_json(msg=stderr)
        else:
            module.fail_json(msg=stdout)

    result['changed'] = changed

    module.exit_json(**result)

# Import module snippets.
from ansible.module_utils.basic import *
main()
