#!/usr/bin/env python3
from map_builders import SimpleMapBuilder
import tcod
import copy
import color

from engine import Engine
import entity_factories


def main():
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 43

    max_monsters_room = 2

    tileset = tcod.tileset.load_tilesheet(
        "resources/dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD)

    player = copy.deepcopy(entity_factories.player)
    engine = Engine(player=player)

    builder = SimpleMapBuilder(max_rooms=30,
                               room_min_size=6,
                               room_max_size=10,
                               map_width=map_width,
                               map_height=map_height,
                               max_monsters_room=max_monsters_room,
                               engine=engine,
                               )

    engine.game_map = builder.build()
    engine.update_fov()

    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )

    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Crown of Vorona",
        vsync=True
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")

        while True:
            root_console.clear()
            engine.event_handler.on_render(console=root_console)
            context.present(root_console)

            engine.event_handler.handle_events(context)


if __name__ == "__main__":
    main()
