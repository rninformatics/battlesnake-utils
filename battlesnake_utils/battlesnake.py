from typing import Optional, Union

import sys
import copy
import pandas as pd
from time import sleep

class Pos:
    """
    An x,y position, with many helper methods
    """

    all_directions = ['left', 'up', 'right', 'down']
    ascii_for_direction = {'left': '←', 'up': '↑', 'right': '→', 'down': '↓'}

    def __init__(self, x: Union[int, dict], y: int = None):
        """ create from a dictionary with x and y keys, or as named parameters """
        # allow unnamed or named x and y, or a dict
        if isinstance(x, dict):
            if 'x' not in x:
                raise Exception("Pos constructor dict has no 'x' key")
            elif 'y' not in x:
                raise Exception("Pos constructor dict has no 'y' key")
            self.x = x['x']
            self.y = x['y']
        else:
            if y is None:
                raise Exception("Pos constructor: no y value")
            self.x = x
            self.y = y

    def __eq__(self, other):
        """ two points are equal if they have the same x and y """
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return f"({self.x},{self.y})"

    def __hash__(self):
        return hash(self.__str__())

    @classmethod
    def turn_direction_left(cls, direction):
        """ turn left (relative to given direction) """
        i = cls.all_directions.index(direction)
        i = i - 1
        if i < 0:
            i = 3
        return cls.all_directions[i]

    @classmethod
    def turn_direction_right(cls, direction):
        """ turn right (relative to given direction) """
        i = cls.all_directions.index(direction)
        i = i + 1
        if i > 3:
            i = 0
        return cls.all_directions[i]

    def as_dict(self):
        return { 'x': self.x, 'y': self.y }

    def as_tuple(self):
        return self.x, self.y

    def distance_to(self, x: Union[int, dict], y: int = None):
        """ distance to another point """
        # convert dict to x, y
        if isinstance(x, dict):
            y = x['y']
            x = x['x']
        elif isinstance(x, Pos):
            y = x.y
            x = x.x

        dist = ((x - self.x)**2 + (y - self.y)**2)**0.5
        return dist

    def moved_to(self, direction):
        """ return this position moved by 1 in given direction """
        if direction == 'left':
            next_x = self.x - 1
            next_y = self.y
        elif direction == 'right':
            next_x = self.x + 1
            next_y = self.y
        elif direction == 'up':
            next_x = self.x
            next_y = self.y + 1
        elif direction == 'down':
            next_x = self.x
            next_y = self.y - 1
        else:
            raise Exception(f"invalid direction: {direction}")

        return Pos(x=next_x, y=next_y)

    def direction_to(self, other):
        """ return directions(s) to other Pos """
        if self == other:
            return []

        dirs = []
        if self.x < other.x:
            dirs.append('right')
        elif self.x > other.x:
            dirs.append('left')

        if self.y < other.y:
            dirs.append('up')
        elif self.y > other.y:
            dirs.append('down')

        return dirs


class Snake:
    head_char = 'H'
    tail_char = 'T'
    def __init__(self, snake_dict: Optional[dict] = None):
        if snake_dict is None:
            self.id = "0"
            self.name = ""
            self.length = 0
            self.health = 0
            self.body = []
            self.head = None
            self.tail = None
        else:
            self.id = snake_dict['id']
            self.name = snake_dict['name']
            self.length = snake_dict['length']
            self.health = snake_dict['health']
            self.body = []
            for seg in snake_dict['body']:
                self.body.append(Pos(seg))
            self.body_dict = [ pos.as_dict() for pos in self.body ]
            self.head = self.body[0]
            self.tail = self.body[-1]

    def as_dict(self):
        d = {
            'id': self.id,
            'latency': '0',
            'name': self.name,
            'health': self.health,
            'head': self.head.as_dict(),
            'body': self.body_dict,
            'length': self.length,
            'shout': "",
            'squad': "",
            'customizations' : {},
        }
        return d

    def facing_direction(self):
        """ determine which direction this snake is facing """

        # check if just starting a game
        if self.head == self.body[1]:
            # technically None would be a more accurate choice, but I don't want to check for None
            # everytime calling this method
            return 'up'

        direction = self.body[1].direction_to( self.body[0])
        return direction[0]

    def pos_ahead(self):
        """ position in front of head """
        return self.head.moved_to(self.facing_direction())

    def pos_to_right(self):
        """ position to right of head """
        return self.head.moved_to(self.head.turn_direction_right(self.facing_direction()))

    def pos_to_left(self):
        """ position to left of head """
        return self.head.moved_to(self.head.turn_direction_left(self.facing_direction()))

    def pos_ahead_to_right(self):
        """ forward one, right one """
        ahead = self.head.moved_to(self.facing_direction())
        return ahead.moved_to(self.head.turn_direction_right(self.facing_direction()))

    def pos_ahead_to_left(self):
        """ forward one, right one """
        ahead = self.head.moved_to(self.facing_direction())
        return ahead.moved_to(self.head.turn_direction_left(self.facing_direction()))


class Board:
    def __init__(self, board_dict: Optional[dict] = None):
        if board_dict is None:
            self.width = 0
            self.height = 0
            self.snakes = []
            self.food = []
            self.hazards = []
            self.crumbs = []
        else:
            self.width = board_dict['width']
            self.height = board_dict['height']
            self.snakes = []
            self.crumbs = []
            self.food = [ Pos(xy) for xy in board_dict['food'] ]
            self.hazards = [ Pos(xy) for xy in board_dict['hazards'] ]

            if len(board_dict['snakes']) > 0:
                for i in range(len(board_dict['snakes'])):
                    self.snakes.append(Snake(board_dict['snakes'][i]))

        # keep a dataframe representation of this board
        self.update_df()

    def update_df(self):
        " transform board attributes into a dataframe representation "
        df = pd.DataFrame(' ', columns=range(self.width), index=range(self.height))

        if len(self.snakes) > 0:
            # snake positions
            for i in range(len(self.snakes)):
                snake = self.snakes[i]
                body = snake.body
                head = snake.head
                tail = snake.tail
                for j in range(len(body)):
                    x = body[j].x
                    y = body[j].y
                    df.at[y,x] = str(i)   # snake body
                x = head.x
                y = head.y
                df.at[y,x] = Snake.head_char             # snake head
                df.at[tail.y, tail.x] = Snake.tail_char  # snake tail

        if len(self.food) > 0:
            # food
            for i in range(len(self.food)):
                food_piece = self.food[i]
                x = food_piece.x
                y = food_piece.y
                df.at[y,x] = 'f'          # food

        if len(self.hazards) > 0:
            # hazards
            for i in range(len(self.hazards)):
                hazard = self.hazards[i]
                x = hazard.x
                y = hazard.y
                df.at[y,x] = '.'

        if len(self.crumbs) > 0:
            # crumbs
            for i in range(len(self.crumbs)):
                crumb = self.crumbs[i]
                x = crumb.x
                y = crumb.y
                df.at[y,x] = ';'

        self.df = df

    def __str__(self):
        " print out the board with increasing y going up "
        df_reversed = self.df[::-1]
        return( df_reversed.to_string())

    def as_dict(self):
        d = dict()
        d['width'] = self.width
        d['height'] = self.height
        d['hazards'] = [ pos.as_dict() for pos in self.hazards ]
        d['food'] = [ pos.as_dict() for pos in self.food ]
        d['snakes'] = [ snake.as_dict() for snake in self.snakes ]

        return(d)

    def is_free(self, pos: Union[dict, Pos], tails_are_obstructions=False):
        " is given position on the board free (ie not obstructed) ? "

        # accept dict or Pos object
        if isinstance(pos, dict):
            x = pos['x']
            y = pos['y']
        elif isinstance(pos, Pos):
            x = pos.x
            y = pos.y
        else:
            raise Exception(f"is_free: can't handle type: {type(pos)}")

        board_width = self.width
        board_height = self.height

        # not free if off the board
        is_free = None
        if x < 0 or x >= board_width or y < 0 or y >= board_height:
            is_free =  False
            this_spot = "<off board>"
        else:
            this_spot = self.df.at[y,x]
            # note: food is not obstructing
            is_free = this_spot == ' ' or this_spot == 'f' or (not tails_are_obstructions and this_spot == 'T')

        #print(f"pos ({x},{y}) is_free={is_free} cause value is '{this_spot}'")
        return is_free

    def facing_t_choice(self, snake):
        " determine if given snake is facing an obstruction and have choice to turn left or right "
        # FIXME: detect non-square t-choices
        facing_direction = snake.facing_direction()
        turned_left = Pos.turn_direction_left(facing_direction)
        turned_right = Pos.turn_direction_right(facing_direction)
        print(f"snake is facing direction: {facing_direction}")

        ahead_pos = snake.head.moved_to(facing_direction)
        left_pos = snake.head.moved_to(turned_left)
        right_pos = snake.head.moved_to(turned_right)
        ahead_and_left_pos = ahead_pos.moved_to(turned_left)
        ahead_and_right_pos = ahead_pos.moved_to(turned_right)

        ahead_pos_is_free = self.is_free(ahead_pos)
        left_pos_is_free = self.is_free(left_pos)
        right_pos_is_free = self.is_free(right_pos)
        ahead_and_left_pos_is_free = self.is_free(ahead_and_left_pos)
        ahead_and_right_pos_is_free = self.is_free(ahead_and_right_pos)

        if left_pos_is_free and right_pos_is_free and not ahead_pos_is_free:
            return True

        if not ahead_and_left_pos_is_free or not ahead_and_right_pos_is_free:
            return True

        return False

    def free_positions_at(self, pos: Pos, direction):
        " starting from pos and going in given direction, return all the free points "
        free_positions = []
        pos = pos.moved_to(direction)
        while self.is_free(pos, tails_are_obstructions=True):
            free_positions.append(pos)
            pos = pos.moved_to(direction)

        return free_positions


    def unobstructed_between(self, pos1, pos2):
        " whether the path between pos1 and pos2 is unobstructed (not including pos1 and pos2 themselves)"

        # TODO: please optimize this

        # determine if the rectangle formed by these two points is all "free" 
        x1 = min(pos1.x, pos2.x)
        x2 = max(pos1.x, pos2.x)
        y1 = min(pos1.y, pos2.y)
        y2 = max(pos1.y, pos2.y)

        for x in range(x1, x2+1):
            for y in range(y1, y2+1):
                if (x == pos1.x and y == pos1.y) or (x == pos2.x and y == pos2.y):
                    # don't test the actual points given
                    continue
                p = Pos(x,y)
                if not self.is_free(p):
                    return False
                    
        return True


class EmptyBoard (Board):
    def __init__(self, width: int, height: Optional[int] = None):
        if height is None:
            height = width

        board_dict = {
            'width': width,
            'height': height,
            'snakes': [],
            'food': [],
            'hazards': [],
        }
        Board.__init__(self, board_dict)

class Walk():
    " a list of positions, a current position, a current direction "
    def __init__(self, board: Board, pos: Pos, direction = 'up'):
        self.board = board
        self.travelled_points = {pos}
        self.pos = pos
        self.direction = direction
        self.start_pos = None
        self.start_direction = None

    def __str__(self):
        # overlay our travelled points on top of the board
        b2 = copy.deepcopy(self.board)
        for pt in self.travelled_points:
            b2.df.at[pt.y, pt.x] = ';'

        b2.df.at[self.pos.y, self.pos.x] = Pos.ascii_for_direction[self.direction]

        return b2.__str__()

    def perimeter_area(self):
        return len(self.travelled_points)

    def turn_right(self):
        self.direction = Pos.turn_direction_right(self.direction)

    def turn_left(self):
        self.direction = Pos.turn_direction_left(self.direction)

    def free_on_right(self):
        our_right_dir = Pos.turn_direction_right(self.direction)
        return self.board.is_free( self.pos.moved_to(our_right_dir), tails_are_obstructions=True)

    def free_on_left(self):
        our_left_dir = Pos.turn_direction_left(self.direction)
        return self.board.is_free( self.pos.moved_to(our_left_dir), tails_are_obstructions=True)

    def mark_all_points_to_the_right_as_travelled(self):
        our_right_dir = Pos.turn_direction_right(self.direction)
        free_pos = self.board.free_positions_at(self.pos, our_right_dir)
        for p in free_pos:
            self.travelled_points.add(p)
        return free_pos

    def move_forward(self):
        old_pos = self.pos
        self.pos = self.pos.moved_to(self.direction)
        self.travelled_points.add(self.pos)
        self.mark_all_points_to_the_right_as_travelled()
        #print(f"moved forward: {old_pos} -> {self.pos}")

    def turn_right_until_not_obstructed(self):
        n_turns = 0
        while not self.board.is_free( self.pos.moved_to(self.direction), tails_are_obstructions=True) and n_turns < 5:
            self.turn_right()
            n_turns += 1
            #print(f"turned to face: {self.direction}")
        return self.direction

    def walk_until_obstructed(self):
        next_pos = self.pos.moved_to(self.direction)
        while self.board.is_free(next_pos, tails_are_obstructions=True):
            self.move_forward()
            next_pos = self.pos.moved_to(self.direction)
            #print(f"moved {self.direction}")

    def free_space_to_our_left(self):
        our_left_dir = Pos.turn_direction_left(self.direction)
        pos_to_our_left = self.pos.moved_to(our_left_dir)
        return self.board.is_free(pos_to_our_left, tails_are_obstructions=True)

    def walk_until_obstructed_or_free_on_left(self):

        next_pos = self.pos.moved_to(self.direction)
        left_pos = self.pos.moved_to(Pos.turn_direction_left(self.direction))
        while self.board.is_free(next_pos, tails_are_obstructions=True) and not self.board.is_free(left_pos, tails_are_obstructions=True):
            self.move_forward()
            next_pos = self.pos.moved_to(self.direction)
            left_pos = self.pos.moved_to(Pos.turn_direction_left(self.direction))
            #print(f"moved {self.direction}")

            if self.start_pos is not None and self.start_direction is not None and self.pos == self.start_pos and self.direction == self.start_direction:
                #print(f"walk_until_obstructed_or_free_on_left: reached end: {self.pos}/{self.direction}")
                return True

        return False

    def walk_perimeter(self, debug=False, verbose=False):

        self.walk_until_obstructed()
        
        self.turn_right_until_not_obstructed()
        start_direction = self.direction
        self.start_direction = start_direction

        # if still on obstruction, move forward one
        if not self.board.is_free(self.pos):
            print("moving off starting obstruction")
            self.move_forward()

        start_pos = copy.deepcopy(self.pos)
        self.start_pos = start_pos

        # start keeping track of travelled points here
        self.travelled_points = {self.pos}

        if verbose:
            print(f"Begin perimeter walk, start = {self.start_pos},{self.start_direction}:\n{self}")
        if debug:
            input("press enter to continue")

        first_time = True
        n_loops = 0
        while first_time or not (self.pos == start_pos and self.direction == start_direction):

            n_loops += 1
            if n_loops > 40:
                print(f"walk_perimeter: HELP! I think I'm caught in some kind of infinite loop")
                print(f"start_pos: {start_pos}")
                print(f"start_direction: {start_direction}")
                break

            reached_end = self.walk_until_obstructed_or_free_on_left()
            if not first_time and reached_end:
                break

            first_time = False

            if self.free_on_left():
                self.turn_left()
                # test 
                if self.pos == start_pos and self.direction == start_direction:
                    # special case of being done
                    break
                self.move_forward()
            else:
                self.turn_right_until_not_obstructed()

            if len(self.travelled_points) > self.board.width * self.board.height * 4:
                print(f"walk_perimeter: HELP! I think I'm caught in a infinite loop")
                print(f"start_pos: {start_pos}")
                print(f"start_direction: {start_direction}")
                break

            if verbose:
                print(f"{self}")
            if debug:
                input("press enter to continue")

        area = self.perimeter_area()

        if verbose:
            print(f"End perimeter walk:\n{self}")
        return area



class Game():
    def __init__(self, game_dict: Optional[dict] = None):
        if game_dict is None:
            self.turn = 0
            self.board = EmptyBoard(20)
            self.you = Snake( {
                'id'      : '0',
                'name'    : 'snake1',
                'latency' : '0',
                'health'  : 100,
                'body'    : [ { 'x' : 10, 'y' : 10 }, { 'x' : 10, 'y' : 10 }, { 'x' : 10, 'y' : 10 } ],
                'head' : { 'x' : 10, 'y' : 10 },
                'length'         : 3,
                'shout'          : '',
                'squad'          : '',
                'customizations' : { 'color' : '#00ff00', 'head' : 'shark', 'tail' : 'coffee' } }
            )
            self.board.snakes.append(self.you)
            self.board.update_df()
        else:
            self.turn = game_dict['turn']
            self.board = Board(game_dict['board'])
            self.you = Snake(game_dict['you'])

    def __str__(self):
        return(f"\nSnake: {self.you.name, self.you.id}\nTurn: {self.turn}\n" + str(self.board) + "\n")

    def as_dict(self):
        " return game_state dict "
        d = {
            'game' : {
                'id' : '8ca0476c-5c80-4f92-9117-ff914e51f10a',
                'ruleset' : {
                    'name'    : 'solo',
                    'version' : 'cli',
                    'settings' : {
                        'foodSpawnChance'     : 15,
                        'minimumFood'         : 1,
                        'hazardDamagePerTurn' : 14,
                        'hazardMap'           : '',
                        'hazardMapAuthor'     : 'Rick N',
                        'royale'              : { 'shrinkEveryNTurns' : 25 },
                        'squad' : {
                            'allowBodyCollisions' : False,
                            'sharedElimination'   : False,
                            'sharedHealth'        : False,
                            'sharedLength'        : False
                        } }
                },
                'map'     : 'empty map',
                'timeout' : 500,
                'source'  : ''
              },
              'turn' : self.turn,
        }

        d['board'] = self.board.as_dict()
        d['you'] = self.you.as_dict()

        return(d)

    def clone(self, you_id=None):
        " Return copy of this game, optionally changing 'you' "
        game_state = self.as_dict()
        clone = Game(game_state)

        if you_id is not None:
            # change identify of "you" in this game
            target_snake = None
            for snake in clone.board.snakes:
                if snake.id == you_id:
                    target_snake = snake
                    break
            if target_snake is not None:
                clone.you = target_snake
            else:
                print(f"HELP! couldn't find new 'you' snake with id: {you_id}", file=sys.stderr)

        return clone

    def direction_and_distance_to_closest_food(self):
        " return direction(s) to closest food "
        food = self.board.food
        if len(food) == 0:
            return None, None

        my_head = self.you.head

        dists = []
        for i in range(len(food)):
            dist = my_head.distance_to(food[i])
            dists.append(dist)
        sorted_dists = sorted(dists)
        closest = sorted_dists[0]
        wanted_index = dists.index(closest)
        wanted_food = food[wanted_index]

        food_dirs = []
        if my_head.x < wanted_food.x:
            food_dirs.append('right')
        elif my_head.x > wanted_food.x:
            food_dirs.append('left')

        if my_head.y < wanted_food.y:
            food_dirs.append('up')
        elif my_head.y > wanted_food.y:
            food_dirs.append('down')

        return food_dirs, closest

    def direction_and_distance_to_closest_unobstructed_food(self):
        " return direction(s) and distance to closest, unobstructed food "
        food = self.board.food
        if len(food) == 0:
            return None, None

        my_head = self.you.head

        # filter out obstructed ones
        food = [ x for x in food if self.board.unobstructed_between(my_head, x) ]
        if len(food) == 0:
            return None, None

        dists = []
        for i in range(len(food)):
            dist = my_head.distance_to(food[i])
            dists.append(dist)
        sorted_dists = sorted(dists)

        closest = sorted_dists[0]
        wanted_index = dists.index(closest)
        wanted_food = food[wanted_index]

        dists = []
        for i in range(len(food)):
            dist = my_head.distance_to(food[i])
            dists.append(dist)
        sorted_dists = sorted(dists)
        closest = sorted_dists[0]
        wanted_index = dists.index(closest)
        wanted_food = food[wanted_index]

        food_dirs = []
        if my_head.x < wanted_food.x:
            food_dirs.append('right')
        elif my_head.x > wanted_food.x:
            food_dirs.append('left')

        if my_head.y < wanted_food.y:
            food_dirs.append('up')
        elif my_head.y > wanted_food.y:
            food_dirs.append('down')

        return food_dirs, closest


    def towards_dead_end(self, direction):
        " are you facing a dead end ?"

        board_width = self.board.width
        board_height = self.board.height

        # board without food
        board_df = self.board.df.replace(['f'], ' ')

        # position of our head + move in direction
        new_head = self.you.head.moved_to(direction)
        move_x = new_head.x
        move_y = new_head.y

        print(f"board_width = {board_width}")
        print(f"board_height = {board_height}")
        print(f"move_x = {move_x}")
        print(f"move_y = {move_y}")
        print(f"head = {self.you.head}")
        print(f"tail = {self.you.tail}")

        no_moves = True
        dead_end = False

        # if we get to an open spot, then not a dead end
        while move_x >= 0 and move_x < board_width and move_y >= 0 and move_y < board_height and (self.board.is_free({'x':move_x, 'y':move_y}) or (move_x == self.you.head.x and move_y == self.you.head.y)):

            no_moves = False

            # four positions around (move_x,move_y)
            # north is always up
            north_pos = {'x': move_x, 'y': move_y+1}
            south_pos = {'x': move_x, 'y': move_y-1}
            east_pos = {'x': move_x+1, 'y': move_y}
            west_pos = {'x': move_x-1, 'y': move_y}

            if direction == 'right':
                side_positions = [ north_pos, south_pos ]
                ahead_position = east_pos
                next_x = move_x + 1
                next_y = move_y
            elif direction == 'left':
                side_positions = [ north_pos, south_pos ]
                ahead_position = west_pos
                next_x = move_x - 1
                next_y = move_y
            elif direction == 'up':
                side_positions = [ west_pos, east_pos ]
                ahead_position = north_pos
                next_x = move_x
                next_y = move_y + 1
            else: # down
                side_positions = [ west_pos, east_pos ]
                ahead_position = south_pos
                next_x = move_x
                next_y = move_y - 1

            print(f"ahead_position = {ahead_position}")
            print(f"side positions = {side_positions}")

            pos_is_free = []
            pos_is_free.append( self.board.is_free(ahead_position))
            pos_is_free.append( self.board.is_free(side_positions[0]))
            pos_is_free.append( self.board.is_free(side_positions[1]))
            print(f"are those positions free: {pos_is_free}")
            num_free = sum(pos_is_free)

            if num_free == 0:
                # if all positions aren't free, then dead end
                print(f"no positions free, dead end, break")
                dead_end = True
                break
            elif num_free >= 2:
                # if two or more positions free, not a dead end?
                dead_end = False
                print(f"two or more positions free, not dead end, break")
                break
            else:
                # only one position free, then keep going (may end up dead end)
                print(f"one position free, keep looking")

            move_x = next_x
            move_y = next_y

        
        if no_moves:
            dead_end = True

        print(f"returning dead_end = {dead_end}")

        return dead_end


