#!/usr/bin/env python3

import ffai.web.api as api
import ffai.ai.bots as bot
import ffai.core.model as m
import ffai.core.table as t
import ffai.core.procedure as p
import ffai.util.pathfinding as pf
from typing import Optional, List, Dict, Tuple
import time
import ffai.core.game as g
import math
import random
from enum import Enum
from ffai.ai.registry import register_bot, make_bot
import ffai.util.bothelper as helper
from ffai.util.bothelper import ActionSequence
# from operator import itemgetter
from ffai.core.procedure import *


class GrodBot(Agent):
    """
    A Bot that uses path finding to evaluate all possibilities.

    WIP!!! Hand-offs and Pass actions going a bit funny.

    """

    mean_actions_available = []
    steps = []

    BASE_SCORE_BLITZ = 60.0
    BASE_SCORE_FOUL = -50.0
    BASE_SCORE_BLOCK = 2*65   # For a two dice block
    BASE_SCORE_HANDOFF = 40.0
    BASE_SCORE_PASS = 40.0
    BASE_SCORE_MOVE_TO_OPPONENT = 45.0
    BASE_SCORE_MOVE_BALL = 45.0
    BASE_SCORE_MOVE_TOWARD_BALL = 45.0
    BASE_SCORE_MOVE_TO_SWEEP = 0.0
    BASE_SCORE_CAGE_BALL = 70.0
    BASE_SCORE_MOVE_TO_BALL = 60.0
    BASE_SCORE_BALL_AND_CHAIN = 75.0
    BASE_SCORE_DEFENSIVE_SCREEN = 0.0
    ADDITIONAL_SCORE_DODGE = 0.0  # Lower this value to dodge more.
    ADDITIONAL_SCORE_NEAR_SIDELINE = -20.0
    ADDITIONAL_SCORE_SIDELINE = -40.0

    def __init__(self, name, verbose=True):
        super().__init__(name)
        self.my_team = None
        self.opp_team = None
        self.current_move: Optional[ActionSequence] = None
        self.verbose = verbose
        self.heat_map: Optional[helper.FfHeatMap] = None
        self.actions_available = []

    def act(self, game):

        available = 0
        for action_choice in game.state.available_actions:
            if len(action_choice.positions) == 0 and len(action_choice.players) == 0:
                available += 1
            elif len(action_choice.positions) > 0:
                available += len(action_choice.positions)
            else:
                available += len(action_choice.players)
        self.actions_available.append(available)

        # Get current procedure
        proc = game.state.stack.peek()

        # Call private function
        if isinstance(proc, CoinTossFlip):
            return self.coin_toss_flip(game)
        if isinstance(proc, CoinTossKickReceive):
            return self.coin_toss_kick_receive(game)
        if isinstance(proc, Setup):
            return self.setup(game)
        if isinstance(proc, PlaceBall):
            return self.place_ball(game)
        if isinstance(proc, HighKick):
            return self.high_kick(game)
        if isinstance(proc, Touchback):
            return self.touchback(game)
        if isinstance(proc, Turn) and proc.quick_snap:
            return self.quick_snap(game)
        if isinstance(proc, Turn) and proc.blitz:
            return self.blitz(game)
        if isinstance(proc, Turn):
            return self.turn(game)
        if isinstance(proc, PlayerAction):
            return self.player_action(game)
        if isinstance(proc, Block):
            return self.block(game)
        if isinstance(proc, Push):
            return self.push(game)
        if isinstance(proc, FollowUp):
            return self.follow_up(game)
        if isinstance(proc, Apothecary):
            return self.apothecary(game)
        if isinstance(proc, PassAction):
            return self.pass_action(game)
        if isinstance(proc, Catch):
            return self.catch(game)
        if isinstance(proc, Interception):
            return self.interception(game)
        if isinstance(proc, GFI):
            return self.gfi(game)
        if isinstance(proc, Dodge):
            return self.dodge(game)
        if isinstance(proc, Pickup):
            return self.pickup(game)

        raise Exception("Unknown procedure")

    def new_game(self, game: g.Game, team):
        """
        Called when a new game starts.
        """
        self.my_team = team
        self.opp_team = game.get_opp_team(team)
        self.actions_available = []

    def coin_toss_flip(self, game: g.Game):
        """
        Select heads/tails and/or kick/receive
        """
        return m.Action(t.ActionType.TAILS)
        # return Action(ActionType.HEADS)

    def coin_toss_kick_receive(self, game: g.Game):
        """
        Select heads/tails and/or kick/receive
        """
        return m.Action(t.ActionType.RECEIVE)
        # return Action(ActionType.KICK)

    def setup(self, game: g.Game) -> m.Action:
        """
        Move players from the reserves to the pitch
        """

        if isinstance(game.state.stack.peek(), p.Setup):
            proc: p.Setup = game.state.stack.peek()
        else:
            raise ValueError('Setup procedure expected')

        if proc.reorganize:
            # We are dealing with perfect defence.  For now do nothing, but we could send all players back to reserve box
            action_steps: List[m.Action] = [m.Action(t.ActionType.END_SETUP)]
            self.current_move = ActionSequence(action_steps, description='Perfect Defence do nothing')

        else:

            if not helper.get_players(game, self.my_team, include_own=True, include_opp=False, include_off_pitch=False):
                # If no players are on the pitch yet, create a new ActionSequence for the setup.
                action_steps: List[m.Action] = []

                turn = game.state.round
                half = game.state.half
                opp_score = 0
                for team in game.state.teams:
                    if team != self.my_team:
                        opp_score = max(opp_score, team.state.score)
                score_diff = self.my_team.state.score - opp_score

                # Choose 11 best players to field
                players_available: List[m.Player] = []
                for available_action in game.state.available_actions:
                    if available_action.action_type == t.ActionType.PLACE_PLAYER:
                        players_available = available_action.players

                players_sorted_value = sorted(players_available, key=lambda x: player_value(game, x), reverse=True)
                n_keep: int = min(11, len(players_sorted_value))
                players_available = players_sorted_value[:n_keep]

                # Are we kicking or receiving?
                if game.state.receiving_this_drive:
                    place_squares: List[m.Square] = [
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 7),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 8),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 9),
                        # Receiver next
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 8), 8),
                        # Support line players
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 10),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 11),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 5),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 13),
                        # A bit wide semi-defensive
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 11), 4),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 11), 12),
                        # Extra help at the back
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 10), 8)
                    ]
                    players_sorted_bash = sorted(players_available, key=lambda x: player_bash_ability(game, x), reverse=True)
                    players_sorted_blitz = sorted(players_available, key=lambda x: player_blitz_ability(game, x), reverse=True)

                else:
                    place_squares: List[m.Square] = [

                        # LOS squares first
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 7),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 8),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 13), 9),

                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 12), 3),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 12), 13),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 11), 2),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 11), 14),

                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 12), 5),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 12), 10),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 11), 11),
                        game.state.pitch.get_square(helper.reverse_x_for_right(game, self.my_team, 11), 5)
                        ]

                    players_sorted_bash = sorted(players_available, key=lambda x: player_bash_ability(game, x), reverse=True)
                    players_sorted_blitz = sorted(players_available, key=lambda x: player_blitz_ability(game, x), reverse=True)

                for i in range(len(players_available)):
                    action_steps.append(m.Action(t.ActionType.PLACE_PLAYER, player=players_sorted_bash[i], pos=place_squares[i]))

                action_steps.append(m.Action(t.ActionType.END_SETUP))

                self.current_move = ActionSequence(action_steps, description='Setup')

        # We must have initialised the action sequence, lets execute it
        next_action: m.Action = self.current_move.popleft()
        return next_action

    def place_ball(self, game: g.Game):
        """
        Place the ball when kicking.
        """
        #left_center = m.Square(7, 8)
        #right_center = m.Square(20, 8)

        center_opposite: m.Square = m.Square(helper.reverse_x_for_left(game, self.my_team, 7), 8)
        return m.Action(t.ActionType.PLACE_BALL, pos=center_opposite)

    def high_kick(self, game: g.Game):
        """
        Select player to move under the ball.
        """
        ball_pos = game.get_ball_position()
        if game.is_team_side(game.get_ball_position(), self.my_team) and game.get_player_at(game.get_ball_position()) is None:
            players_available = game.get_players_on_pitch(self.my_team, up=True)
            if players_available:
                players_sorted = sorted(players_available, key=lambda x: player_blitz_ability(game, x), reverse=True)
                player = players_sorted[0]
                return m.Action(t.ActionType.PLACE_PLAYER, player=player, pos=ball_pos)
        return m.Action(t.ActionType.SELECT_NONE)

    def touchback(self, game: g.Game):
        """
        Select player to give the ball to.
        """
        players_available = game.get_players_on_pitch(self.my_team, up=True)
        if players_available:
            players_sorted = sorted(players_available, key=lambda x: player_blitz_ability(game, x), reverse=True)
            player = players_sorted[0]
            return m.Action(t.ActionType.SELECT_PLAYER, player=player)
        return m.Action(t.ActionType.SELECT_NONE)

    def set_next_move(self, game: g.Game):
        """ Set self.current_move

        :param game:
        """
        self.current_move = None

        players_moved: List[m.Player] = helper.get_players(game, self.my_team, include_own=True, include_opp=False, include_used=True, only_used=False)

        players_to_move: List[m.Player] = helper.get_players(game, self.my_team, include_own=True, include_opp=False, include_used=False)
        paths_own: Dict[m.Player, List[pf.Path]] = dict()
        ff_map = pf.FfTileMap(game.state)
        for player in players_to_move:
            player_mover = pf.FfMover(player)
            finder = pf.AStarPathFinder(ff_map, player.move_allowed(), allow_diag_movement=True, heuristic=pf.BruteForceHeuristic(), probability_costs=True)
            paths = finder.find_paths(player_mover, player.position.x, player.position.y)
            paths_own[player] = paths

        players_opponent: List[m.Player] = helper.get_players(game, self.my_team, include_own=False, include_opp=True, include_stunned=False)
        paths_opposition: Dict[m.Player, List[pf.Path]] = dict()
        for player in players_opponent:
            player_mover = pf.FfMover(player)
            finder = pf.AStarPathFinder(ff_map, player.move_allowed(), allow_diag_movement=True, heuristic=pf.BruteForceHeuristic(), probability_costs=True)
            paths = finder.find_paths(player_mover, player.position.x, player.position.y)
            paths_opposition[player] = paths

        # Create a heat-map of control zones
        heat_map: helper.FfHeatMap = helper.FfHeatMap(game, self.my_team)
        heat_map.add_unit_by_paths(game, paths_opposition)
        heat_map.add_unit_by_paths(game, paths_own)
        heat_map.add_players_moved(game, helper.get_players(game, self.my_team, include_own=True, include_opp=False, only_used=True))
        self.heat_map = heat_map

        all_actions: List[ActionSequence] = []
        for action_choice in game.state.available_actions:
            if action_choice.action_type == t.ActionType.START_MOVE:
                players_available: List[m.Player] = action_choice.players
                for player in players_available:
                    paths = paths_own[player]
                    all_actions.extend(potential_move_actions(game, heat_map, player, paths))
            elif action_choice.action_type == t.ActionType.START_BLITZ:
                players_available: List[m.Player] = action_choice.players
                for player in players_available:
                    player_mover = pf.FfMover(player)
                    finder = pf.AStarPathFinder(ff_map, player.move_allowed() - 1, allow_diag_movement=True, heuristic=pf.BruteForceHeuristic(), probability_costs=True)
                    paths = finder.find_paths(player_mover, player.position.x, player.position.y)
                    all_actions.extend(potential_blitz_actions(game, heat_map, player, paths))
            elif action_choice.action_type == t.ActionType.START_FOUL:
                players_available: List[m.Player] = action_choice.players
                for player in players_available:
                    paths = paths_own[player]
                    all_actions.extend(potential_foul_actions(game, heat_map, player, paths))
            elif action_choice.action_type == t.ActionType.START_BLOCK:
                players_available: List[m.Player] = action_choice.players
                for player in players_available:
                    all_actions.extend(potential_block_actions(game, heat_map, player))
            elif action_choice.action_type == t.ActionType.START_PASS:
                players_available: List[m.Player] = action_choice.players
                for player in players_available:
                    player_square: m.Square = player.position
                    if game.state.pitch.get_ball_position() == player_square:
                        paths = paths_own[player]
                        all_actions.extend(potential_pass_actions(game, heat_map, player, paths))
            elif action_choice.action_type == t.ActionType.START_HANDOFF:
                players_available: List[m.Player] = action_choice.players
                for player in players_available:
                    player_square: m.Square = player.position
                    if game.state.pitch.get_ball_position() == player_square:
                        paths = paths_own[player]
                        all_actions.extend(potential_handoff_actions(game, heat_map, player, paths))
            elif action_choice.action_type == t.ActionType.END_TURN:
                all_actions.extend(potential_end_turn_action(game))

        if all_actions:
            all_actions.sort(key=lambda x: x.score, reverse=True)
            self.current_move = all_actions[0]

            if self.verbose:
                print('   Turn=H' + str(game.state.half) + 'R' + str(game.state.round) + ', Team=' + game.state.current_team.name + ', Action=' + self.current_move.description + ', Score=' + str(self.current_move.score))

    def set_continuation_move(self, game: g.Game):
        """ Set self.current_move

        :param game:
        """
        self.current_move = None

        player: m.Player = game.state.active_player
        player_square: m.Square = player.position
        ff_map = pf.FfTileMap(game.state)
        player_mover = pf.FfMover(player)
        finder = pf.AStarPathFinder(ff_map, player.move_allowed(), allow_diag_movement=True, heuristic=pf.BruteForceHeuristic(), probability_costs=True)
        paths = finder.find_paths(player_mover, player_square.x, player_square.y)

        all_actions: List[ActionSequence] = []
        for action_choice in game.state.available_actions:
            if action_choice.action_type == t.ActionType.MOVE:
                players_available: List[m.Player] = action_choice.players
                all_actions.extend(potential_move_actions(game, self.heat_map, player, paths, is_continuation=True))
            elif action_choice.action_type == t.ActionType.END_PLAYER_TURN:
                all_actions.extend(potential_end_player_turn_action(game, self.heat_map, player))

        if all_actions:
            all_actions.sort(key=lambda x: x.score, reverse=True)
            self.current_move = all_actions[0]

            if self.verbose:
                print('   Turn=H' + str(game.state.half) + 'R' + str(game.state.round) + ', Team=' + game.state.current_team.name + ', Action=Continue Move + ' + self.current_move.description + ', Score=' + str(self.current_move.score))

    def turn(self, game: g.Game) -> m.Action:
        """
        Start a new player action / turn.
        """

        # Simple algorithm: 
        #   Loop through all available (yet to move) players.
        #   Compute all possible moves for all players.
        #   Assign a score to each action for each player.
        #   The player/play with the highest score is the one the Bot will attempt to use.
        #   Store a representation of this turn internally (for use by player-action) and return the action to begin.

        self.set_next_move(game)
        next_action: m.Action = self.current_move.popleft()
        return next_action

    def quick_snap(self, game: g.Game):

        self.current_move = None
        return m.Action(t.ActionType.END_TURN)

    def blitz(self, game: g.Game):

        self.current_move = None
        return m.Action(t.ActionType.END_TURN)

    def player_action(self, game: g.Game):
        """
        Take the next action from the current stack and execute
        """
        if self.current_move.is_empty():
            self.set_continuation_move(game)

        action_step = self.current_move.popleft()
        return action_step

    def block(self, game: g.Game):
        """
        Select block die or reroll.
        """
        # Loop through available dice results
        active_player: m.Player = game.state.active_player
        attacker: m.Player = game.state.stack.items[-1].attacker
        defender: m.Player = game.state.stack.items[-1].defender
        favor: m.Team = game.state.stack.items[-1].favor

        actions: List[ActionSequence] = []
        check_reroll = False
        for action_choice in game.state.available_actions:
            if action_choice.action_type == t.ActionType.USE_REROLL:
                check_reroll = True
                continue
            action_steps: List[m.Action] = [
                m.Action(action_choice.action_type)
                ]
            score = block_favourability(action_choice.action_type, self.my_team, active_player, attacker, defender, favor)
            actions.append(ActionSequence(action_steps, score=score, description='Block die choice'))

        if check_reroll and check_reroll_block(game, self.my_team, actions, favor):
                return m.Action(t.ActionType.USE_REROLL)
        else:
            actions.sort(key=lambda x: x.score, reverse=True)
            current_move = actions[0]
            return current_move.action_steps[0]

    def push(self, game: g.Game):
        """
        Select square to push to.
        """
        # Loop through available squares
        block_proc: Optional[p.Block] = helper.last_block_proc(game)
        attacker: m.Player = block_proc.attacker
        defender: m.Player = block_proc.defender
        is_blitz_action = block_proc.blitz
        score: int = -100
        for to_square in game.state.available_actions[0].positions:
            cur_score = score_push(game, defender.position, to_square)
            if cur_score > score:
                score = cur_score
                push_square = to_square
        return m.Action(t.ActionType.PUSH, pos=push_square)

    def follow_up(self, game: g.Game):
        """
        Follow up or not. ActionType.FOLLOW_UP must be used together with a position.
        """
        player = game.state.active_player
        do_follow = check_follow_up(game)
        for position in game.state.available_actions[0].positions:
            # Always follow up
            if do_follow and player.position != position:
                return m.Action(t.ActionType.FOLLOW_UP, pos=position)
            elif not do_follow and player.position == position:
                return m.Action(t.ActionType.FOLLOW_UP, pos=position)

    def apothecary(self, game: g.Game):
        """
        Use apothecary?
        """
        return m.Action(t.ActionType.USE_APOTHECARY)
        # return Action(ActionType.DONT_USE_APOTHECARY)

    def interception(self, game: g.Game):
        """
        Select interceptor.
        """
        for action in game.state.available_actions:
            if action.action_type == t.ActionType.INTERCEPTION:
                for player, agi_rolls in zip(action.players, action.agi_rolls):
                    return m.Action(t.ActionType.INTERCEPTION, player=player)
        return m.Action(t.ActionType.SELECT_NONE)

    def pass_action(self, game: g.Game):
        """
        Reroll or not.
        """
        return m.Action(t.ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def catch(self, game: g.Game):
        """
        Reroll or not.
        """
        return m.Action(t.ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def gfi(self, game: g.Game):
        """
        Reroll or not.
        """
        return m.Action(t.ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def dodge(self, game: g.Game):
        """
        Reroll or not.
        """
        return m.Action(t.ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def pickup(self, game: g.Game):
        """
        Reroll or not.
        """
        return m.Action(t.ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def end_game(self, game: g.Game):
        """
        Called when a game end.
        """
        print("Num steps:", len(self.actions_available))
        print("Avg. branching factor:", np.mean(self.actions_available))
        GrodBot.steps.append(len(self.actions_available))
        GrodBot.mean_actions_available.append(np.mean(self.actions_available))
        print("Avg. Num steps:", np.mean(GrodBot.steps))
        print("Avg. overall branching factor:", np.mean(GrodBot.mean_actions_available))
        winner = game.get_winner()
        print("Casualties: ", game.num_casualties())
        print("Score: " + self.my_team.name + "->" + str(self.my_team.state.score) + " ... " + self.opp_team.name + "->" + str(self.opp_team.state.score))
        if winner is None:
            print("It's a draw")
        elif winner == self:
            print("I ({}) won".format(self.name))
        else:
            print("I ({}) lost".format(self.name))


def block_favourability(block_result: m.ActionType, team: m.Team, active_player: m.Player, attacker: m.Player, defender: m.Player, favor: m.Team) -> float:

    if attacker.team == active_player.team:
        if block_result == t.ActionType.SELECT_DEFENDER_DOWN: return 6.0
        elif block_result == t.ActionType.SELECT_DEFENDER_STUMBLES:
            if defender.has_skill(t.Skill.DODGE) and not attacker.has_skill(t.Skill.TACKLE): return 4.0       # push back
            else: return 6.0
        elif block_result == t.ActionType.SELECT_PUSH:
                return 4.0
        elif block_result == t.ActionType.SELECT_BOTH_DOWN:
            if defender.has_skill(t.Skill.BLOCK) and not attacker.has_skill(t.Skill.BLOCK): return 1.0        # skull
            elif not attacker.has_skill(t.Skill.BLOCK): return 2                                            # both down
            elif attacker.has_skill(t.Skill.BLOCK) and defender.has_skill(t.Skill.BLOCK): return 3.0          # nothing happens
            else: return 5.0                                                                                  # only defender is down
        elif block_result == t.ActionType.SELECT_ATTACKER_DOWN:
            return 1.0                                                                                        # skull
    else:
        if block_result == t.ActionType.SELECT_DEFENDER_DOWN:
            return 1.0                                                                                        # least favourable
        elif block_result == t.ActionType.SELECT_DEFENDER_STUMBLES:
            if defender.has_skill(t.Skill.DODGE) and not attacker.has_skill(t.Skill.TACKLE): return 3       # not going down, so I like this.
            else: return 1.0                                                                                  # splat.  No good.
        elif block_result == t.ActionType.SELECT_PUSH:
            return 3.0
        elif block_result == t.ActionType.SELECT_BOTH_DOWN:
            if not attacker.has_skill(t.Skill.BLOCK) and defender.has_skill(t.Skill.BLOCK): return 6.0        # Attacker down, I am not.
            if not attacker.has_skill(t.Skill.BLOCK) and not defender.has_skill(t.Skill.BLOCK): return 5.0    # Both down is pretty good.
            if attacker.has_skill(t.Skill.BLOCK) and not defender.has_skill(t.Skill.BLOCK): return 2.0        # Just I splat
            else: return 4.0                                                                                  # Nothing happens (both have block).
        elif block_result == t.ActionType.SELECT_ATTACKER_DOWN:
            return 6.0                                                                                        # most favourable!

    return 0.0


def potential_end_player_turn_action(game: g.Game, heat_map, player: m.Player) -> List[ActionSequence]:
    actions: List[ActionSequence] = []
    action_steps: List[m.Action] = [
        m.Action(t.ActionType.END_PLAYER_TURN, player=player)
        ]
    # End turn happens on a score of 1.0.  Any actions with a lower score are never selected.
    actions.append(ActionSequence(action_steps, score=1.0, description='End Turn'))
    return actions


def potential_end_turn_action(game: g.Game) -> List[ActionSequence]:
    actions: List[ActionSequence] = []
    action_steps: List[m.Action] = [
        m.Action(t.ActionType.END_TURN)
        ]
    # End turn happens on a score of 1.0.  Any actions with a lower score are never selected.
    actions.append(ActionSequence(action_steps, score=1.0, description='End Turn'))
    return actions


def potential_block_actions(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player) -> List[ActionSequence]:

    # Note to self: need a "stand up and end move option.
    move_actions: List[ActionSequence] = []
    if not player.state.up:
        # There is currently a bug in the controlling logic.  Prone players shouldn't be able to block
        return move_actions
    blockable_players: List[m.Player] = game.state.pitch.adjacent_players(player, include_own=False, include_opp=True, manhattan=False, only_blockable=True, only_foulable=False)
    for blockable_player in blockable_players:
        action_steps: List[m.Action] = [
            m.Action(t.ActionType.START_BLOCK, player=player),
            m.Action(t.ActionType.BLOCK, pos=blockable_player.position, player=player),
            m.Action(t.ActionType.END_PLAYER_TURN, player=player)
        ]

        action_score = score_block(game, heat_map, player, blockable_player)
        score = action_score

        move_actions.append(ActionSequence(action_steps, score=score, description='Block ' + player.name + ' to (' + str(blockable_player.position.x) + ',' + str(blockable_player.position.y) + ')'))
        # potential action -> sequence of steps such as "START_MOVE, MOVE (to square) etc
    return move_actions


def potential_blitz_actions(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, paths: List[pf.Path]) -> List[ActionSequence]:
    move_actions: List[ActionSequence] = []
    for path in paths:
        path_steps = path.steps
        end_square: m.Square = game.state.pitch.get_square(path.steps[-1].x, path.steps[-1].y)
        blockable_squares = game.state.pitch.adjacent_player_squares_at(player, end_square, include_own=False, include_opp=True, manhattan=False, only_blockable=True, only_foulable=False)
        for blockable_square in blockable_squares:
            action_steps: List[m.Action] = []
            action_steps.append(m.Action(t.ActionType.START_BLITZ, player=player))
            if not player.state.up:
                action_steps.append(m.Action(t.ActionType.STAND_UP, player=player))
            for step in path_steps:
                # Note we need to add 1 to x and y because the outermost layer of squares is not actually reachable
                action_steps.append(m.Action(t.ActionType.MOVE, pos=game.state.pitch.get_square(step.x, step.y), player=player))
            action_steps.append(m.Action(t.ActionType.BLOCK, pos=blockable_square, player=player))
            # action_steps.append(m.Action(t.ActionType.END_PLAYER_TURN, player=player))

            action_score = score_blitz(game, heat_map, player, end_square, game.state.pitch.get_player_at(blockable_square))
            path_score = path_cost_to_score(path)  # If an extra GFI required for block, should increase here.  To do.
            score = action_score + path_score

            move_actions.append(ActionSequence(action_steps, score=score, description='Blitz ' + player.name + ' to ' + str(blockable_square.x) + ',' + str(blockable_square.y)))
            # potential action -> sequence of steps such as "START_MOVE, MOVE (to square) etc
    return move_actions


def potential_pass_actions(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, paths: List[pf.Path]) -> List[ActionSequence]:
    move_actions: List[ActionSequence] = []
    for path in paths:
        path_steps = path.steps
        end_square: m.Square = game.state.pitch.get_square(path.steps[-1].x, path.steps[-1].y)
        # Need possible receving players
        to_squares, distances = game.state.pitch.passes_at(player, game.state.weather, end_square)
        for to_square in to_squares:
            action_steps: List[m.Action] = []
            action_steps.append(m.Action(t.ActionType.START_PASS, player=player))

            receiver: Optional[m.Player] = game.state.pitch.get_player_at(to_square)

            if not player.state.up:
                action_steps.append(m.Action(t.ActionType.STAND_UP, player=player))
            for step in path_steps:
                # Note we need to add 1 to x and y because the outermost layer of squares is not actually reachable
                action_steps.append(m.Action(t.ActionType.MOVE, pos=game.state.pitch.get_square(step.x, step.y), player=player))
            action_steps.append(m.Action(t.ActionType.PASS, pos=to_square, player=player))
            action_steps.append(m.Action(t.ActionType.END_PLAYER_TURN, player=player))

            action_score = score_pass(game, heat_map, player, end_square, to_square)
            path_score = path_cost_to_score(path)  # If an extra GFI required for block, should increase here.  To do.
            score = action_score + path_score

            move_actions.append(ActionSequence(action_steps, score=score, description='Pass ' + player.name + ' to ' + str(to_square.x) + ',' + str(to_square.y)))
            # potential action -> sequence of steps such as "START_MOVE, MOVE (to square) etc
    return move_actions


def potential_handoff_actions(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, paths: List[pf.Path]) -> List[ActionSequence]:
    move_actions: List[ActionSequence] = []
    for path in paths:
        path_steps = path.steps
        end_square: m.Square = game.state.pitch.get_square(path.steps[-1].x, path.steps[-1].y)
        handoffable_squares = game.state.pitch.adjacent_player_squares_at(player, end_square, include_own=True, include_opp=False, manhattan=False, only_blockable=True, only_foulable=False)
        for handoffable_square in handoffable_squares:
            action_steps: List[m.Action] = []
            action_steps.append(m.Action(t.ActionType.START_HANDOFF, player=player))
            for step in path_steps:
                # Note we need to add 1 to x and y because the outermost layer of squares is not actually reachable
                action_steps.append(m.Action(t.ActionType.MOVE, pos=game.state.pitch.get_square(step.x, step.y), player=player))
            action_steps.append(m.Action(t.ActionType.HANDOFF, pos=handoffable_square, player=player))
            action_steps.append(m.Action(t.ActionType.END_PLAYER_TURN, player=player))

            action_score = score_handoff(game, heat_map, player, game.state.pitch.get_player_at(handoffable_square), end_square)
            path_score = path_cost_to_score(path) # If an extra GFI required for block, should increase here.  To do.
            score = action_score + path_score

            move_actions.append(ActionSequence(action_steps, score=score, description='Handoff ' + player.name + ' to ' + str(handoffable_square.x) + ',' + str(handoffable_square.y)))
            # potential action -> sequence of steps such as "START_MOVE, MOVE (to square) etc
    return move_actions


def potential_foul_actions(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, paths: List[pf.Path]) -> List[ActionSequence]:
    move_actions: List[ActionSequence] = []
    for path in paths:
        path_steps = path.steps
        end_square: m.Square = game.state.pitch.get_square(path.steps[-1].x, path.steps[-1].y)
        foulable_squares = game.state.pitch.adjacent_player_squares_at(player, end_square, include_own=False, include_opp=True, manhattan=False, only_blockable=False, only_foulable=True)
        for foulable_square in foulable_squares:
            action_steps: List[m.Action] = []
            action_steps.append(m.Action(t.ActionType.START_FOUL, player=player))
            if not player.state.up:
                action_steps.append(m.Action(t.ActionType.STAND_UP, player=player))
            for step in path_steps:
                # Note we need to add 1 to x and y because the outermost layer of squares is not actually reachable
                action_steps.append(m.Action(t.ActionType.MOVE, pos=game.state.pitch.get_square(step.x, step.y)))
            action_steps.append(m.Action(t.ActionType.FOUL, foulable_square, player=player))
            action_steps.append(m.Action(t.ActionType.END_PLAYER_TURN, player=player))

            action_score = score_foul(game, heat_map, player, game.state.pitch.get_player_at(foulable_square), end_square)
            path_score = path_cost_to_score(path) # If an extra GFI required for block, should increase here.  To do.
            score = action_score + path_score

            move_actions.append(ActionSequence(action_steps, score=score, description='Foul ' + player.name + ' to ' + str(foulable_square.x) + ',' + str(foulable_square.y)))
            # potential action -> sequence of steps such as "START_MOVE, MOVE (to square) etc
    return move_actions


def potential_move_actions(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, paths: List[pf.Path], is_continuation: bool=False) -> List[ActionSequence]:

    move_actions: List[ActionSequence] = []
    ball_square: m.Square = game.state.pitch.get_ball_position()
    for path in paths:
        path_steps = path.steps
        action_steps: List[m.Action] = []
        if not is_continuation:
            action_steps.append(m.Action(t.ActionType.START_MOVE, player=player))
        if not player.state.up:
            action_steps.append(m.Action(t.ActionType.STAND_UP, player=player))
        for step in path_steps:
            # Note we need to add 1 to x and y because the outermost layer of squares is not actually reachable
            action_steps.append(m.Action(t.ActionType.MOVE, pos=game.state.pitch.get_square(step.x, step.y), player=player))

        to_square: m.Square = game.state.pitch.get_square(path_steps[-1].x, path_steps[-1].y)
        action_score, is_complete, description = score_move(game, heat_map, player, to_square)
        if is_complete:
            action_steps.append(m.Action(t.ActionType.END_PLAYER_TURN, player=player))

        path_score = path_cost_to_score(path)  # If an extra GFI required for block, should increase here.  To do.
        if is_continuation and path_score > 0:
            # Continuing actions (after a Blitz block for example) may choose risky options, so penalise
            path_score = -10 + path_score * 2
        score = action_score + path_score

        move_actions.append(ActionSequence(action_steps, score=score, description='Move: ' + description + ' ' + player.name + ' to ' + str(path_steps[-1].x) + ',' + str(path_steps[-1].y)))
        # potential action -> sequence of steps such as "START_MOVE, MOVE (to square) etc
    return move_actions


def score_blitz(game: g.Game, heat_map: helper.FfHeatMap, attacker: m.Player, block_from_square: m.Square, defender: m.Player) -> float:
    score: float = GrodBot.BASE_SCORE_BLITZ
    num_block_dice: int = game.state.pitch.num_block_dice_at(attacker, defender, block_from_square, blitz=True, dauntless_success=False)
    ball_position: m.Player = game.state.pitch.get_ball_position()
    if num_block_dice == 3: score += 30.0
    if num_block_dice == 2: score += 10.0
    if num_block_dice == 1: score += -30.0
    if num_block_dice == -2: score += -75.0
    if num_block_dice == -3: score += -100.0
    if attacker.has_skill(t.Skill.BLOCK): score += 20.0
    if defender.has_skill(t.Skill.DODGE) and not attacker.has_skill(t.Skill.TACKLE): score -= 10.0
    if defender.has_skill(t.Skill.BLOCK): score += -10.0
    if ball_position == attacker.position:
        if attacker.position.is_adjacent(defender.position) and block_from_square == attacker.position:
            score += 20.0
        else:
            score += -40.0
    if defender.position == ball_position: score += 50.0              # Blitzing ball carrier
    if defender.position.is_adjacent(ball_position): score += 20.0    # Blitzing someone adjacent to ball carrier
    if helper.direct_surf_squares(game, block_from_square, defender.position): score += 25.0  # A surf
    score -= len(game.state.pitch.adjacent_players_at(attacker, defender.position, include_own=False, include_opp=True)) * 5.0
    if attacker.position == block_from_square: score -= 20.0      # A Blitz where the block is the starting square is unattractive
    if helper.in_scoring_range(game, defender): score += 10.0       # Blitzing players closer to the endzone is attractive
    return score


def score_foul(game: g.Game, heat_map: helper.FfHeatMap, attacker: m.Player, defender: m.Player, to_square: m.Square) -> float:
    score = GrodBot.BASE_SCORE_FOUL
    ball_carrier: Optional[m.Player] = game.state.pitch.get_ball_carrier()

    if ball_carrier == attacker: score = score - 30.0
    if attacker.has_skill(t.Skill.DIRTY_PLAYER): score = score + 10.0
    if attacker.has_skill(t.Skill.SNEAKY_GIT): score = score + 10.0
    if defender.state.stunned: score = score - 15.0

    assists_for, assists_against = game.state.pitch.num_assists_at(attacker, defender, to_square, ignore_guard=True)
    score = score + (assists_for-assists_against) * 15.0

    if attacker.team.state.bribes > 0: score += 40.0
    if attacker.has_skill(t.Skill.CHAINSAW): score += 30.0
    # TVdiff = defender.GetBaseTV() - attacker.GetBaseTV()
    tv_diff = 10.0
    score = score + tv_diff

    return score


def score_move(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool, str):

    scores: List[(float, bool, str)] = [
        [*score_receiving_position(game, heat_map, player, to_square), 'move to receiver'],
        [*score_move_towards_ball(game, heat_map, player, to_square), 'move toward ball'],
        [*score_move_to_ball(game, heat_map, player, to_square), 'move to ball'],
        [*score_move_ball(game, heat_map, player, to_square), 'move ball'],
        [*score_sweep(game, heat_map, player, to_square), 'move to sweep'],
        [*score_defensive_screen(game, heat_map, player, to_square), 'move to defensive screen'],
        [*score_offensive_screen(game, heat_map, player, to_square), 'move to offsensive screen'],
        [*score_caging(game, heat_map, player, to_square), 'move to cage'],
        [*score_mark_opponent(game, heat_map, player, to_square), 'move to mark opponent']
        ]

    scores.sort(key=lambda tup: tup[0], reverse=True)
    score, is_complete, description = scores[0]

    # All moves should avoid the sideline
    if helper.distance_to_sideline(game, to_square) == 0: score += GrodBot.ADDITIONAL_SCORE_SIDELINE
    if helper.distance_to_sideline(game, to_square) == 1: score += GrodBot.ADDITIONAL_SCORE_NEAR_SIDELINE

    return score, is_complete, description


def score_receiving_position(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool):
    if player.team != game.state.pitch.get_ball_team() or player == game.state.pitch.get_ball_carrier(): return 0.0, True

    receivingness = player_receiver_ability(game, player)
    score = receivingness - 30.0
    if helper.in_scoring_endzone(game, player.team, to_square):
        num_in_range = len(helper.players_in_scoring_endzone(game, player.team, include_own=True, include_opp=False))
        if player.team.state.turn == 8: score += 40   # Pretty damned urgent to get to end zone!
        score -= num_in_range * num_in_range * 40  # Don't want too many catchers in the endzone ...

    score += 5.0 * (max(helper.distance_to_scoring_endzone(game, player.team, player.position), player.get_ma()) - max(helper.distance_to_scoring_endzone(game, player.team, to_square), player.get_ma()))
    # Above score doesn't push players to go closer than their MA from the endzone.

    if helper.distance_to_scoring_endzone(game, player.team, to_square) > player.get_ma() + 2: score -= 30.0
    opps: List[m.Player] = game.state.pitch.adjacent_players_at(player, to_square, include_own=False, include_opp=True, include_stunned=False)
    if opps: score -= 40.0 + 20.0 * len(opps)
    score -= 10.0 * len(game.state.pitch.adjacent_players_at(player, to_square, include_own=False, include_opp=True))
    num_in_range = len(helper.players_in_scoring_distance(game, player.team, include_own=True, include_opp=False))
    score -= num_in_range * num_in_range * 20.0     # Lower the score if we already have some receivers.
    if helper.players_in(game, player.team, helper.squares_within(game, to_square, 2), include_opp=False, include_own=True): score -= 20.0

    return score, True


def score_move_towards_ball(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square)  -> (float, bool):
    ball_square: m.Square = game.state.pitch.get_ball_position()
    ball_carrier = game.state.pitch.get_ball_carrier()
    ball_team = game.state.pitch.get_ball_team()

    if (to_square == ball_square) or ((ball_team is not None) and (ball_team == player.team)): return 0.0, True

    score = GrodBot.BASE_SCORE_MOVE_TOWARD_BALL
    if ball_carrier is None: score += 20.0

    player_distance_to_ball = ball_square.distance(player.position)
    destination_distance_to_ball = ball_square.distance(to_square)

    score += (player_distance_to_ball - destination_distance_to_ball)

    if destination_distance_to_ball > 3:
        pass
        # score -= 50

    #ma_allowed = player.move_allowed()

    # current_distance_to_ball = ball_square.distance(player.position)

    # Cancel the penalty for being near the sideline if the ball is on the sideline
    # if helper.distance_to_sideline(game, ball_square) <= 1:
    #     if helper.distance_to_sideline(game, to_square): score += 10.0

    # Increase score if moving closer to the ball
    # score += (current_distance_to_ball - distance_to_ball)*2

    return score, True


def score_move_to_ball(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool):
    ball_square: m.Square = game.state.pitch.get_ball_position()
    ball_carrier = game.state.pitch.get_ball_carrier()
    if (ball_square != to_square) or (ball_carrier is not None):
        return 0.0, True

    score = GrodBot.BASE_SCORE_MOVE_TO_BALL
    if player.has_skill(t.Skill.SURE_HANDS) or not player.team.state.reroll_used: score += 15.0
    if player.get_ag() < 2: score += -10.0
    if player.get_ag() == 3: score += 5.0
    if player.get_ag() > 3: score += 10.0
    num_tz = game.state.pitch.num_tackle_zones_at(player, ball_square)
    score += - 10 * num_tz    # Lower score if lots of tackle zones on ball.

    # If there is only 1 or 2 players left to move, lets improve score of trying to pick the ball up
    players_to_move: List[m.Player] = helper.get_players(game, player.team, include_own=True, include_opp=False, include_used=False, include_stunned=False)
    if len(players_to_move) == 1:
        score += 25
    if len(players_to_move) == 2:
        score += 15

    # If the current player is the best player to pick up the ball, increase the score
    players_sorted_blitz = sorted(players_to_move, key=lambda x: player_blitz_ability(game, x), reverse=True)
    if players_sorted_blitz[0] == player:
        score += 9

    # Cancel the penalty for being near the sideline if the ball is on/near the sideline (it's applied later)
    if helper.distance_to_sideline(game, ball_square) == 1: score -= GrodBot.ADDITIONAL_SCORE_NEAR_SIDELINE
    if helper.distance_to_sideline(game, ball_square) == 0: score -= GrodBot.ADDITIONAL_SCORE_SIDELINE

    # Need to increase score if no other player is around to get the ball (to do)

    return score, False


def score_move_ball(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool):
    # ball_square: m.Square = game.state.pitch.get_ball_position()
    ball_carrier = game.state.pitch.get_ball_carrier()
    if (ball_carrier is None) or player != ball_carrier: return 0.0, True

    score = GrodBot.BASE_SCORE_MOVE_BALL
    if helper.in_scoring_endzone(game, player.team, to_square):
        if player.team.state.turn == 8: score += 115.0  # Make overwhelmingly attractive
        else: score += 60.0  # Make scoring attractive
    elif player.team.state.turn == 8: score -= 100.0  # If it's the last turn, heavily penalyse a non-scoring action
    else:
        score += heat_map.get_ball_move_square_safety_score(to_square)
        opps: List[m.Player] = game.state.pitch.adjacent_players_at(player, to_square, include_own=False, include_opp=True, include_stunned=False)
        if opps: score -= (40.0 + 20.0 * len(opps))
        opps_close_to_destination = helper.players_in(game, player.team, helper.squares_within(game, to_square, 2), include_own=False, include_opp=True, include_stunned=False)
        if opps_close_to_destination:
            score -= (20.0 + 5.0 * len(opps_close_to_destination))
        if not helper.blitz_used(game): score -= 30.0  # Lets avoid moving the ball until the Blitz has been used (often helps to free the move).

        dist_player = helper.distance_to_scoring_endzone(game, player.team, player.position)
        dist_destination = helper.distance_to_scoring_endzone(game, player.team, to_square)
        score += 5.0 * (dist_player - dist_destination)  # Increase score the closer we get to the scoring end zone

        # Try to keep the ball central
        if helper.distance_to_sideline(game, to_square) < 3:
            score -= 30

    return score, True


def score_sweep(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool):
    if game.state.pitch.get_ball_team() == player.team: return 0.0, True  # Don't sweep unless the other team has the ball
    if helper.distance_to_defending_endzone(game, player.team, game.state.pitch.get_ball_position()) < 9: return 0.0, True  # Don't sweep when the ball is close to the endzone
    if helper.players_in_scoring_distance(game, player.team, include_own=False, include_opp=True): return 0.0, True  # Don't sweep when there are opponent units in scoring range

    score = GrodBot.BASE_SCORE_MOVE_TO_SWEEP
    blitziness = player_blitz_ability(game, player)
    score += blitziness - 60.0
    score -= 30.0 * len(game.state.pitch.adjacent_player_squares(player, include_own=False, only_blockable=True))

    # Now to evaluate ideal square for Sweeping:

    x_preferred = int(helper.reverse_x_for_left(game, player.team, (game.state.pitch.width-2) / 4))
    y_preferred = int((game.state.pitch.height-2) / 2)
    score -= abs(y_preferred - to_square .y) * 10.0

    # subtract 5 points for every square away from the preferred sweep location.
    score -= abs(x_preferred - to_square .x) * 5.0

    # Check if a player is already sweeping:
    for i in range(-2, 3):
        for j in range(-2, 3):
            cur: m.Square = game.state.pitch.get_square(x_preferred + i, y_preferred + j)
            player: Optional[m.Player] = game.state.pitch.get_player_at(cur)
            if player is not None and player.team == player.team: score -= 90.0

    return score, True


def score_defensive_screen(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool):
    ball_carrier = game.state.pitch.get_ball_carrier()
    ball_square = game.state.pitch.get_ball_position()
    ball_team = game.state.pitch.get_ball_team()

    if ball_team is None or ball_team == player.team: return 0.0, True  # Don't screen if we have the ball or ball is on the ground

    # This one is a bit trickier by nature, because it involves combinations of two or more players...
    #    Increase score if square is close to ball carrier.
    #    Decrease if far away.
    #    Decrease if square is behind ball carrier.
    #    Increase slightly if square is 1 away from sideline.
    #    Decrease if close to a player on the same team WHO IS ALREADY screening.
    #    Increase slightly if most of the players movement must be used to arrive at the screening square.

    score = GrodBot.BASE_SCORE_DEFENSIVE_SCREEN

    distance_ball_carrier_to_end = helper.distance_to_defending_endzone(game, player.team, ball_square)
    distance_square_to_end = helper.distance_to_defending_endzone(game, player.team, to_square)

    if distance_square_to_end + 1.0 < distance_ball_carrier_to_end: score += 30.0  # Increase score defending on correct side of field.

    distance_to_ball = ball_square.distance(to_square)
    score += 4.0*max(5.0 - distance_to_ball, 0.0)  # Increase score defending in front of ball carrier
    score += distance_square_to_end/10.0  # Increase score a small amount to screen closer to opponents.
    distance_to_closest_opponent = helper.distance_to_nearest_player(game, player.team, to_square, include_own=False, include_opp=True, include_stunned=False)
    if distance_to_closest_opponent <= 1.5: score -= 30.0
    elif distance_to_closest_opponent <= 2.95: score += 10.0
    elif distance_to_closest_opponent > 2.95: score += 5.0
    if helper.distance_to_sideline(game, to_square) == 1: score -= GrodBot.ADDITIONAL_SCORE_NEAR_SIDELINE  # Cancel the negative score of being 1 from sideline.

    distance_to_closest_friendly_used = helper.distance_to_nearest_player(game, player.team, to_square, include_own=True, include_opp=False, only_used=True)
    if distance_to_closest_friendly_used >= 4: score += 2.0
    elif distance_to_closest_friendly_used >= 3: score += 40.0  # Increase score if the square links with another friendly (hopefully also screening)
    elif distance_to_closest_friendly_used > 2: score += 10.0   # Descrease score if very close to another defender
    else: score -= 10.0  # Decrease score if too close to another defender.

    distance_to_closest_friendly_unused = helper.distance_to_nearest_player(game, player.team, to_square, include_own=True, include_opp=False, include_used=True)
    if distance_to_closest_friendly_unused >= 4: score += 3.0
    elif distance_to_closest_friendly_unused >= 3: score += 8.0  # Increase score if the square links with another friendly (hopefully also screening)
    elif distance_to_closest_friendly_unused > 2: score += 3.0  # Descrease score if very close to another defender
    else: score -= 10.0  # Decrease score if too close to another defender.

    return score, True


def score_offensive_screen(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool):

    # Another subtle one.  Basically if the ball carrier "breaks out", I want to screen him from
    # behind, rather than cage him.  I may even want to do this with an important receiver.
    #     Want my players to be 2 squares from each other, not counting direct diagonals.
    #     Want my players to be hampering the movement of opponent ball or players.
    #     Want my players in a line between goal line and opponent.
    #

    ball_carrier: m.Player = game.state.pitch.get_ball_carrier()
    ball_square: m.Player = game.state.pitch.get_ball_position()
    if ball_carrier is None or ball_carrier.team != player.team: return 0.0, True

    score = 0.0     # Placeholder - not implemented yet.

    return score, True


def score_caging(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool):
    ball_carrier: m.Player = game.state.pitch.get_ball_carrier()
    if ball_carrier is None or ball_carrier.team != player.team or ball_carrier == player: return 0.0, True          # Noone has the ball.  Don't try to cage.
    ball_square: m.Square = game.state.pitch.get_ball_position()

    cage_square_groups: List[List[m.Square]] = [
        helper.caging_squares_north_east(game, ball_square),
        helper.caging_squares_north_west(game, ball_square),
        helper.caging_squares_south_east(game, ball_square),
        helper.caging_squares_south_west(game, ball_square)
        ]

    dist_opp_to_ball = helper.distance_to_nearest_player(game, player.team, ball_square, include_own=False, include_opp=True, include_stunned=False)
    avg_opp_ma = average_ma(game, helper.get_players(game, player.team, include_own=False, include_opp=True, include_stunned=False))

    for curGroup in cage_square_groups:
        if to_square in curGroup and not helper.players_in(game, player.team, curGroup, include_opp=False, include_own=True, only_blockable=True):
            # Test square is inside the cage corner and no player occupies the corner
            if to_square in curGroup: score = GrodBot.BASE_SCORE_CAGE_BALL
            dist = helper.distance_to_nearest_player(game, player.team, to_square, include_own=False, include_stunned=False, include_opp=True)
            score += dist_opp_to_ball - dist
            if dist_opp_to_ball > avg_opp_ma: score -= 30.0
            if not ball_carrier.state.used: score -= 30.0
            if to_square.is_adjacent(game.state.pitch.get_ball_position()): score += 5
            if helper.is_bishop_position_of(game, player, ball_carrier): score -= 2
            score += heat_map.get_cage_necessity_score(to_square)
            if not ball_carrier.state.used: score = max(0.0, score - GrodBot.BASE_SCORE_CAGE_BALL)  # Penalise forming a cage if ball carrier has yet to move
            if not player.state.up: score += 5.0
            return score, True

    return 0, True


def score_mark_opponent(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player, to_square: m.Square) -> (float, bool):

    # Modification - no need to mark prone opponents already marked

    ball_carrier = game.state.pitch.get_ball_carrier()
    team_with_ball = game.state.pitch.get_ball_team()
    ball_square = game.state.pitch.get_ball_position()
    if ball_square == player.position:
        return 0.0, True  # Don't mark opponents deliberately with the ball
    all_opponents: List[m.Player] = game.state.pitch.adjacent_players_at(player, to_square, include_opp=True, include_own=False)
    if not all_opponents: return 0.0, True

    if (ball_carrier is not None) and (ball_carrier == player):
        return 0.0, True

    score = GrodBot.BASE_SCORE_MOVE_TO_OPPONENT
    if to_square.is_adjacent(game.state.pitch.get_ball_position()):
        if team_with_ball == player.team: score += 20.0
        else: score += 30.0

    for opp in all_opponents:
        if helper.distance_to_scoring_endzone(game, opp.team, to_square) < opp.get_ma() + 2:
            score += 10.0  # Mark opponents in scoring range first.
            break         # Only add score once.

    if len(all_opponents) == 1:
        score += 20.0
        num_friendly_next_to = game.state.pitch.num_tackle_zones_in(all_opponents[0])
        if all_opponents[0].state.up:
            if num_friendly_next_to == 1: score += 5.0
            else: score -= 10.0 * num_friendly_next_to

        if not all_opponents[0].state.up:
            if num_friendly_next_to == 0: score += 5.0
            else: score -= 10.0 * num_friendly_next_to  # Unless we want to start fouling ...

    if not player.state.up: score += 25.0
    if not player.has_skill(t.Skill.GUARD): score -= len(all_opponents) * 10.0
    else: score += len(all_opponents) * 10.0

    ball_is_near = False
    for current_opponent in all_opponents:
        if current_opponent.position.is_adjacent(game.state.pitch.get_ball_position()):
            ball_is_near = True

    if ball_is_near: score += 8.0
    if player.position != to_square and game.state.pitch.num_tackle_zones_in(player) > 0:
        score -= 40.0

    if ball_square is not None:
        distance_to_ball = ball_square.distance(to_square)
        score -= distance_to_ball / 5.0   # Mark opponents closer to ball when possible

    if team_with_ball is not None and team_with_ball != player.team:
        distance_to_other_endzone = helper.distance_to_scoring_endzone(game, player.team, to_square)
        # This way there is a preference for most advanced (distance wise) units.
    return score, True


def score_handoff(game: g.Game, heat_map: helper.FfHeatMap, ball_carrier: m.Player, receiver: m.Player, from_square: m.Square) -> float:
    if receiver == ball_carrier: return 0.0

    score = GrodBot.BASE_SCORE_HANDOFF
    score += probability_fail_to_score(probability_catch_fail(game, receiver))
    if not ball_carrier.team.state.reroll_used: score += +10.0
    score -= 5.0 * (helper.distance_to_scoring_endzone(game, ball_carrier.team, receiver.position) - helper.distance_to_scoring_endzone(game, ball_carrier.team, ball_carrier.position))
    if receiver.state.used: score -= 30.0
    if (game.state.pitch.num_tackle_zones_in(ball_carrier) > 0 or game.state.pitch.num_tackle_zones_in(receiver) > 0) and not helper.blitz_used(game): score -= 50.0  # Don't try a risky hand-off if we haven't blitzed yet
    if helper.in_scoring_range(game, receiver) and not helper.in_scoring_range(game, ball_carrier): score += 40.0
    # score += heat_map.get_ball_move_square_safety_score(receiver.position)
    return score


def score_pass(game: g.Game, heat_map: helper.FfHeatMap, passer: m.Player, from_square: m.Square, to_square: m.Square) -> float:

    receiver = game.state.pitch.get_player_at(to_square)

    if receiver is None: return 0.0
    if receiver.team != passer.team: return 0.0
    if receiver == passer: return 0.0

    score = GrodBot.BASE_SCORE_PASS
    score += probability_fail_to_score(probability_catch_fail(game, receiver))
    dist: t.PassDistance = game.state.pitch.pass_distance(from_square, receiver.position)
    score += probability_fail_to_score(probability_pass_fail(game, passer, from_square, dist))
    if not passer.team.state.reroll_used: score += +10.0
    score = score - 5.0 * (helper.distance_to_scoring_endzone(game, receiver.team, receiver.position) - helper.distance_to_scoring_endzone(game, passer.team, passer.position))
    if receiver.state.used: score -= 30.0
    if game.state.pitch.num_tackle_zones_in(passer) > 0 or game.state.pitch.num_tackle_zones_in(receiver) > 0 and not helper.blitz_used(game): score -= 50.0
    if helper.in_scoring_range(game, receiver) and not helper.in_scoring_range(game, passer): score += 40.0
    return score


def score_block(game: g.Game, heat_map: helper.FfHeatMap, attacker: m.Player, defender: m.Player) -> float:
    score = GrodBot.BASE_SCORE_BLOCK
    ball_carrier = game.state.pitch.get_ball_carrier()
    ball_square = game.state.pitch.get_ball_position()
    if attacker.has_skill(t.Skill.CHAINSAW):
        score += 15.0
        score += 20.0 - 2 * defender.get_av()
        # Add something in case the defender is really valuable?
    else:
        num_block_dice = game.state.pitch.num_block_dice(attacker, defender)
        if num_block_dice == 3: score += 15.0
        if num_block_dice == 2: score += 0.0
        if num_block_dice == 1: score += -66.0  # score is close to zero.
        if num_block_dice == -2: score += -95.0
        if num_block_dice == -3: score += -150.0

        if not attacker.team.state.reroll_used and not attacker.has_skill(t.Skill.LONER): score += 10.0
        if attacker.has_skill(t.Skill.BLOCK) or attacker.has_skill(t.Skill.WRESTLE): score += 20.0
        if defender.has_skill(t.Skill.DODGE) and not attacker.has_skill(t.Skill.TACKLE): score += -10.0
        if defender.has_skill(t.Skill.BLOCK): score += -10.0
        if helper.attacker_would_surf(game, attacker, defender): score += 32.0
        if attacker.has_skill(t.Skill.LONER): score -= 10.0

    if attacker == ball_carrier: score += -45.0
    if defender == ball_carrier: score += 35.0
    if defender.position.is_adjacent(ball_square): score += 15.0

    return score


def score_push(game: g.Game, from_square: m.Square, to_square: m.Square) -> float:
    score = 0.0
    ball_square = game.state.pitch.get_ball_position()
    if helper.distance_to_sideline(game, to_square) == 0: score = score + 10.0    # Push towards sideline
    if ball_square is not None and to_square .is_adjacent(ball_square): score = score - 15.0    # Push away from ball
    if helper.direct_surf_squares(game, from_square, to_square): score = score + 10.0
    return score


def check_follow_up(game: g.Game) -> bool:
        # Check the BlockState - ideally follow up if pushed player is prone, or has ball.  Note the procedure for putting
        # the defender on the ground is not activated yet, so we need to check the stack state to determine the state of
        # the defender.
        active_player: m.Player = game.state.active_player

        block_proc = helper.last_block_proc(game)
        attacker: m.Player = block_proc.attacker
        defender: m.Player = block_proc.defender
        is_blitz_action = block_proc.blitz
        for position in game.state.available_actions[0].positions:
            if active_player.position != position:
                follow_up_square: m.Square = position

        num_tz_cur = game.state.pitch.num_tackle_zones_in(active_player)
        num_tz_new = game.state.pitch.num_tackle_zones_at(active_player, follow_up_square)
        opp_adj_cur = game.state.pitch.adjacent_players(active_player, include_stunned=False, include_own=False, include_opp=True)
        opp_adj_new = game.state.pitch.adjacent_players_at(active_player, follow_up_square, include_stunned=False, include_own=False, include_opp=True)

        # If blitzing (with squares of movement left) always follow up if the new square is not in any tackle zone.
        if is_blitz_action and attacker.move_allowed() > 0 and num_tz_new == 0: return True

        # If Attacker has the ball, strictly follow up only if there are less opponents next to new square.
        if game.state.pitch.get_ball_carrier == attacker:
            if len(opp_adj_new) < len(opp_adj_cur):
                return True
            return False

        if game.state.pitch.get_ball_carrier == defender: return True   # Always follow up if defender has ball
        if helper.distance_to_sideline(game, follow_up_square) == 0: return False    # No if moving to sideline
        if helper.distance_to_sideline(game, defender.position) == 0: return True  # Follow up if opponent is on sideline
        if follow_up_square.is_adjacent(game.state.pitch.get_ball_position()): return True # Follow if moving next to ball
        if attacker.position.is_adjacent(game.state.pitch.get_ball_position()): return False # Don't follow if already next to ball

        # Follow up if less standing opponents in the next square or equivalent, but defender is now prone
        if (num_tz_new==0) or (num_tz_new < num_tz_cur) or (num_tz_new == num_tz_cur and not defender.state.up): return True
        if attacker.has_skill(t.Skill.GUARD) and num_tz_new > num_tz_cur: return True      # Yes if attacker has guard
        if attacker.get_st() > defender.get_st() + num_tz_new - num_tz_cur: return True  # Follow if stronger
        if is_blitz_action and attacker.move_allowed() == 0: return True  # If blitzing but out of moves, follow up to prevent GFIing...

        return False


def check_reroll_block(game: g.Game, team: m.Team, block_results: List[ActionSequence], favor: m.Team) -> bool:
    block_proc: Optional[p.Block] = helper.last_block_proc(game)
    attacker: m.Player = block_proc.attacker
    defender: m.Player = block_proc.defender
    is_blitz_action = block_proc.blitz
    ball_carrier: Optional[m.Player] = game.state.pitch.get_ball_carrier()

    best_block_score: float = 0
    cur_block_score: float = -1

    if len(block_results) > 0:
        best_block_score = block_results[0].score

    if len(block_results) > 1:
        cur_block_score = block_results[1].score
        if favor == team and cur_block_score > best_block_score:
            best_block_score = cur_block_score
        if favor != team and cur_block_score < best_block_score:
            best_block_score = cur_block_score

    if len(block_results) > 2:
        cur_block_score = block_results[2].score
        if favor == team and cur_block_score > best_block_score:
            best_block_score = cur_block_score
        if favor != team and cur_block_score < best_block_score:
            best_block_score = cur_block_score

    if best_block_score < 4: return True
    elif ball_carrier == defender and best_block_score < 5: return True # Reroll if target has ball and not knocked over.
    else: return False


def scoring_urgency_score(game: g.Game, heat_map: helper.FfHeatMap, player: m.Player) -> float:
    if player.team.state.turn == 8: return 40
    return 0


def path_cost_to_score(path: pf.Path) -> float:
    cost: float = path.cost

    # assert 0 <= cost <= 1

    score = -(cost * cost * (250.0 + GrodBot.ADDITIONAL_SCORE_DODGE))
    return score


def probability_fail_to_score(probability: float) -> float:
    score = -(probability * probability * (250.0 + GrodBot.ADDITIONAL_SCORE_DODGE))
    return score


def probability_catch_fail(game: g.Game, receiver: m.Player) -> float:
    num_tz = 0.0
    if not receiver.has_skill(t.Skill.NERVES_OF_STEEL): num_tz = game.state.pitch.num_tackle_zones_in(receiver)
    probability_success = min(5.0, receiver.get_ag()+1.0-num_tz)/6.0
    if receiver.has_skill(t.Skill.CATCH): probability_success += (1.0-probability_success)*probability_success
    probability = 1.0 - probability_success
    return probability


def probability_pass_fail(game: g.Game, passer: m.Player, from_square: m.Square, dist: t.PassDistance) -> float:
    num_tz = 0.0
    if not passer.has_skill(t.Skill.NERVES_OF_STEEL): num_tz = game.state.pitch.num_tackle_zones_at(passer, from_square)
    if passer.has_skill(t.Skill.ACCURATE): num_tz -= 1
    if passer.has_skill(t.Skill.STRONG_ARM and dist != t.PassDistance.QUICK_PASS): num_tz -= 1
    if dist == t.PassDistance.HAIL_MARY: return -100.0
    if dist == t.PassDistance.QUICK_PASS: num_tz -= 1
    if dist == t.PassDistance.SHORT_PASS: num_tz -= 0
    if dist == t.PassDistance.LONG_PASS: num_tz += 1
    if dist == t.PassDistance.LONG_BOMB: num_tz += 2
    probability_success = min(5.0, passer.get_ag()-num_tz)/6.0
    if passer.has_skill(t.Skill.PASS): probability_success += (1.0-probability_success)*probability_success
    probability = 1.0 - probability_success
    return probability


def choose_gaze_victim(game: g.Game, player: m.Player) -> m.Player:
    best_victim: Optional[m.Player] = None
    best_score = 0.0
    ball_square: m.Square = game.state.pitch.get_ball_position()
    potentials: List[m.Player] = game.state.pitch.adjacent_players(player, include_own=False, include_opp=True, only_blockable=True)
    for unit in potentials:
        current_score = 5.0
        current_score += 6.0 - unit.get_ag()
        if unit.position.is_adjacent(ball_square): current_score += 5.0
        if current_score > best_score:
            best_score = current_score
            best_victim = unit
    return best_victim


def average_st(game: g.Game, players: List[m.Player]) -> float:
    values = [player.get_st() for player in players]
    return sum(values)*1.0 / len(values)


def average_av(game: g.Game, players: List[m.Player]) -> float:
    values = [player.get_av() for player in players]
    return sum(values)*1.0 / len(values)


def average_ma(game: g.Game, players: List[m.Player]) -> float:
    values = [player.get_ma() for player in players]
    return sum(values)*1.0 / len(values)


def player_bash_ability(game: g.Game, player: m.Player) -> float:
    bashiness: float = 0.0
    bashiness += 10.0 * player.get_st()
    bashiness += 5.0 * player.get_av()
    if player.has_skill(t.Skill.BLOCK): bashiness += 10.0
    if player.has_skill(t.Skill.WRESTLE): bashiness += 10.0
    if player.has_skill(t.Skill.MIGHTY_BLOW): bashiness += 5.0
    if player.has_skill(t.Skill.CLAWS): bashiness += 5.0
    if player.has_skill(t.Skill.PILING_ON): bashiness += 5.0
    if player.has_skill(t.Skill.GUARD): bashiness += 15.0
    if player.has_skill(t.Skill.DAUNTLESS): bashiness += 10.0
    if player.has_skill(t.Skill.FOUL_APPEARANCE): bashiness += 5.0
    if player.has_skill(t.Skill.TENTACLES): bashiness += 5.0
    if player.has_skill(t.Skill.STUNTY): bashiness -= 10.0
    if player.has_skill(t.Skill.REGENERATION): bashiness += 10.0
    if player.has_skill(t.Skill.THICK_SKULL): bashiness += 3.0
    return bashiness


def team_bash_ability(game: g.Game, players: List[m.Player]) -> float:
    total = 0.0
    for player in players: total += player_bash_ability(game, player)
    return total


def player_pass_ability(game: g.Game, player: m.Player) -> float:
    passing_ability = 0.0
    passing_ability += player.get_ag() * 15.0    # Agility most important.
    passing_ability += player.get_ma() * 2.0     # Fast movements make better ball throwers.
    if player.has_skill(t.Skill.PASS): passing_ability += 10.0
    if player.has_skill(t.Skill.SURE_HANDS): passing_ability += 5.0
    if player.has_skill(t.Skill.EXTRA_ARMS): passing_ability += 3.0
    if player.has_skill(t.Skill.NERVES_OF_STEEL): passing_ability += 3.0
    if player.has_skill(t.Skill.ACCURATE): passing_ability += 5.0
    if player.has_skill(t.Skill.STRONG_ARM): passing_ability += 5.0
    if player.has_skill(t.Skill.BONE_HEAD): passing_ability -= 15.0
    if player.has_skill(t.Skill.REALLY_STUPID): passing_ability -= 15.0
    if player.has_skill(t.Skill.WILD_ANIMAL): passing_ability -= 15.0
    if player.has_skill(t.Skill.ANIMOSITY): passing_ability -= 10.0
    if player.has_skill(t.Skill.LONER): passing_ability -= 15.0
    if player.has_skill(t.Skill.DUMP_OFF): passing_ability += 5.0
    if player.has_skill(t.Skill.SAFE_THROW): passing_ability += 5.0
    if player.has_skill(t.Skill.NO_HANDS): passing_ability -= 100.0
    return passing_ability


def player_blitz_ability(game: g.Game, player: m.Player) -> float:
    blitzing_ability = player_bash_ability(game, player)
    blitzing_ability += player.get_ma() * 10.0
    if player.has_skill(t.Skill.TACKLE): blitzing_ability += 5.0
    if player.has_skill(t.Skill.SPRINT): blitzing_ability += 5.0
    if player.has_skill(t.Skill.SURE_FEET): blitzing_ability += 5.0
    if player.has_skill(t.Skill.STRIP_BALL): blitzing_ability += 5.0
    if player.has_skill(t.Skill.DIVING_TACKLE): blitzing_ability += 5.0
    if player.has_skill(t.Skill.MIGHTY_BLOW): blitzing_ability += 5.0
    if player.has_skill(t.Skill.CLAWS): blitzing_ability += 5.0
    if player.has_skill(t.Skill.PILING_ON): blitzing_ability += 5.0
    if player.has_skill(t.Skill.BONE_HEAD): blitzing_ability -= 15.0
    if player.has_skill(t.Skill.REALLY_STUPID): blitzing_ability -= 15.0
    if player.has_skill(t.Skill.WILD_ANIMAL): blitzing_ability -= 10.0
    if player.has_skill(t.Skill.LONER): blitzing_ability -= 15.0
    if player.has_skill(t.Skill.SIDE_STEP): blitzing_ability += 5.0
    if player.has_skill(t.Skill.JUMP_UP): blitzing_ability += 5.0
    if player.has_skill(t.Skill.HORNS): blitzing_ability += 10.0
    if player.has_skill(t.Skill.JUGGERNAUT): blitzing_ability += 10.0
    if player.has_skill(t.Skill.LEAP): blitzing_ability += 5.0
    return blitzing_ability


def player_receiver_ability(game: g.Game, player: m.Player) -> float:
    receiving_ability = 0.0
    receiving_ability += player.get_ma() * 5.0
    receiving_ability += player.get_ag() * 10.0
    if player.has_skill(t.Skill.CATCH): receiving_ability += 15.0
    if player.has_skill(t.Skill.EXTRA_ARMS): receiving_ability += 10.0
    if player.has_skill(t.Skill.NERVES_OF_STEEL): receiving_ability += 5.0
    if player.has_skill(t.Skill.DIVING_CATCH): receiving_ability += 5.0
    if player.has_skill(t.Skill.DODGE): receiving_ability += 10.0
    if player.has_skill(t.Skill.SIDE_STEP): receiving_ability += 5.0
    if player.has_skill(t.Skill.BONE_HEAD): receiving_ability -= 15.0
    if player.has_skill(t.Skill.REALLY_STUPID): receiving_ability -= 15.0
    if player.has_skill(t.Skill.WILD_ANIMAL): receiving_ability -= 15.0
    if player.has_skill(t.Skill.LONER): receiving_ability -= 15.0
    if player.has_skill(t.Skill.NO_HANDS): receiving_ability -= 100.0
    return receiving_ability


def player_run_ability(game: g.Game, player: m.Player) -> float:
    running_ability = 0.0
    running_ability += player.get_ma() * 10.0    # Really favour fast units
    running_ability += player.get_ag() * 10.0    # Agility to be prized
    running_ability += player.get_st() * 5.0     # Doesn't hurt to be strong!
    if player.has_skill(t.Skill.SURE_HANDS): running_ability += 10.0
    if player.has_skill(t.Skill.BLOCK): running_ability += 10.0
    if player.has_skill(t.Skill.EXTRA_ARMS): running_ability += 5.0
    if player.has_skill(t.Skill.DODGE): running_ability += 10.0
    if player.has_skill(t.Skill.SIDE_STEP): running_ability += 5.0
    if player.has_skill(t.Skill.STAND_FIRM): running_ability += 3.0
    if player.has_skill(t.Skill.BONE_HEAD): running_ability -= 15.0
    if player.has_skill(t.Skill.REALLY_STUPID): running_ability -= 15.0
    if player.has_skill(t.Skill.WILD_ANIMAL): running_ability -= 15.0
    if player.has_skill(t.Skill.LONER): running_ability -= 15.0
    if player.has_skill(t.Skill.ANIMOSITY): running_ability -= 5.0
    if player.has_skill(t.Skill.DUMP_OFF): running_ability += 5.0
    if player.has_skill(t.Skill.NO_HANDS): running_ability -= 100.0
    return running_ability


def player_value(game: g.Game, player: m.Player) -> float:
    value = player.get_ag()*40 + player.get_av()*30 + player.get_ma()*30 + player.get_st()*50 + len(player.skills)*20
    return value


# Register bot
register_bot('GrodBot', GrodBot)


def main():

    import examples.scripted_bot_example

    # Load configurations, rules, arena and teams
    config = api.get_config("ff-11-bot-bowl-i.json")
    ruleset = api.get_rule_set(config.ruleset, all_rules=False)  # We don't need all the rules
    arena = api.get_arena(config.arena)
    home = api.get_team_by_id("human-1", ruleset)
    away = api.get_team_by_id("human-2", ruleset)
    config.competition_mode = False

    # Play 5 games as away
    for i in range(5):
        away_agent = make_bot('grodbot')
        away_agent.name = 'grodbot'
        home_agent = make_bot('scripted')
        home_agent.name = 'scripted'
        config.debug_mode = False
        game = api.Game(i, home, away, home_agent, away_agent, config, arena=arena, ruleset=ruleset)
        game.config.fast_mode = True

        print("Starting game", (i + 1))
        start = time.time()
        game.init()
        end = time.time()
        print(end - start)

    # Play 5 games as home
    for i in range(5):
        away_agent = make_bot('scripted')
        away_agent.name = 'scripted'
        home_agent = make_bot('grodbot')
        home_agent.name = 'grodbot'
        config.debug_mode = False
        game = api.Game(i, home, away, home_agent, away_agent, config, arena=arena, ruleset=ruleset)
        game.config.fast_mode = True

        print("Starting game", (i + 1))
        start = time.time()
        game.init()
        end = time.time()
        print(end - start)



if __name__ == "__main__":
    main()
