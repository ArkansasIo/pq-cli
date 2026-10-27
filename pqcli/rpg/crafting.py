from dataclasses import dataclass, field


@dataclass(frozen=True)
class Material:
    id: str
    name: str
    value: int = 0


@dataclass(frozen=True)
class Recipe:
    id: str
    name: str
    profession: str
    level: int
    ingredients: dict[str, int]
    output_item: str
    output_quantity: int = 1


@dataclass
class CraftingBook:
    recipes: dict[str, Recipe] = field(default_factory=dict)
    profession_levels: dict[str, int] = field(default_factory=dict)

    def learn(self, recipe: Recipe) -> None:
        self.recipes[recipe.id] = recipe

    def can_craft(self, recipe_id: str, inventory_counts: dict[str, int]) -> bool:
        recipe = self.recipes[recipe_id]
        if self.profession_levels.get(recipe.profession, 0) < recipe.level:
            return False
        return all(inventory_counts.get(item, 0) >= qty for item, qty in recipe.ingredients.items())
