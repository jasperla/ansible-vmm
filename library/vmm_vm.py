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
short_description: Manage VMs with vmctl(8).
description:
    - Manage vmm(4) virtual machines on OpenBSD with vmctl(8). It updates
      the vmd configuration file (C(/etc/vm.conf) by default) to reflect
      the configuration specified by the task.
version_added: "2.3"
author: Jasper Lievisse Adriaanse (@jasper_la)
...
'''

EXAMPLES = '''
# Make sure the VM is started, stopped or reset
#- vmm_ctl: name=web state=started XXX: does this work or do we need to

- vmm_ctl: name=web state=stopped

# Set the state for all VMs
- vmm_ctl: name='*' state=started
'''

def main():
    module = AnsibleModule(
	argument_spec = dict(
            name  = dict(required=True),
            state = dict(required=True, choices=['present', 'started'])
        )
    )

    name = module.params['name']
    state = module.params['state']

    rc = 0
    stdout = stderr = ''
    result = { 'name': name }

    result['changed'] = changed

    module.exit_json(**result)

# Import module snippets.
from ansible.module_utils.basic import *
main()
