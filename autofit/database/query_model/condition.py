from abc import ABC, abstractmethod

from autofit.database import get_class_path


class Table:
    def __init__(self, name):
        self.name = name

    @property
    def abbreviation(self):
        return self.name[0]

    def __str__(self):
        return f"{self.name} AS {self.abbreviation}"


object_table = Table("object")
value_table = Table("value")


class AbstractCondition(ABC):
    @property
    @abstractmethod
    def tables(self):
        pass

    @property
    def tables_string(self):
        return ", ".join(sorted(map(str, self.tables)))

    @abstractmethod
    def __str__(self):
        pass

    def __and__(self, other):
        return And(
            self,
            other
        )

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __gt__(self, other):
        return str(self) > str(other)

    def __lt__(self, other):
        return str(self) < str(other)


class ValueCondition(AbstractCondition):
    def __init__(self, symbol, value):
        self.value = value
        self.symbol = symbol

    @property
    def tables(self):
        return {value_table}

    def __str__(self):
        return f"{value_table.abbreviation}.value {self.symbol} {self.value}"


class NameCondition(AbstractCondition):
    def __init__(self, name):
        self.name = name

    @property
    def tables(self):
        return {object_table}

    def __str__(self):
        return f"{object_table.abbreviation}.name = '{self.name}'"


class TypeCondition(AbstractCondition):
    def __init__(self, cls):
        self.cls = cls

    @property
    def tables(self):
        return {object_table}

    @property
    def class_path(self):
        return get_class_path(
            self.cls
        )

    def __str__(self):
        return f"{object_table.abbreviation}.class_path = '{self.class_path}'"


class And(AbstractCondition):
    def __init__(
            self,
            *conditions: AbstractCondition
    ):
        self.conditions = set()
        for condition in conditions:
            if isinstance(
                    condition,
                    And
            ):
                for sub_condition in condition:
                    self.conditions.add(sub_condition)
            else:
                self.conditions.add(condition)

    def __iter__(self):
        return iter(sorted(self.conditions))

    @property
    def tables(self):
        return {
            table
            for condition
            in self.conditions
            for table
            in condition.tables
        }

    def __str__(self):
        return " AND ".join(map(
            str,
            sorted(
                self.conditions
            )
        ))
