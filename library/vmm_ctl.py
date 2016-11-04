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


DOCUMENTATION = '''
---
module: vmm_ctl
short_description: Manage vmd(8) with vmctl(8).
description:
    - Manage vmd(8) on OpenBSD. Individual VMs can be managed with C(vmm_vm).
version_added: "2.3"
author: Jasper Lievisse Adriaanse (@jasper_la)
...
'''

EXAMPLES = '''
# Reload vmd(8) configuration from disk
- vm_ctl: state=reloaded

# Load a specific configuration from disk
- vm_ctl: path=/path/to/config state=loaded

# Reset all VMs and switches
vm_ctl: state=reset target=all

# Reset only VMs
vm_ctl: state=reset target=vms

# Reset only switches
vm_ctl: state=reset target=switches
'''

# Reload the vmd(8) in-memory configuration.
# By definition this returns changed=True.
def vmm_ctl_reload(module):
    (rc, stdout, stderr) = module.run_command('vmctl reload')
    return (rc, stdout, stderr, True)

# Load a configuration from the specified path. vmctl(8) currently
# has no way of reporting an error in case of an invalid config file,
# so test it first directly with vmd(8).
# By definition loading a valid config returns changed=True.
def vmm_ctl_load(module, path):
    if not os.access(path, os.F_OK):
        module.fail_json(msg="Configuration file %s does not exist" % (path))

    # Let's see if vmd(8) will accept the new config.
    (rc, stdout, stderr) = module.run_command("vmd -n -f %s" % (path))
    if rc != 0:
        module.fail_json(msg="Invalid configuration file %s: %s" % (path, stderr))

    (rc, stdout, stderr) = module.run_command("vmctl load %s" % (path))
    return (1, stdout, stderr, True)

def vmm_ctl_reset(module, target):
    (rc, stdout, stderr) = module.run_command("vmctl reset %s" % (target))
    return (rc, stdout, stderr, True)

def main():
    module = AnsibleModule(
	argument_spec = dict(
            state  = dict(required=True, choices=['reloaded', 'loaded', 'reset']),
            path   = dict(default=None),
            target = dict(choices=['all', 'vms', 'switches'])
        )
    )

    state  = module.params['state']
    path   = module.params['path']
    target = module.params['target']

    rc = 0
    stdout = stderr = ''
    result = {}

    # Let's check upfront the required binaries are present. If they're
    # missing we're either not on OpenBSD or the release is too old.
    for v in ['vmd', 'vmctl']:
        if not os.access(os.path.join('/usr/sbin', v), os.X_OK):
            module.fail_json(msg="Could not find %s, unable to continue" % (b))

    if state == 'reloaded':
        (rc, stdout, stderr, changed) = vmm_ctl_reload(module)
    elif state == 'loaded':
        (rc, stdout, stderr, changed) = vmm_ctl_load(module, path)
    elif state == 'reset':
        (rc, stdout, stderr, changed) = vmm_ctl_reset(module, target)

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
