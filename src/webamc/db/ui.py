#!/usr/bin/env python3

from webamc.all import *
from webamc.www import html_elements as he


class Input:
    js_init_fun = ""
    def __init__(self, col: sa.Column[tp.Any]) -> None:
        self.col = col
    def direct_update(self) -> bool:
        return self.js_init_fun != ""
    def element(self) -> he.Element:
        raise ValueError
    def element_cmp(self) -> he.Element:
        name = self.col.name + "-cmp"
        result = he.Select(
            he.Option(),
            he.Option(he.Txt("op_eq"), value="="),
            he.Option(he.Txt("op_diff"), value="!="),
            name=name,
            id_=name
        )
        return result
    def _init_element(self, element: he.Element) -> he.Element:
        element["name"] = self.col.name
        element["id"] = self.col.name
        return element


class Text(Input):
    def element(self) -> he.Element:
        return self._init_element(he.Input(type_="text"))
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_like"), value="like"),
            he.Option(he.Txt("op_notlike"), value="notlike")
        )
        return result


class Password(Input):
    def element(self) -> he.Element:
        return self._init_element(he.Input(type_="password"))


class Textarea(Input):
    def element(self) -> he.Element:
        return self._init_element(he.Textarea(rows="6", cols="40"))
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_like"), value="like"),
            he.Option(he.Txt("op_notlike"), value="notlike")
        )
        return result


class Number(Input):
    def element(self) -> he.Element:
        return self._init_element(he.Input(type_="number"))
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_lt"), value="<"),
            he.Option(he.Txt("op_gt"), value=">")
        )
        return result


class Date(Input):
    def element(self) -> he.Element:
        return self._init_element(he.Input(type_="date"))
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_before"), value="<"),
            he.Option(he.Txt("op_after"), value=">")
        )
        return result


class DateTime(Input):
    def element(self) -> he.Element:
        return self._init_element(he.Input(type_="datetime-local"))
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_before"), value="<"),
            he.Option(he.Txt("op_after"), value=">")
        )
        return result


class Color(Input):
    js_init_fun = "db_color"
    def element(self) -> he.Element:
        return self._init_element(he.Input(type_="color"))


class Checkbox(Input):
    js_init_fun = "db_checkbox"
    def element(self) -> he.Element:
        return self._init_element(he.Input(type_="checkbox"))


class Select(Input):
    def __init__(
            self,
            col: sa.Column[tp.Any],
            options: dict[tp.Any, tp.Any]
    ) -> None:
        super().__init__(col)
        self.options = options
    def element(self) -> he.Element:
        options = [
            he.Option(he.Str(v), value=k) for k, v in self.options.items()
        ]
        if self.col.nullable:
            options.insert(0, he.Option(value=""))
        result = self._init_element(he.Select(*options, type_="select"))
        if all(isinstance(v, int) for v in self.options.values()):
            result.set_data("type", "integer")
        return result
