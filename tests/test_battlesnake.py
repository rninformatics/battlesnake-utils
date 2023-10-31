import pytest
import pandas as pd

import arcade_board
import battlesnake_utils.battlesnake as bs

def test_board():

    # empty board
    b = bs.Board()
    assert isinstance(b, bs.Board)
    assert b.width == 0
    assert b.height == 0

    d = b.as_dict()
    assert isinstance(d, dict)

    # arcade board
    arcade_board_data = arcade_board.board_data()
    b = bs.Board(arcade_board_data)
    assert isinstance(b, bs.Board)
    assert b.width == 19
    assert b.height == 21
    print(b)

    assert isinstance(b.df, pd.DataFrame)

    assert b.facing_t_choice(b.snakes[0]) == True

    # move snake to the right
    b.snakes[0].head.x = 17
    b.snakes[0].head.y = 17
    b.snakes[0].body[0] = b.snakes[0].head
    b.snakes[0].body[1].x = 16
    b.snakes[0].body[1].y = 17
    b.snakes[0].body[2].x = 15
    b.snakes[0].body[2].y = 17
    b.update_df()
    print(b)
    assert b.facing_t_choice(b.snakes[0]) == True

    # move snake to another position
    b.snakes[0].head.x = 14
    b.snakes[0].head.y = 15
    b.snakes[0].body[0] = b.snakes[0].head
    b.snakes[0].body[1].x = 14
    b.snakes[0].body[1].y = 16
    b.snakes[0].body[2].x = 14
    b.snakes[0].body[2].y = 17
    b.update_df()
    print(b)
    assert b.facing_t_choice(b.snakes[0]) == True

    p1 = bs.Pos(1,7)
    p2 = bs.Pos(2,8)
    assert b.unobstructed_between(p1, p2)

    p1 = bs.Pos(1,7)
    p2 = bs.Pos(2,7)
    assert b.unobstructed_between(p1, p2)

    p1 = bs.Pos(8,7)
    p2 = bs.Pos(10,7)
    assert not b.unobstructed_between(p1, p2)


def test_empty_board():
    eb = bs.EmptyBoard(3)
    assert isinstance(eb, bs.Board)

    assert eb.width == 3 and eb.height == 3
    for i in range(eb.width):
        assert eb.is_free( {'x': i, 'y': i} )

    assert not eb.is_free( {'x': eb.width, 'y': eb.height} )

    eb.df.at[0,0] = 'x'
    assert not eb.is_free( {'x': 0, 'y': 0} )

def test_board_methods():
    b = bs.Board()

    # all positions aren't free for zero-size board
    assert not b.is_free({'x': 0, 'y': 0})
    assert not b.is_free({'x': 100, 'y': 100})

    # board with hazard at 1,1
    b = bs.EmptyBoard(3)
    b.hazards.append(bs.Pos(x=1,y=1))
    b.update_df()
    assert b.is_free({'x': 0, 'y': 0})
    assert b.is_free({'x': 2, 'y': 2})
    assert not b.is_free({'x': 1, 'y': 1})

def test_turns():
    assert bs.Pos.turn_direction_left('up')  == 'left'
    assert bs.Pos.turn_direction_left('left')  == 'down'
    assert bs.Pos.turn_direction_left('down')  == 'right'
    assert bs.Pos.turn_direction_left('right')  == 'up'

    assert bs.Pos.turn_direction_right('up')  == 'right'
    assert bs.Pos.turn_direction_right('right')  == 'down'
    assert bs.Pos.turn_direction_right('down')  == 'left'
    assert bs.Pos.turn_direction_right('left')  == 'up'

def test_pos():

    # test different constuctors
    p = bs.Pos(x=0,y=1)
    assert p.x == 0 and p.y == 1

    p = bs.Pos(1,2)
    assert p.x == 1 and p.y == 2

    p = bs.Pos({'x': 3, 'y': 4})
    assert p.x == 3 and p.y == 4

    # conversion
    d = p.as_dict()
    assert isinstance(d, dict)
    assert d['x'] == p.x and d['y'] == p.y

    # distance to another point
    p = bs.Pos(0,0)
    assert p.distance_to(3,4) == 5
    assert p.distance_to(1,1) == 2**0.5
    assert p.distance_to(bs.Pos(1,1)) == 2**0.5

    # moving a point
    new_p = p.moved_to('right')
    assert new_p.x == 1 and new_p.y == 0

    new_p = p.moved_to('left')
    assert new_p.x == -1 and new_p.y == 0

    new_p = p.moved_to('up')
    assert new_p.x == 0 and new_p.y == 1

    new_p = p.moved_to('down')
    assert new_p.x == 0 and new_p.y == -1

    # direction to another point
    for d in p.all_directions:
        dirs = p.direction_to( p.moved_to(d))
        assert len(dirs) == 1 and d in dirs

    dirs = p.direction_to( bs.Pos(p.x+1, p.y+1) )
    assert len(dirs) == 2 and 'right' in dirs and 'up' in dirs
    dirs = p.direction_to( bs.Pos(p.x+1, p.y-1) )
    assert len(dirs) == 2 and 'right' in dirs and 'down' in dirs
    dirs = p.direction_to( bs.Pos(p.x-1, p.y-1) )
    assert len(dirs) == 2 and 'left' in dirs and 'down' in dirs
    dirs = p.direction_to( bs.Pos(p.x-1, p.y+1) )
    assert len(dirs) == 2 and 'left' in dirs and 'up' in dirs

    # point equivalence
    p1 = bs.Pos(0,0)
    p2 = bs.Pos(0,0)
    assert p1 == p2

def test_snake():
    s = bs.Snake()
    assert isinstance(s, bs.Snake)
    assert s.length == 0

    #s = board.Snake(
    sd =         {
                'id'      : '5dba42ff-6611-4233-a16f-cdbd2a70c0f3',
                'name'    : 'snake1',
                'latency' : '0',
                'health'  : 100,
                'body'    : [ { 'x' : 14, 'y' : 17 }, { 'x' : 14, 'y' : 17 }, { 'x' : 14, 'y' : 17 } ],
                'head' : { 'x' : 14, 'y' : 17 },
                'length'         : 3,
                'shout'          : '',
                'squad'          : '',
                'customizations' : { 'color' : '#00ff00', 'head' : 'caffeine', 'tail' : 'coffee' } 
             }

    s = bs.Snake(sd)

    assert s.length == 3
    assert s.name == "snake1"
    assert s.health == 100
    assert s.body[0].x == 14
    assert s.body[0].y == 17

    assert s.facing_direction() == 'up'

    s.body[1].x = 14
    s.body[1].y = 16
    s.body[2].x = 14
    s.body[2].y = 15
    assert s.pos_ahead() == bs.Pos(14, 18)
    assert s.pos_to_left() == bs.Pos(13, 17)
    assert s.pos_to_right() == bs.Pos(15, 17)
    assert s.pos_ahead_to_right() == bs.Pos(15, 18)
    assert s.pos_ahead_to_left() == bs.Pos(13, 18)

def test_game():
    g = bs.Game();
    assert isinstance(g, bs.Game)
    assert isinstance(g.you, bs.Snake)
    assert isinstance(g.board, bs.Board)
    assert g.turn == 0
    assert g.board.width == 20 and g.board.height == 20
    assert g.you.length == 3
    assert g.you.head.x == 10 and g.you.head.y == 10
    assert len(g.board.snakes) == 1
    assert len(g.board.snakes[0].body) == 3
    assert g.board.snakes[0].body[0].x == 10

    # convert game object to game state dict
    game_state = g.as_dict()
    assert isinstance(game_state, dict)

    # ensure we can create a game object 
    # from a game state dict we created
    g2 = bs.Game(game_state)
    assert isinstance(g2, bs.Game)

    # direction to closest food
    g = bs.Game() 

    # no food returns None
    food_dirs, food_dist = g.direction_and_distance_to_closest_unobstructed_food()
    assert food_dirs is None and food_dist is None

    # food to upper, right
    g.board.food.append(bs.Pos(12,12))
    g.board.update_df()
    print(f"\n{g.board}")
    food_dirs, food_dist = g.direction_and_distance_to_closest_unobstructed_food()
    assert len(food_dirs) == 2 and 'up' in food_dirs and 'right' in food_dirs
    assert food_dist == 8**0.5

    # obstruction between us and food
    g.board.hazards.append(bs.Pos(11,11))
    g.board.update_df()
    food_dirs, food_dist = g.direction_and_distance_to_closest_unobstructed_food()
    assert food_dirs is None

    return

    # all directions should not be towards dead end
    for d in ['left', 'right', 'up', 'down']:
        assert g.towards_dead_end(d) == False

    # after we put hazards all around us
    # all directions should be towards dead end
    g.board.hazards.append(bs.Pos(10, 11))
    g.board.hazards.append(bs.Pos(11, 10))
    g.board.hazards.append(bs.Pos(9, 10))
    g.board.hazards.append(bs.Pos(10, 9))
    g.board.update_df()
    for d in ['left', 'right', 'up', 'down']:
        assert g.towards_dead_end(d) == True

    # create a copy of a game
    clone_g = g.clone()
    assert isinstance(clone_g, bs.Game)

    # make sure this game is independent of original game
    clone_g.turn = 1
    assert clone_g.turn != g.turn


import game_state_deadend2 as gs2
def test_game_clone():
    game_state = gs2.game_state()
    g = bs.Game(game_state)
    assert isinstance(g, bs.Game)

    new_snake_id = "gs_d8F9m6wbHtMFqyggdBFwVQTK"
    clone_g = g.clone(you_id=new_snake_id)
    # old you: gs_JDvdxKtfdkFrC7rctDMmYSpT
    # new you: gs_d8F9m6wbHtMFqyggdBFwVQTK
    assert isinstance(clone_g, bs.Game)
    assert clone_g.you.id == new_snake_id


#    print("=========")
#    print(g)
#
#    assert g.towards_dead_end('up') == True
#    assert g.towards_dead_end('left') == False
#    assert g.towards_dead_end('right') == True
#    assert g.towards_dead_end('down') == False

import game_state_deadend3 as gs3
def test_deadend_situation3():
    " moving down should't be dead end cause tail shouldn't be considered an obstruction (it will move out of our way) "
    game_state = gs3.game_state()
    g = bs.Game(game_state)
    assert isinstance(g, bs.Game)
    print("=========")
    print(g)
    assert g.towards_dead_end('down') == False


def test_walk():
    game_state = gs3.game_state()
    g = bs.Game(game_state)
    w = bs.Walk(g.board, bs.Pos(0,0), "down")
    assert isinstance(w, bs.Walk)

    direction = w.turn_right_until_not_obstructed()
    assert direction == 'up'
    assert not w.free_on_left()
    assert w.free_on_right()

    pos = w.walk_until_obstructed()
    assert not w.free_space_to_our_left()

    w.turn_right()
    assert not w.free_space_to_our_left()

    w.turn_right()
    assert w.free_space_to_our_left()

    w.turn_left()
    w.walk_until_obstructed_or_free_on_left()

    w.turn_right_until_not_obstructed()
    w.walk_until_obstructed_or_free_on_left()
    assert w.pos == bs.Pos(4,6)
    print(f"{w}")

    w.walk_perimeter(verbose=True, debug=False)
    print(f"{w}")
    assert w.perimeter_area() == 90

    assert len(w.board.free_positions_at(bs.Pos(0,0), 'down')) == 0
    assert len(w.board.free_positions_at(bs.Pos(0,0), 'left')) == 0
    assert len(w.board.free_positions_at(bs.Pos(0,0), 'right')) == 10
    assert len(w.board.free_positions_at(bs.Pos(0,0), 'up')) == 10
    assert len(w.board.free_positions_at(bs.Pos(0,10), 'right')) == 4


    g = bs.Game(game_state)
    w = bs.Walk(g.board, bs.Pos(0,0), "up")
    w.mark_all_points_to_the_right_as_travelled()
    print(w)


import game_state_deadend4 as gs4
def test_deadend_situation4():
    " t-choice with only 1 space free in one choice "
    game_state = gs4.game_state()
    g = bs.Game(game_state)
    assert isinstance(g, bs.Game)
    print("=========")
    print(g)
    w = bs.Walk(g.board, bs.Pos(10,8), "right")
    w.walk_perimeter(verbose=True, debug=False)
    print(w)

import game_state_deadend5 as gs5
def test_deadend_situation5():
    " t-choice with only 1 space free in one choice "
    game_state = gs5.game_state()
    g = bs.Game(game_state)
    assert isinstance(g, bs.Game)
    print("=========")
    print(g)
    w = bs.Walk(g.board, bs.Pos(7,8), "up")
    w.walk_perimeter(verbose=True, debug=False)
    print(w)
    a = w.perimeter_area()
    print(f"area = {a}")

import game_state_deadend6 as gs6
def test_deadend_situation6():
    " t-choice with only 1 space free in one choice "
    game_state = gs6.game_state()
    g = bs.Game(game_state)
    assert isinstance(g, bs.Game)
    print("=========")
    print(g)
