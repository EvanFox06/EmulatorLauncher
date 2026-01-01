import os
from typing import Callable
from tkinter import Event
from io import BytesIO
from math import floor
from tkinter import Menu
from typing import Any

import cv2
import customtkinter as ctk
import numpy
import requests
from PIL import Image

from emulators import Emulators


class WrappingFrame(ctk.CTkFrame):
    def __init__(self, master: Any):
        """
        Frame for game objects

        Automatically wraps child objects to next line
        :param master: master tkinter widget
        """
        super().__init__(master)
        self.games = []
        self.bind('<Configure>', self.__reconfigure)

    def __reconfigure(self, _event: Event = None) -> None:
        """
        recalculates the position of contained game objects based on width
        :param _event: Purely for binding to tkinter event. Should not be set to anything.
        :return: None
        """
        # calculate the amount of games that fit on one line
        # (assume that the games are 150px wide with 10px padding)
        # and arrange them in a grid based on that
        x_size: int = self._current_width // 170
        if x_size == 0:
            x_size = 1
        for i in range(len(self.games)):
            self.games[i].grid(row=floor(i / x_size), column=int(i % x_size), padx=10, pady=10)

    def clear(self) -> None:
        """
        Removes all game objects from the frame
        :return: None
        """
        self.games = []

    def sort(self) -> None:
        """
        Sorts game objects alphabetically
        :return: None
        """
        self.games.sort(key = lambda g: g.name)


class Game(ctk.CTkFrame):
    def __init__(self, master: WrappingFrame, name: str, emulator: Emulators.Emulator):
        """
        Frame object for displaying and running a game
        :param master: master tkinter widget
        :param name: game name
        :param emulator: emulator that is used to run this game
        """
        super().__init__(master, border_width=2)
        master.games.append(self)
        self.name = name
        self.emulator = emulator
        self.path = os.path.abspath(f'{emulator.id}/{name}/game.{emulator.ext}')

        # load the game icon from its directory (default to fully white image)
        img_path = os.path.join(emulator.id, name, 'icon.png')
        if not os.path.isfile(img_path):
            self.img = Image.new('RGBA', (1, 1), 'white')
        else:
            self.img = Image.open(img_path).resize((150, 150))

        # create extra image to be used when mouse is hovering over the game
        self.hover_img = Image.fromarray(cv2.convertScaleAbs(numpy.array(self.img), alpha=0.5, beta=0))
        # add the emulator icon to the corner of both images
        self.img.paste(self.emulator.icon, box=(110, 110), mask=self.emulator.icon)
        self.hover_img.paste(self.emulator.icon, box=(110, 110), mask=self.emulator.icon)
        self.img = ctk.CTkImage(self.img, size=(150, 150))
        self.hover_img = ctk.CTkImage(self.hover_img, size=(150, 150))

        self.icon = ctk.CTkLabel(self, image=self.img, text='')
        self.title = ctk.CTkLabel(self, text=self.name, width=150, wraplength=150, font=ctk.CTkFont(size=20))
        self.icon.grid(row=0, column=0)
        self.title.grid(row=1, column=0)

        # bind hover and click actions for darkening the image and running the game to all relevant objects
        for o in self, self.icon, self.title:
            o.bind('<Button-1>', lambda e: self.icon.configure(image=self.img))
            o.bind('<ButtonRelease-1>', self.run)
            o.bind('<Enter>', lambda e: self.icon.configure(image=self.hover_img))
            o.bind('<Leave>', lambda e: self.icon.configure(image=self.img))

    def run(self, _event: Event = None) -> None:
        """
        Runs the game
        :param _event: Purely for binding to tkinter event. Should not be set to anything.
        :return: None
        """
        self.icon.configure(image=self.hover_img)
        self.emulator.run_game(self)


class AddGame(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, reload_games: Callable):
        """
        TopLevel window for adding a game to the library
        :param master: master tkinter widget
        :param reload_games: Function to reload the games list
        """
        super().__init__(master)
        self.reload_games = reload_games
        self.title('Add Game')
        self.font = ctk.CTkFont(size=20)
        self.file_label = ctk.CTkLabel(self, text='File:', font=self.font)
        self.file_input = ctk.CTkComboBox(self, values=self.game_choice(), font=self.font,
                                          dropdown_font=self.font, state='readonly')
        self.name_label = ctk.CTkLabel(self, text='Name:', font=self.font)
        self.name_input = ctk.CTkEntry(self, font=self.font)
        self.icon_label = ctk.CTkLabel(self, text='Icon URL:', font=self.font)
        self.icon_input = ctk.CTkEntry(self, font=self.font)
        self.add_button = ctk.CTkButton(self, text='Add Game', command=self.add_game, font=self.font)

        self.file_label.grid(row=0, column=0, padx=20, pady=10, sticky='e')
        self.file_input.grid(row=0, column=1, padx=20, pady=10)
        self.name_label.grid(row=1, column=0, padx=20, pady=10, sticky='e')
        self.name_input.grid(row=1, column=1, padx=20, pady=10)
        self.icon_label.grid(row=2, column=0, padx=20, pady=10, sticky='e')
        self.icon_input.grid(row=2, column=1, padx=20, pady=10)
        self.add_button.grid(row=3, column=0, padx=20, pady=10, columnspan=2)

    @staticmethod
    def game_choice():
        """
        :return: The game files in the rom zips folder (excludes zip and 7z files)
        """
        games = sorted([f for f in os.listdir('rom zips') if os.path.splitext(f)[1] not in ('.zip', '.7z')])
        if not games:
            return ['']
        return games

    def add_game(self) -> None:
        """
        Adds a game to the library based on the inputted values
        :return: None
        """
        file = self.file_input.get()
        ext = os.path.splitext(file)[1][1:]
        emu = Emulators.from_ext(ext)
        if emu is None:
            return
        name = self.name_input.get()

        # create a directory for the game and put the game file in there
        os.mkdir(os.path.join(emu.id, name))
        os.rename(f'rom zips/{file}', os.path.join(emu.id, name, f'game.{ext}'))
        # download the icon from the inputted URL and save it into the game directory
        icon_path = os.path.join(emu.id, name, 'icon.png')
        try:
            Image.open(BytesIO(requests.get(self.icon_input.get()).content)).save(icon_path)
        except Exception as e:
            print('Could not load icon')
            print(e)
        # close this window
        self.reload_games()
        self.withdraw()


class EmuOutdated(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, outdated: list[tuple[str, str, Emulators.Emulator]]):
        """
        Top level window to be displayed when an emulator is outdated
        :param master: master tkinter widget
        :param outdated: list of outdated emulators in the form of tuples (installed_ver, latest_ver, emulator)
        """
        super().__init__(master)
        self.title('Emulator outdated!')
        self.font = ctk.CTkFont(size=20)

        self.labels = []
        for i in range(len(outdated)):
            installed, latest, emulator = outdated[i]
            self.labels.append(ctk.CTkLabel(
                self, text=f'{emulator.id} is outdated!\ninstalled: {installed}\nlatest: {latest}', font=self.font))
            self.labels[-1].grid(row=i, column=0, padx=20, pady=20)


class App(ctk.CTk):
    def __init__(self):
        """
        Main application class
        """
        super().__init__(className='EmulatorLauncher')
        self.geometry('600x600')
        self.title('Emulators')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # create a wrapping frame and load all installed games into it
        self.games_frame = None
        self.load_games()

        self.menu = Menu(self)
        self.config(menu=self.menu)
        self.menu.add_command(label='Add Game', command=lambda: AddGame(self, self.load_games))
        self.menu.add_command(label='Open Dolphin', command=lambda: os.system(os.path.abspath('dolphin/dolphin')))

        self.check_emu_versions()
        self.mainloop()

    def check_emu_versions(self) -> None:
        """
        Checks if any of the emulators are outdated
        :return: None
        """
        outdated = []
        for emu in Emulators.ALL:
            vers = emu.installed_version(), emu.latest_version(), emu
            if vers[0] != vers[1]:
                outdated.append(vers)
        if outdated:
            EmuOutdated(self, outdated)


    def load_games(self) -> None:
        """
        loads or reloads all installed games
        :return: None
        """
        if self.games_frame is not None:
            self.games_frame.destroy()
            del self.games_frame
        self.games_frame = WrappingFrame(self)
        self.games_frame.clear()
        for emu in Emulators.ALL:
            for game in self.listdir(emu.id):
                Game(self.games_frame, game, emu)
        self.games_frame.sort()
        self.games_frame.grid(sticky='nsew')

    @staticmethod
    def listdir(dir_name: str, app_name: str = None) -> list[str]:
        """
        :param dir_name: directory to list
        :param app_name: name of the application in the directory (defaults to dir_name)
        :return: all files in the directory except the application and its relevant subdirectories
        """
        if app_name is None:
            app_name = dir_name
        return [d for d in os.listdir(dir_name) if d not in
                (app_name, app_name + '.config', app_name + '.home', app_name + '.png')]


if __name__ == '__main__':
    App()
