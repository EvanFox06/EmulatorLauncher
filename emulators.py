import os
from os import path, system

import requests
from PIL import Image


class Emulators:
    class Emulator:
        """
        Stores the information of an emulator
        Should never be constructed directly
        """
        def __init__(self, sid: str, ext: str, gh_path: str):
            """
            :param sid: string id (also the name of the emulator directory)
            :param ext: extension of the game files this emulator uses
            :param gh_path: the emulators GitHub repo path in the form of '{owner}/{repo}'
            """
            self.id = sid
            self.ext = ext
            self.gh_path = gh_path
            self.icon = Image.open(f'{sid}/{sid}.png').resize((40, 40))

        @staticmethod
        def get_run_cmd(game) -> str:
            """
            :param game: the game to run in the emulator
            :return: the bash command used to run the emulator
            """
            return f'echo "run {game.path}"'

        def run_game(self, game) -> None:
            """
            :param game: the game to run in the emulator
            :return: None
            """
            cmd = self.get_run_cmd(game)
            print('running:', cmd)
            system(cmd)

        @staticmethod
        def installed_version() -> str:
            """
            :return: the installed version of this emulator
            """
            return '0'

        def latest_version(self) -> str:
            """
            :return: the latest version of this emulator from GitHub
            """
            return requests.get(f'https://api.github.com/repos/{self.gh_path}/releases/latest', headers={
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'User-Agent': 'EvanFox06'
            }).json()['tag_name']

    class __Mgba(Emulator):
        def __init__(self):
            super().__init__('mgba', 'gba', 'mgba-emu/mgba')

        @staticmethod
        def get_run_cmd(game):
            return f'{path.abspath('mgba/mgba')} "{game.path}"'

        @staticmethod
        def installed_version():
            v_out = os.popen(f'{path.abspath('mgba/mgba')} --version').read()
            return v_out.split()[1]


    class __Dolphin(Emulator):
        def __init__(self):
            super().__init__('dolphin', 'rvz', '')

        @staticmethod
        def get_run_cmd(game):
            return f'{path.abspath("dolphin/dolphin")} "{game.path}"'

        @staticmethod
        def installed_version():
            return 'auto'

        def latest_version(self):
            return 'auto'

    class __MelonDS(Emulator):
        def __init__(self):
            super().__init__('melonds', 'nds', 'melonDS-emu/melonDS')

        @staticmethod
        def get_run_cmd(game):
            return f'{path.abspath('melonds/melonds')} "{game.path}"'

        @staticmethod
        def installed_version():
            v_out = os.popen(f'{path.abspath('melonds/melonds')} --help').read()
            return v_out.split('\n')[0].split()[1]

    class __Azahar(Emulator):
        def __init__(self):
            super().__init__('azahar', 'cci', 'azahar-emu/azahar')

        @staticmethod
        def get_run_cmd(game):
            return f'{path.abspath('azahar/azahar')} "{game.path}"'

        @staticmethod
        def installed_version():
            v_out = os.popen(f'{path.abspath('azahar/azahar')} -v').read()
            return v_out.split()[1]

    MGBA = __Mgba()
    DOLPHIN = __Dolphin()
    MELONDS = __MelonDS()
    AZAHAR = __Azahar()

    ALL: list[Emulator] = [MGBA, DOLPHIN, MELONDS, AZAHAR]

    @staticmethod
    def from_ext(ext: str) -> Emulator | None:
        """
        :param ext: the extension of a game file
        :return: the emulator that should be used to run it
        """
        for e in Emulators.ALL:
            if e.ext == ext:
                return e
        return None