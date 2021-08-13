from typing import List, Dict, TYPE_CHECKING, Tuple
import entity_factories
from entity import Entity


max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],
    2: [(entity_factories.confusion_scroll, 10)],
    4: [(entity_factories.lightning_scroll, 25)],
    6: [(entity_factories.fireball_scroll, 25)],
}

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.goblin, 80)],
    3: [(entity_factories.orc, 15)],
    5: [(entity_factories.orc, 30)],
    7: [(entity_factories.orc, 60)],
}
