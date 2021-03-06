# nephelaiio.tmux

[![Build Status](https://travis-ci.org/nephelaiio/ansible-role-tmux.svg?branch=master)](https://travis-ci.org/nephelaiio/ansible-role-tmux)

An [ansible role](https://galaxy.ansible.com/nephelaiio/tmux) to install and configure {tmux}(https://tmux.github.io)

## Role Variables

Please refer to the [defaults file](/defaults/main.yml) for an up to date list of input parameters.

## Example Playbook

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

```
    - hosts: servers
      roles:
         - role: tmux
```

## Testing

Please make sure your environment has [docker](https://www.docker.com) installed in order to run role validation tests. Additional python dependencies are listed in the [requirements file](https://github.com/nephelaiio/ansible-role-requirements/blob/master/requirements.txt)

This role is tested against the following distributions:

- Ubuntu Bionic
- Ubuntu Xenial
- CentOS 7
- Debian Stretch
- Arch Linux

You can test the role directly from sources using command `molecule test`

## License

This project is licensed under the terms of the [MIT License](/LICENSE)
