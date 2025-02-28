"""
==========================
Author: Niels Justesen
Year: 2018
==========================
This module contains enumerations and tables for the rules.
"""

from enum import Enum


class Tile(Enum):
    HOME = 1
    HOME_TOUCHDOWN = 2
    HOME_WING_LEFT = 3
    HOME_WING_RIGHT = 4
    HOME_SCRIMMAGE = 5
    AWAY = 6
    AWAY_TOUCHDOWN = 7
    AWAY_WING_LEFT = 8
    AWAY_WING_RIGHT = 9
    AWAY_SCRIMMAGE = 10
    CROWD = 11
    MIDFIELD = 12


class BBDieResult(Enum):
    ATTACKER_DOWN = 1
    BOTH_DOWN = 2
    PUSH = 3
    DEFENDER_STUMBLES = 4
    DEFENDER_DOWN = 5


class RollType(Enum):
    AGILITY_ROLL = 1
    STRENGTH_ROLL = 2
    ARMOR_ROLL = 3
    INJURY_ROLL = 4
    CASUALTY_ROLL = 5
    SCATTER_ROLL = 6
    BOUNCE_ROLL = 7
    THROWN_IN_ROLL = 8
    BLOCK_ROLL = 9
    DISTANCE_ROLL = 10
    WEATHER_ROLL = 11
    KICKOFF_ROLL = 12
    FANS_ROLL = 13
    RIOT_ROLL = 14
    CHEERING_FANS_ROLL = 15
    BRILLIANT_COACHING_ROLL = 16
    THROW_A_ROCK_ROLL = 17
    PITCH_INVASION_ROLL = 19
    GFI_ROLL = 20
    STAND_UP_ROLL = 21
    KO_READY_ROLL = 22
    SWELTERING_HEAT_ROLL = 23


class OutcomeType(Enum):
    HEADS_WON = 1
    HEADS_LOSS = 2
    WEATHER_SWELTERING_HEAT = 3
    WEATHER_VERY_SUNNY = 4
    WEATHER_NICE = 5
    WEATHER_POURING_RAIN = 6
    WEATHER_BLIZZARD = 7
    PLAYER_PLACED = 9
    ILLEGAL_SETUP_NUM = 10
    ILLEGAL_SETUP_SCRIMMAGE = 11
    ILLEGAL_SETUP_WINGS = 12
    BALL_PLACED = 13
    KICKOFF_GET_THE_REF = 14
    KICKOFF_RIOT = 15
    KICKOFF_PERFECT_DEFENSE = 16
    KICKOFF_HIGH_KICK = 17
    KICKOFF_CHEERING_FANS = 18
    KICKOFF_CHANGING_WHEATHER = 19
    KICKOFF_BRILLIANT_COACHING = 20
    KICKOFF_QUICK_SNAP = 21
    KICKOFF_BLITZ = 22
    KICKOFF_THROW_A_ROCK = 23
    KICKOFF_PITCH_INVASION = 24
    EXTRA_BRIBE = 25
    RIOT = 26
    HIGH_KICK = 27
    EXTRA_REROLL = 28
    BRILLIANT_COACHING = 29
    PITCH_INVASION_ROLL = 32
    KICK_IN_BOUNDS = 34
    KICK_OUT_OF_BOUNDS = 35
    BALL_HIT_GROUND = 36
    BALL_HIT_PLAYER = 37
    SETUP_DONE = 38
    KNOCKED_DOWN = 39
    ARMOR_BROKEN = 40
    ARMOR_NOT_BROKEN = 41
    STUNNED = 42
    KNOCKED_OUT = 43
    BADLY_HURT = 44
    INTERCEPTION = 46
    BALL_CAUGhT = 47
    BALL_DROPPED = 48
    FAILED_DODGE = 49
    SUCCESSFUL_DODGE = 50
    FAILED_GFI = 51
    SUCCESSFUL_GFI = 52
    FAILED_PICKUP = 53
    SUCCESSFUL_PICKUP = 54
    HANDOFF = 57
    STUNNED_TURNED = 59
    END_PLAYER_TURN = 60
    MOVE_ACTION_STARTED = 61
    BLOCK_ACTION_STARTED = 62
    BLITZ_ACTION_STARTED = 63
    PASS_ACTION_STARTED = 64
    FOUL_ACTION_STARTED = 65
    HANDOFF_ACTION_STARTED = 66
    END_OF_GAME = 67
    END_OF_PREGAME = 68
    END_OF_TURN = 69
    END_OF_FIRST_HALF = 70
    TOUCHDOWN = 71
    TURNOVER = 72
    CASUALTY = 73
    APOTHECARY_USED_KO = 74
    APOTHECARY_USED_CASUALTY = 75
    CASUALTY_APOTHECARY = 76
    DAUNTLESS_USED = 77
    PUSHED_INTO_CROWD = 78
    PUSHED = 79
    ACCURATE_PASS = 80
    INACCURATE_PASS = 81
    FUMBLE = 82
    CATCH_FAILED = 83
    HOME_RECEIVE = 84
    AWAY_RECEIVE = 85
    TAILS_WON = 86
    TAILS_LOSS = 87
    TOUCHBACK = 88
    BALL_ON_GROUND = 89
    GAME_STARTED = 90
    BALL_SCATTER = 91
    SPECTATORS = 92
    FAME = 93
    KICK_OPP_HALF = 95
    GENTLE_GUST_OUT_OF_BOUNDS = 96
    GENTLE_GUST_IN_BOUNDS = 97
    GENTLE_GUST_OPP_HALF = 98
    END_OF_BLITZ = 99
    END_OF_QUICK_SNAP = 100
    END_OF_SECOND_HALF = 101
    PLAYER_PLACED_HIGH_KICK = 102
    TOUCHBACK_BALL_PLACED = 103
    HIT_BY_ROCK = 104
    TURN_START = 105
    PLAYER_READY = 106
    PLAYER_NOT_READY = 107
    CATCH = 108
    SKILL_USED = 109
    PLAYER_STAND_UP_SUCCESS = 110
    PLAYER_STAND_UP_FAILURE = 111
    BALL_OUT_OF_BOUNDS = 112
    FOLLOW_UP = 113
    FOUL = 114
    PLAYER_EJECTED = 115
    MISS_NEXT_GAME = 116
    DEAD = 117
    REROLL_USED = 118
    BLOCK_ROLL = 119
    INTERCEPTION_FAILED = 120
    TURN_ADDED = 121
    TURN_SKIPPED = 122
    BALL_BOUNCED = 123
    THROW_IN = 124
    THROW_IN_OUT_OF_BOUNDS = 125
    TEAM_SPECTATORS = 126
    CHEERING_FANS_ROLL = 127
    BRILLIANT_COACHING_ROLL = 128
    THROW_A_ROCK_ROLL = 129
    QUICK_SNAP_START = 130
    BLITZ_START = 131
    END_OF_GAME_WINNER = 132
    END_OF_GAME_DRAW = 133
    PLAYER_HEATED = 134
    PLAYER_NOT_HEATED = 135
    END_OF_GAME_DISQUALIFICATION = 136


class PlayerActionType(Enum):
    MOVE = 1
    BLOCK = 2
    BLITZ = 3
    PASS = 4
    HANDOFF = 5
    FOUL = 6


class PhysicalState(Enum):
    NONE = 1
    STUNNED = 5
    KOD = 6
    BH = 7
    MNG = 8
    DEAD = 9
    BONE_HEADED = 10
    HYPNOTIZED = 11
    REALLY_STUPID = 12
    HEATED = 13
    EJECTED = 14


class CasualtyEffect(Enum):
    NONE = 1
    MNG = 2
    NI = 3
    MA = 4
    AV = 5
    AG = 6
    ST = 7
    DEAD = 8


class CasualtyType(Enum):
    """
    D68 Result Effect
    11-38 Badly Hurt No long term effect
    41 Broken Ribs Miss next game
    42 Groin Strain Miss next game
    43 Gouged Eye Miss next game
    44 Broken Jaw Miss next game
    45 Fractured Arm Miss next game
    46 Fractured Leg Miss next game
    47 Smashed Hand Miss next game
    48 Pinched Nerve Miss next game
    51 Damaged Back Niggling Injury
    52 Smashed Knee Niggling Injury
    53 Smashed Hip -1 MA
    54 Smashed Ankle -1 MA
    55 Serious Concussion -1 AV
    56 Fractured Skull -1 AV
    57 Broken Neck -1 AG
    58 Smashed Collar Bone -1 ST
    61-68 DEAD Dead!
    """
    BADLY_HURT = 38
    BROKEN_RIBS = 41
    GROIN_STRAIN = 42
    GOUGED_EYE = 43
    BROKEN_JAW = 44
    FRACTURED_ARM = 45
    FRACTURED_LEG = 46
    SMASHED_HAND = 47
    PINCHED_NERVE = 48
    DAMAGED_BACK = 51
    SMASHED_KNEE = 52
    SMASHED_HIP = 53
    SMASHED_ANKLE = 54
    SERIOUS_CONCUSSION = 55
    FRACTURED_SKULL = 56
    BROKEN_NECK = 57
    SMASHED_COLLAR_BONE = 58
    DEAD = 61


class ActionType(Enum):
    START_GAME = 1
    HEADS = 3
    TAILS = 4
    KICK = 5
    RECEIVE = 6
    PLACE_PLAYER = 7
    END_SETUP = 8
    PLACE_BALL = 9
    START_MOVE = 10
    START_BLOCK = 11
    START_BLITZ = 12
    START_PASS = 13
    START_FOUL = 14
    START_HANDOFF = 15
    END_PLAYER_TURN = 16
    MOVE = 17
    BLOCK = 18
    PASS = 20
    FOUL = 21
    HANDOFF = 22
    USE_REROLL = 24
    END_TURN = 25
    USE_APOTHECARY = 27
    #USE_JUGGERNAUT = 29
    #USE_WRESTLE = 30
    INTERCEPTION = 34
    CONTINUE = 35
    SELECT_PLAYER = 37
    SELECT_NONE = 38
    DONT_USE_APOTHECARY = 40
    DONT_USE_REROLL = 42
    STAND_UP = 43
    PUSH = 44
    SELECT_ATTACKER_DOWN = 46
    SELECT_BOTH_DOWN = 47
    SELECT_PUSH = 48
    SELECT_DEFENDER_STUMBLES = 49
    SELECT_DEFENDER_DOWN = 50
    SETUP_FORMATION_WEDGE = 51
    SETUP_FORMATION_LINE = 52
    SETUP_FORMATION_ZONE = 53
    SETUP_FORMATION_SPREAD = 54
    FOLLOW_UP = 55
    SELECT_FIRST_ROLL = 41
    SELECT_SECOND_ROLL = 42


class WeatherType(Enum):
    SWELTERING_HEAT = 1
    VERY_SUNNY = 2
    NICE = 3
    POURING_RAIN = 4
    BLIZZARD = 5


class SkillCategory(Enum):
    General = 0,
    Agility = 1,
    Strength = 2,
    Passing = 3,
    Mutation = 4,
    Extraordinary = 5


class Skill(Enum):
    THICK_SKULL = 1
    STUNTY = 2
    MIGHTY_BLOW = 3
    CLAWS = 4
    SPRINT = 5
    SURE_FEET = 6
    NO_HANDS = 7
    BALL_AND_CHAIN = 8
    DODGE = 9
    PREHENSILE_TAIL = 10
    TACKLE = 11
    BREAK_TACKLE = 12
    TITCHY = 13
    DIVING_TACKLE = 14
    SHADOWING = 15
    TENTACLES = 16
    TWO_HEADS = 17
    BLOCK = 18
    WRESTLE = 19
    STAND_FIRM = 20
    GUARD = 21
    HORNS = 22
    SIDE_STEP = 23
    FRENZY = 24
    CATCH = 25
    SURE_HANDS = 26
    BIG_HAND = 27
    EXTRA_ARMS = 28
    DIRTY_PLAYER = 29
    SNEAKY_GIT = 30
    STRONG_ARM = 31
    LONG_LEGS = 32
    PASS = 33
    LONER = 34
    WILD_ANIMAL = 35
    RIGHT_STUFF = 36
    ALWAYS_HUNGRY = 37
    REALLY_STUPID = 36
    REGENERATION = 37
    THROW_TEAM_MATE = 38
    BONE_HEAD = 39
    DUMP_OFF = 40
    STAB = 41
    JUMP_UP = 42
    DAUNTLESS = 43
    JUGGERNAUT = 44
    SECRET_WEAPON = 45
    NERVES_OF_STEEL = 46
    BOMBARDIER = 47
    LEAP = 48
    VERY_LONG_LEGS = 49
    CHAINSAW = 50
    TAKE_ROOT = 51
    SAFE_THROW = 52
    DECAY = 53
    DISTURBING_PRESENCE = 54
    NURGLES_ROT = 55
    FOUL_APPEARANCE = 56
    DIVING_CATCH = 57
    BLOOD_LUST = 58
    HYPNOTIC_GAZE = 59
    HAIL_MARY_PASS = 60
    ACCURATE = 61
    KICK = 62
    KICK_OFF_RETURN = 63
    PASS_BLOCK = 64
    FEND = 65
    MULTIPLE_BLOCK = 66
    STRIP_BALL = 67
    GRAB = 68
    STAKES = 69
    ANIMOSITY = 70
    PILING_ON = 71


class PassDistance(Enum):
    QUICK_PASS = 1
    SHORT_PASS = 2
    LONG_PASS = 3
    LONG_BOMB = 4
    HAIL_MARY = 5


class Rules:

    pass_matrix = [
        [0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4],
        [1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4],
        [1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 5],
        [1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5],
        [2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 5],
        [2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 5, 5],
        [2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 5, 5],
        [3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 5, 5, 5],
        [3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5],
        [3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5],
        [3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5],
        [4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5],
        [4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        [4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
    ]

    pass_modifiers = {
        PassDistance.QUICK_PASS: 1,
        PassDistance.SHORT_PASS: 0,
        PassDistance.LONG_PASS: -1,
        PassDistance.LONG_BOMB: -2,
        PassDistance.HAIL_MARY: 0  # Not used??
    }

    casualty_effect = {
        CasualtyType.BADLY_HURT: CasualtyEffect.NONE,
        CasualtyType.BROKEN_RIBS: CasualtyEffect.MNG,
        CasualtyType.GROIN_STRAIN: CasualtyEffect.MNG,
        CasualtyType.GOUGED_EYE: CasualtyEffect.MNG,
        CasualtyType.BROKEN_JAW: CasualtyEffect.MNG,
        CasualtyType.FRACTURED_ARM: CasualtyEffect.MNG,
        CasualtyType.FRACTURED_LEG: CasualtyEffect.MNG,
        CasualtyType.SMASHED_HAND: CasualtyEffect.MNG,
        CasualtyType.PINCHED_NERVE: CasualtyEffect.MNG,
        CasualtyType.DAMAGED_BACK: CasualtyEffect.NI,
        CasualtyType.SMASHED_KNEE: CasualtyEffect.NI,
        CasualtyType.SMASHED_HIP: CasualtyEffect.MA,
        CasualtyType.SMASHED_ANKLE: CasualtyEffect.MA,
        CasualtyType.SERIOUS_CONCUSSION: CasualtyEffect.AV,
        CasualtyType.FRACTURED_SKULL: CasualtyEffect.AV,
        CasualtyType.BROKEN_NECK: CasualtyEffect.AG,
        CasualtyType.SMASHED_COLLAR_BONE: CasualtyEffect.ST,
        CasualtyType.DEAD: CasualtyEffect.DEAD
    }
