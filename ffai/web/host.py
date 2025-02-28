"""
==========================
Author: Niels Justesen
Year: 2018
==========================
This module contains the Host class that is used to manage games in memory. 
A similar host could be implemented that uses a persistent database instead.
"""

from ffai.core.util import *
import pickle
import glob
import uuid


class Save:

    def __init__(self, game, team_id):
        self.game = game
        self.team_id = team_id

    def to_json(self):
        return {
            'game': self.game.to_json(),
            'team_id': self.team_id
        }


class InMemoryHost:

    def __init__(self):
        self.games = {}

    def add_game(self, game):
        self.games[game.game_id] = game

    def end_game(self, id):
        del self.games[id]

    def get_game(self, id):
        return self.games[id]

    def get_games(self):
        return list(self.games.values())

    def save_game(self, game_id, name, team_id):
        game = self.get_game(game_id)
        filename = os.path.join(get_data_path("saves/"), name+".ffai")
        print("Saving game")
        pickle.dump(game, open(filename, "wb"))
        game_clone = pickle.load(open(filename, "rb"))
        game_clone.game_id = str(uuid.uuid1())
        save = Save(game, team_id=team_id)
        pickle.dump(save, open(filename, "wb"))
        print("Game saved")

    def load_file(self, filename):
        print("Loading game")
        save = pickle.load(open(filename, "rb"))
        print("Game loaded")
        return save

    def load_game(self, name):
        save = self.load_file(get_data_path("saves/" + name.lower() + ".ffai"))
        self.games[save.game.game_id] = save.game
        return save

    def get_savenames(self):
        files = glob.glob(get_data_path("saves/*"))
        out = []
        for file in files:
            file = file.lower()
            if ".ffai" not in file:
                continue
            file = file.split(".ffai")[0]
            if "/" in file:
                file = file.split("/")[-1]
            out.append(file)
        return out

    def get_saved_games(self):
        games = [self.load_file(filename) for filename in glob.glob(get_data_path("saves/*"))]
        return zip(games, self.get_savenames())
