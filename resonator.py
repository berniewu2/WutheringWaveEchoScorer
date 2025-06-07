from data import damage_composition


class Property:
    def __init__(self, data: dict):
        self.data: dict = data
        self.score: float = 0.0

    def set_score(self, score: float):
        self.score = score
        return self

    def __str__(self):
        return f"{self.data['property']}: {self.data['value']}"

    __repr__ = __str__


class Echo:
    def __init__(
        self, main_attribute: dict, sub_attribute: dict, cost: int, score: float, property_list: list[Property]
    ):
        self.main_attribute: dict = main_attribute
        self.sub_attribute: dict = sub_attribute
        self.cost: int = cost
        self.score: float = score
        self.property_list: list[Property] = property_list

    def set_score(self, score: float):
        self.score = score
        return self

    def to_dict(self) -> dict:
        return {
            "cost": self.cost,
            "score": self.score,
            "main_attribute": self.main_attribute,
            "sub_attribute": self.sub_attribute,
            "propertyList": [p.data for p in self.property_list],
        }

    def __str__(self):
        return (
            "Echo(\n"
            f"  cost:           {self.cost},\n"
            f"  score:          {self.score},\n"
            f"  main_attribute: {self.main_attribute!r},"
            f"  sub_attribute:  {self.sub_attribute!r},\n"
            f"  property_list:  {[p.data for p in self.property_list]}\n"
            ")"
        )

    __repr__ = __str__


class EchoBuilder:
    def __init__(self):
        self._main_attribute: Property = None
        self._sub_attribute: Property = None
        self._cost = 0
        self._score = 0.0
        self._property_list = []

    def set_main_attribute(self, main_attribute: Property):
        self._main_attribute = main_attribute
        return self

    def set_sub_attributes(self, sub_attributes: Property):
        self._sub_attribute = sub_attributes
        return self

    def set_cost(self, cost: int):
        self._cost = cost
        return self

    def set_score(self, score: float):
        self._score = score
        return self

    def add_property(self, prop: Property):
        self._property_list.append(prop)
        return self

    def with_properties(self, props: list[Property]):
        self._property_list = list(props)
        return self

    def build(self) -> Echo:
        if self._main_attribute is None:
            raise ValueError("main_attribute must be set via with_main_attribute(...) before build()")

        echo = Echo(
            main_attribute=self._main_attribute,
            sub_attribute=self._sub_attribute,
            cost=self._cost,
            score=self._score,
            property_list=list(self._property_list),
        )
        return echo


class Resonator:
    def __init__(self, name: str, echo_list: list[Echo]):
        self.name: str = name
        self.score: float = 0.0
        self.energy_regen: float = 0.0
        self.echo_list: list[Echo] = echo_list
        self.weight: dict = None
        self.perfect_score: float = damage_composition[self.name]["score_needed"]

    def set_weight(self, weight: dict):
        self.weight = weight
        return self

    def set_score(self):
        score = 0
        for echo in self.echo_list:
            score += echo.score
        if self.energy_regen > self.weight["Energy Regen"][0]:
            score -= (self.energy_regen - self.weight["Energy Regen"][0]) * (
                self.weight["Energy Regen"][1] - self.weight["Energy Regen"][2]
            )
        self.score = score
        return self

    def add_energy_regen(self, energy_regen: float):
        self.energy_regen += energy_regen
        return self

    def __str__(self):
        if self.echo_list:
            arts = "\n".join(f"    - {a!r}" for a in self.echo_list)
            echos_block = f"\n  echos:\n{arts}\n"
        else:
            echos_block = "  echos: []\n"

        return (
            "Resonator(\n"
            f"  name:          {self.name!r},\n"
            f"  score:         {self.score},"
            f"{echos_block}"
            ")"
        )
