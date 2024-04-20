import traceback
from abc import ABC
from typing import List

import lugo4py
from settings import get_my_expected_position


class MyBot(lugo4py.Bot, ABC):
    def on_disputing(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        try:

            ball_position = inspector.get_ball().position

            # try the auto complete for reader.make_order_... there are other options
            move_order = inspector.make_order_move_max_speed(ball_position)

            # Try other methods to create Move Orders:
            # move_order = inspector.make_order_move_by_direction(lugo4py.DIRECTION_FORWARD, 100)
            # move_order = reader.make_order_move_from_vector(lugo4py.sub_vector(vector_a, vector_b))

            # we can ALWAYS try to catch the ball
            catch_order = inspector.make_order_catch()

            return [move_order, catch_order]

        except Exception as e:
            print(f'did not play this turn due to exception {e}')
            traceback.print_exc()

    def on_defending(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        try:

            ball_position = inspector.get_ball().position

            if self.shouldIHelp(inspector.get_me(), inspector.get_my_team_players(), ball_position, 3):
                move_dest = ball_position
            else:
                move_dest = get_my_expected_position(inspector, self.mapper, self.number)

            move_order = inspector.make_order_move_max_speed(move_dest)
            # we can ALWAYS try to catch the ball
            catch_order = inspector.make_order_catch()

            return [move_order, catch_order]
        except Exception as e:
            print(f'did not play this turn due to exception {e}')
            traceback.print_exc()

    def on_holding(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        try:

            # "point" is an X and Y raw coordinate referenced by the field, so the side of the field matters!
            # "region" is a mapped area of the field create by your mapper! so the side of the field DO NOT matter!
            opponent_goal_point = self.mapper.get_attack_goal()
            goal_region = self.mapper.get_region_from_point(opponent_goal_point.get_center())
            my_region = self.mapper.get_region_from_point(inspector.get_me().position)

            if self.is_near(my_region, goal_region):
                my_order = inspector.make_order_kick_max_speed(opponent_goal_point.get_center())
            else:
                my_order = inspector.make_order_move_max_speed(opponent_goal_point.get_center())

            return [my_order]

        except Exception as e:
            print(f'did not play this turn due to exception. {e}')
            traceback.print_exc()

    def on_supporting(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        try:
            ball_holder_position = inspector.get_ball().position

            # "point" is an X and Y raw coordinate referenced by the field, so the side of the field matters!
            # "region" is a mapped area of the field create by your mapper! so the side of the field DO NOT matter!
            ball_holder_region = self.mapper.get_region_from_point(ball_holder_position)
            my_region = self.mapper.get_region_from_point(inspector.get_me().position)

            if self.shouldIHelp(inspector.get_me(), inspector.get_my_team_players(), ball_holder_position, 3):
                move_dest = ball_holder_position
            else:
                move_dest = get_my_expected_position(inspector, self.mapper, self.number)

            move_order = inspector.make_order_move_max_speed(move_dest)
            return [move_order]

        except Exception as e:
            print(f'did not play this turn due to exception {e}')
            traceback.print_exc()

    def as_goalkeeper(self, inspector: lugo4py.GameSnapshotInspector, state: lugo4py.PLAYER_STATE) -> List[lugo4py.Order]:
        try:
            position = inspector.get_ball().position

            if state != lugo4py.PLAYER_STATE.DISPUTING_THE_BALL:
                position = self.mapper.get_attack_goal().get_center()

            my_order = inspector.make_order_move_max_speed(position)

            return [my_order, inspector.make_order_catch()]

        except Exception as e:
            print(f'did not play this turn due to exception {e}')
            traceback.print_exc()

    def getting_ready(self, snapshot: lugo4py.GameSnapshot):
        print('getting ready')

    def is_near(self, region_origin: lugo4py.mapper.Region, dest_origin: lugo4py.mapper.Region) -> bool:
        max_distance = 2
        return abs(region_origin.get_row() - dest_origin.get_row()) <= max_distance and abs(
            region_origin.get_col() - dest_origin.get_col()) <= max_distance

    def shouldIHelp(self, me: lugo4py.Player, myTeam: List[lugo4py.Player], targetPosition: lugo4py.Point, maxPlayers: int):
        nearestPlayers = 0
        myDistance = lugo4py.geo.distance_between_points(me.position, targetPosition)
        for teamMate in myTeam:
            if teamMate.number != me.number and lugo4py.geo.distance_between_points(teamMate.position, targetPosition) < myDistance:
                nearestPlayers += 1
                if (nearestPlayers >= maxPlayers):
                    return False
        return True

    def getNearestAlly(self, me: lugo4py.Player, myTeam: List[lugo4py.Player]):
        nearestPlayer = None
        lastDistance = lugo4py.specs.FIELD_WIDTH
        for teamMate in myTeam:
            distanceBetweenMeAndPlayer = lugo4py.geo.distance_between_points(me.position, teamMate.position)
            if distanceBetweenMeAndPlayer < lastDistance and me.number != teamMate.number:
                nearestPlayer = teamMate
            lastDistance = distanceBetweenMeAndPlayer
        return nearestPlayer
    
    def getNearestOpponent(self, me: lugo4py.Player, opponentTeam: List[lugo4py.Player]):
        nearestPlayer = None
        lastDistance = lugo4py.specs.FIELD_WIDTH
        for opponent in opponentTeam:
            distanceBetweenMeAndPlayer = lugo4py.geo.distance_between_points(me.position, opponent.position)
            if distanceBetweenMeAndPlayer < lastDistance:
                nearestPlayer = opponent
            lastDistance = distanceBetweenMeAndPlayer
        return nearestPlayer

    def equalRegion(self, region1: lugo4py.mapper.Region, region2: lugo4py.mapper.Region):
        return region1.col == region2.col and region1.row == region2.row
    
    def getGoalCorner(self, inspector: lugo4py.GameSnapshotInspector):
        goalKeeperPosition = inspector.get_opponent_goalkeeper().position
        goalCenter = self.mapper.get_attack_goal().get_center()

        if (goalKeeperPosition.y >= goalCenter.y):
            return self.mapper.get_attack_goal().get_bottom_pole()
        return self.mapper.get_attack_goal().get_top_pole()

    def holdPosition(self, inspector: lugo4py.GameSnapshotInspector):
        expectedPosition = get_my_expected_position(inspector, self.mapper, self.number)
        return lugo4py.geo.distance_between_points(inspector.get_me().position, expectedPosition) < lugo4py.specs.PLAYER_SIZE