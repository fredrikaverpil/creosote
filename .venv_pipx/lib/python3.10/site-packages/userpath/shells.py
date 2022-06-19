from os import environ, path, pathsep


DEFAULT_SHELLS = ('bash', 'sh')


class Shell(object):
    comment_starter = '#'

    def __init__(self, home=None):
        self.home = home or path.expanduser('~')


class Sh(Shell):
    def config(self, location, front=True):
        head, tail = (location, '$PATH') if front else ('$PATH', location)
        new_path = '{}{}{}'.format(head, pathsep, tail)

        return {path.join(self.home, '.profile'): 'PATH="{}"'.format(new_path)}

    @classmethod
    def show_path_commands(cls):
        # TODO: Find out what file influences non-login shells. The issue may simply be our Docker setup.
        return [['sh', '-i', '-l', '-c', 'echo $PATH']]


class Bash(Shell):
    def config(self, location, front=True):
        head, tail = (location, '$PATH') if front else ('$PATH', location)
        new_path = '{}{}{}'.format(head, pathsep, tail)
        contents = 'export PATH="{}"'.format(new_path)

        configs = {path.join(self.home, '.bashrc'): contents}

        # https://github.com/ofek/userpath/issues/3#issuecomment-492491977
        profile_path = path.join(self.home, '.profile')
        bash_profile_path = path.join(self.home, '.bash_profile')

        if path.exists(profile_path) and not path.exists(bash_profile_path):
            login_config = profile_path
        else:
            # NOTE: If it is decided in future that we want to make a distinction between
            # login and non-login shells, be aware that macOS will still need this since
            # Terminal.app runs a login shell by default for each new terminal window.
            login_config = bash_profile_path

        configs[login_config] = contents

        return configs

    @classmethod
    def show_path_commands(cls):
        return [['bash', '-i', '-c', 'echo $PATH'], ['bash', '-i', '-l', '-c', 'echo $PATH']]


class Fish(Shell):
    def config(self, location, front=True):
        location = ' '.join(location.split(pathsep))
        head, tail = (location, '$PATH') if front else ('$PATH', location)

        # https://github.com/fish-shell/fish-shell/issues/527#issuecomment-12436286
        contents = 'set PATH {} {}'.format(head, tail)

        return {path.join(self.home, '.config', 'fish', 'config.fish'): contents}

    @classmethod
    def show_path_commands(cls):
        return [
            ['fish', '-i', '-c', 'for p in $PATH; echo "$p"; end'],
            ['fish', '-i', '-l', '-c', 'for p in $PATH; echo "$p"; end'],
        ]


class Xonsh(Shell):
    def config(self, location, front=True):
        locations = location.split(pathsep)

        if front:
            contents = '\n'.join('$PATH.insert(0, {!r})'.format(location) for location in reversed(locations))
        else:
            contents = '\n'.join('$PATH.append({!r})'.format(location) for location in locations)

        return {path.join(self.home, '.xonshrc'): contents}

    @classmethod
    def show_path_commands(cls):
        command = "print('{}'.join($PATH))".format(pathsep)
        return [['xonsh', '-i', '-c', command], ['xonsh', '-i', '--login', '-c', command]]


class Zsh(Shell):
    def config(self, location, front=True):
        head, tail = (location, '$PATH') if front else ('$PATH', location)
        new_path = '{}{}{}'.format(head, pathsep, tail)
        contents = 'export PATH="{}"'.format(new_path)

        zdotdir = environ.get('ZDOTDIR', self.home)
        return {path.join(zdotdir, '.zshrc'): contents, path.join(zdotdir, '.zprofile'): contents}

    @classmethod
    def show_path_commands(cls):
        return [['zsh', '-i', '-c', 'echo $PATH'], ['zsh', '-i', '-l', '-c', 'echo $PATH']]


SHELLS = {
    'bash': Bash,
    'fish': Fish,
    'sh': Sh,
    'xonsh': Xonsh,
    'zsh': Zsh,
}
