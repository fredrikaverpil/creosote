import os
import platform
from datetime import datetime
from io import open

from .shells import DEFAULT_SHELLS, SHELLS
from .utils import ensure_parent_dir_exists, get_flat_output, get_parent_process_name, location_in_path, normpath

try:
    import winreg
except ImportError:
    try:
        import _winreg as winreg
    except ImportError:
        winreg = None


class WindowsInterface:
    def __init__(self, **kwargs):
        pass

    @staticmethod
    def _get_new_path():
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ) as key:
            return winreg.QueryValueEx(key, 'PATH')[0]

    def location_in_new_path(self, location, check=False):
        locations = normpath(location).split(os.pathsep)
        new_path = self._get_new_path()

        for location in locations:
            if not location_in_path(location, new_path):
                if check:
                    raise Exception('Unable to find `{}` in:\n{}'.format(location, new_path))
                else:
                    return False
        else:
            return True

    def put(self, location, front=True, check=False, **kwargs):
        import ctypes

        location = normpath(location)

        head, tail = (location, self._get_new_path()) if front else (self._get_new_path(), location)
        new_path = '{}{}{}'.format(head, os.pathsep, tail)

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_path)

        # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessagetimeoutw
        # https://docs.microsoft.com/en-us/windows/win32/winmsg/wm-settingchange
        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF,  # HWND_BROADCAST
            0x1A,  # WM_SETTINGCHANGE
            0,  # must be NULL
            'Environment',
            0x0002,  # SMTO_ABORTIFHUNG
            5000,  # milliseconds
            ctypes.wintypes.DWORD(),
        )

        return self.location_in_new_path(location, check=check)


class UnixInterface:
    def __init__(self, shells=None, all_shells=False, home=None):
        if shells:
            all_shells = False
        else:
            if all_shells:
                shells = sorted(SHELLS)
            else:
                shells = [self.detect_shell()]

        shells = [os.path.basename(shell).lower() for shell in shells if shell]
        shells = [shell for shell in shells if shell in SHELLS]

        if not shells:
            shells = DEFAULT_SHELLS

        # De-dup and retain order
        deduplicated_shells = set()
        selected_shells = []
        for shell in shells:
            if shell not in deduplicated_shells:
                deduplicated_shells.add(shell)
                selected_shells.append(shell)

        self.shells = [SHELLS[shell](home) for shell in selected_shells]
        self.shells_to_verify = [SHELLS[shell](home) for shell in DEFAULT_SHELLS] if all_shells else self.shells

    @classmethod
    def detect_shell(cls):
        # First, try to see what spawned this process
        shell = get_parent_process_name().lower()
        if shell in SHELLS:
            return shell

        # Then, search for environment variables that are known to be set by certain shells
        # NOTE: This likely does not work when not directly in the shell
        if 'BASH_VERSION' in os.environ:
            return 'bash'

        # Finally, try global environment
        shell = os.path.basename(os.environ.get('SHELL', '')).lower()
        if shell in SHELLS:
            return shell

    def location_in_new_path(self, location, check=False):
        locations = normpath(location).split(os.pathsep)

        for shell in self.shells_to_verify:
            for show_path_command in shell.show_path_commands():
                new_path = get_flat_output(show_path_command)
                for location in locations:
                    if not location_in_path(location, new_path):
                        if check:
                            raise Exception(
                                'Unable to find `{}` in the output of `{}`:\n{}'.format(
                                    location, show_path_command, new_path
                                )
                            )
                        else:
                            return False
        else:
            return True

    def put(self, location, front=True, app_name=None, check=False):
        location = normpath(location)
        app_name = app_name or 'userpath'

        for shell in self.shells:
            for file, contents in shell.config(location, front=front).items():
                try:
                    ensure_parent_dir_exists(file)

                    if os.path.exists(file):
                        with open(file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                    else:
                        lines = []

                    if any(contents in line for line in lines):
                        continue

                    lines.append(
                        u'\n{} Created by `{}` on {}\n'.format(
                            shell.comment_starter, app_name, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                        )
                    )
                    lines.append(u'{}\n'.format(contents))

                    with open(file, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                except Exception:
                    continue

        return self.location_in_new_path(location, check=check)


__default_interface = WindowsInterface if os.name == 'nt' or platform.system() == 'Windows' else UnixInterface


class Interface(__default_interface):
    pass
