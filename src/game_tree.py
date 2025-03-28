import copy

from rich.table import Table
from typing import Generator

from src import config


class PositionNode:
    def __init__(
        self,
        board: list[list[str]],
        to_move: str,
        last_move: tuple[tuple[int, int], tuple[int, int]] = None,
    ):
        self.board: list[list[str]] = board
        self.to_move: str = to_move
        self.children: list[PositionNode] = []
        self.children_positions: list[list[list[str]]] = []
        self.rating: int | float = 0.0
        self.last_move: tuple[tuple[int, int], tuple[int, int]] = last_move

    @property
    def winner(self) -> str:
        count_1, count_2 = 0, 0
        for i in range(5):
            for j in range(5):
                if i + j <= 5:
                    if self.board[i][j] == "1":
                        count_1 += 1
                    if (
                        self.board[config.BOARD_SIZE - 1 - i][
                            config.BOARD_SIZE - 1 - j
                        ]
                        == "2"
                    ):
                        count_2 += 1
        return "1" if count_1 == 19 else "2" if count_2 == 19 else "0"

    @property
    def as_table(self) -> Table:
        table: Table = Table(show_header=False, show_lines=True)
        for i, row in enumerate(self.board):
            new_row: list[str] = []
            for j, x in enumerate(row):
                color: str = config.TEAM_CONFIG[x]["color"]
                x = " " if x == "0" else x
                if self.last_move:
                    color = (
                        "green"
                        if (i, j) == self.last_move[1]
                        else "red" if (i, j) == self.last_move[0] else color
                    )
                    x = "X" if color == "red" else x
                new_row.append(f"[bold {color}]{x}[/]")
            table.add_row(*new_row)
        return table

    def new_position(
        self,
        position: list[list[str]],
        old_x: int,
        old_y: int,
        new_x: int,
        new_y: int,
    ) -> list[list[str]]:
        new_position = copy.deepcopy(position)
        new_position[new_x][new_y] = self.to_move
        new_position[old_x][old_y] = "0"
        return new_position

    def add_new_child(
        self,
        position: list[list[str]],
        old_x: int,
        old_y: int,
        new_x: int,
        new_y: int,
    ) -> "PositionNode":
        new_child = PositionNode(
            position,
            to_move="1" if self.to_move == "2" else "2",
            last_move=((old_x, old_y), (new_x, new_y)),
        )
        self.children.append(new_child)
        self.children_positions.append(position)
        return new_child

    @property
    def new_children(self) -> Generator["PositionNode", None, None]:
        for x in range(config.BOARD_SIZE):
            for y in range(config.BOARD_SIZE):
                if self.board[x][y] == self.to_move:
                    for dx, dy in config.MOVEMENT_VECTORS:
                        new_x, new_y = x + dx, y + dy
                        if (
                            0 <= new_x < config.BOARD_SIZE
                            and 0 <= new_y < config.BOARD_SIZE
                            and self.board[new_x][new_y] == "0"
                        ):
                            new_position = self.new_position(
                                self.board, x, y, new_x, new_y
                            )
                            yield self.add_new_child(
                                new_position, x, y, new_x, new_y
                            )
                    # yield from self.find_jump_move(x, y, self.board)  # TODO: make jumping work

    def find_jump_move(
        self, x: int, y: int, position: list[list[str]]
    ) -> Generator["PositionNode", None, None]:
        for dx, dy in config.MOVEMENT_VECTORS:
            new_x, new_y = x + 2 * dx, y + 2 * dy
            if (
                0 <= new_x < config.BOARD_SIZE
                and 0 <= new_y < config.BOARD_SIZE
                and self.board[x + dx][y + dy] != "0"
                and self.board[new_x][new_y] == "0"
            ):
                new_position = self.new_position(position, x, y, new_x, new_y)
                if new_position not in self.children_positions:
                    yield self.add_new_child(new_position, x, y, new_x, new_y)
                    yield from self.find_jump_move(new_x, new_y, new_position)

    def find_child_with_rating(
        self, rating: int
    ) -> "PositionNode":  # TODO: randomize
        return next(child for child in self.children if child.rating == rating)
