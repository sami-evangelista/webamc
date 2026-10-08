from webamc.all import *
from webamc.www import html_elements as he


class Input:
    def __init__(self, col: sa.Column[tp.Any], js_type: str) -> None:
        self.col = col
        self.js_type = js_type
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
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
    def _init_element(
            self,
            element: he.Element,
            **kwargs: str
    ) -> he.Element:
        result = element
        result["name"] = self.col.name
        result["id"] = self.col.name
        result.set_data("type", self.js_type)
        for arg, val in kwargs.items():
            result[arg] = val
        return result


class Text(Input):
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        result = he.Input(type_="text")
        if value is not None:
            result["value"] = str(value)
        return self._init_element(result, **kwargs)
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_like"), value="like"),
            he.Option(he.Txt("op_notlike"), value="notlike")
        )
        return result


class Password(Input):
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        result = he.Input(type_="password")
        if value is not None:
            result["value"] = str(value)
        return self._init_element(result, **kwargs)


class Textarea(Input):
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        result = he.Textarea(rows="20", cols="80")
        if value is not None:
            result.append(he.Str(str(value)))
        return self._init_element(result, **kwargs)
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_like"), value="like"),
            he.Option(he.Txt("op_notlike"), value="notlike")
        )
        return result


class Number(Input):
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        result = he.Input(type_="number")
        if value is not None:
            assert isinstance(value, int)
            result["value"] = str(int(value))
        return self._init_element(result, **kwargs)
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_lt"), value="<"),
            he.Option(he.Txt("op_gt"), value=">")
        )
        return result


class Date(Input):
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        result = he.Input(type_="date")
        if value is not None:
            result["value"] = str(value)
        return self._init_element(result, **kwargs)
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_before"), value="<"),
            he.Option(he.Txt("op_after"), value=">")
        )
        return result


class DateTime(Input):
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        result = he.Input(type_="datetime-local")
        if value is not None:
            result["value"] = str(value)
        return self._init_element(result, **kwargs)
    def element_cmp(self) -> he.Element:
        result = super().element_cmp()
        result.append(
            he.Option(he.Txt("op_before"), value="<"),
            he.Option(he.Txt("op_after"), value=">")
        )
        return result


class Color(Input):
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        result = he.Input(type_="color")
        if value is not None:
            result["value"] = str(value)
        return self._init_element(result, **kwargs)


class Checkbox(Input):
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        result = he.Input(type_="checkbox")
        result.add_flag("checked", value is not None and bool(value))
        return self._init_element(result, **kwargs)


class Select(Input):
    def __init__(
            self,
            col: sa.Column[tp.Any],
            js_type: str,
            options: dict[tp.Any, tp.Any]
    ) -> None:
        super().__init__(col, js_type)
        self.options = options
    def element(
            self,
            value: None | types.db_base_val_t = None,
            **kwargs: tp.Any
    ) -> he.Element:
        options = [
            he.Option(he.Str(v), value=k).add_flag("selected", value == k)
            for k, v in self.options.items()
        ]
        if self.col.nullable:
            options.insert(0, he.Option(value=""))
        result = self._init_element(he.Select(*options), **kwargs)
        return result
