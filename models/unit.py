from enum import Enum


class UnitModel(Enum):
    NaN = 0,
    Max = 1,
    Pro = 2,
    Plus = 3


def get_unit_model(unit_name: str) -> UnitModel:
    if unit_name[0:3] == '002':
        return UnitModel.Plus
    elif unit_name[0:3] == '001':
        return UnitModel.Pro
    elif unit_name[0:3] == '000':
        return UnitModel.Max
    return UnitModel.Max
