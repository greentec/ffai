#!/usr/bin/env python3

from ffai.ai.competition import Competition
import examples.scripted_bot_example
import examples.grodbot
from copy import deepcopy
from ffai.core.load import get_team, get_rule_set, get_config

# Load competition configuration for the bot bowl
config = get_config('ff-11-bot-bowl-i.json')


# scripted vs. random
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='scripted', competitor_b_name='random', config=config)
results = competition.run(num_games=20)
results.print()

# Random vs. idle
config.time_limits.game = 10  # 10 second time limit per game
config.time_limits.turn = 1  # 1 second time limit per turn
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='random', competitor_b_name='idle', config=config)
results = competition.run(num_games=2)
results.print()

# Random vs. violator
config.time_limits.game = 60  # 60 second time limit per game
config.time_limits.turn_ = 1  # 1 second time limit per turn
config.time_limits.secondary = 1  # 1 second time limit for secondary choices
config.time_limits.disqualification = 1  # 1 second disqualification limit 
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='random', competitor_b_name='violator', config=config)
results = competition.run(num_games=2)
results.print()

# Random vs. just-in-time
config.time_limits.game = 600  # 60 second time limit per game
config.time_limits.turn = 1  # 1 second time limit per turn
config.time_limits.secondary = 1  # 1 second time limit for secondary choices
config.time_limits.disqualification = 1  # 1 second disqualification limit 
#config.debug_mode = True
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='random', competitor_b_name='just-in-time', config=config)
results = competition.run(num_games=2)
results.print()

# Random vs. init crash
config.time_limits.game = 60  # 60 second time limit per game
config.time_limits.turn = 1  # 1 second time limit per turn
config.time_limits.secondary = 1  # 1 second time limit for secondary choices
config.time_limits.disqualification = 1  # 1 second disqualification threshold 
config.time_limits.init = 20  # 2 init limit 
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='random', competitor_b_name='init-crash', config=config)
results = competition.run(num_games=2)
results.print()

# Random vs. crash
config.time_limits.game = 32  # 32 second time limit per game
config.time_limits.turn = 1  # 1 second time limit per turn
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='random', competitor_b_name='crash', config=config)
results = competition.run(num_games=2)
results.print()

# Random vs. manipulator
config.time_limits.game = 32  # 32 second time limit per game
config.time_limits.turn = 1  # 1 second time limit per turn
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='random', competitor_b_name='manipulator', config=config)
results = competition.run(num_games=2)
results.print()

# Scripted vs. grodbot
config = get_config('ff-11-bot-bowl-i.json') 
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='scripted', competitor_b_name='grodbot', config=config)
results = competition.run(num_games=2)
results.print()


# Scripted vs. grodbot
config = get_config('ff-11-bot-bowl-i.json')
competition = Competition('MyCompetition', competitor_a_team_id='human-1', competitor_b_team_id='human-2', competitor_a_name='random', competitor_b_name='grodbot', config=config)
results = competition.run(num_games=2)
results.print()
