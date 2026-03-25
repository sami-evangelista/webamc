# pylint: disable-all

from webamc.all import *
from webamc.util import fmt


class Element:
    empty = False

    def __init__(self, *children: "Element", **attrs: tp.Any):
        self.children = [c for c in children]
        self.attrs = {
            str(x[:-1]) if str(x[-1]) == "_" else str(x): str(y)
            for x, y in attrs.items()
        }
        self.data: dict[str, str] = dict()

    def __str__(self) -> str:
        result = ""
        tag = self.__class__.__name__.lower()
        result += f"<{tag}" + "".join(
            f" {k}=\"{v}\"" for k, v in self.attrs.items()
        )
        if self.data != dict():
            result += " " + " ".join(
                f"data-{k}=\"{v}\"" for k, v in self.data.items()
            )
        result += ">" + "\n".join(str(c) for c in self.children)
        if not self.empty:
            result += f"</{tag}>"
        return result

    def __setitem__(self, attr: str, value: str) -> None:
        self.attrs[attr] = value

    def __getitem__(self, attr: str) -> str:
        return self.attrs.get(attr, "")

    def append(self, *e: "Element") -> None:
        for child in e:
            self.children.append(child)

    def set_attr(self, attr: str, value: str) -> "Element":
        self.attrs[attr] = value
        return self

    def set_data(self, data: str, value: str) -> "Element":
        self.data[data] = value
        return self


class A(Element):
    pass
class Body(Element):
    pass
class Br(Element):
    empty = True
class Button(Element):
    pass
class Code(Element):
    escape = False
class Div(Element):
    pass
class Em(Element):
    pass
class Fieldset(Element):
    pass
class Form(Element):
    pass
class H1(Element):
    pass
class H2(Element):
    pass
class H3(Element):
    pass
class Head(Element):
    pass
class Hr(Element):
    pass
class Html(Element):
    pass
class Img(Element):
    empty = True
class Input(Element):
    empty = True
class Meta(Element):
    empty = True
class Label(Element):
    pass
class Li(Element):
    pass
class Link(Element):
    empty = True
class Option(Element):
    pass
class P(Element):
    pass
class Pre(Element):
    pass
class Select(Element):
    pass
class Textarea(Element):
    pass
class Span(Element):
    pass
class Td(Element):
    pass
class Thead(Element):
    pass
class Tr(Element):
    pass
class Table(Element):
    pass
class Ul(Element):
    pass
class Title(Element):
    pass


class ElementList(Element):
    def __str__(self) -> str:
        return "\n".join(str(c) for c in self.children)
class Empty(Element):
    def __str__(self) -> str:
        return ""
class Txt(Element):
    def __init__(self, id_: types.txt_t, fmt: bool=True):
        self.id_ = id_
        self.fmt = fmt
    def __str__(self) -> str:
        result = lang.txt(self.id_)
        if self.fmt:
            result = fmt.fmt_title(result)
        result = html.escape(result)
        return result
class Str(Element):
    def __init__(self, content: str, escape: bool = True):
        self.content = content
        self.escape = escape
    def __str__(self) -> str:
        if self.escape:
            return html.escape(self.content)
        return self.content
class Script(Element):
    def __init__(self, content: None | str | list[str] = None, **attrs: tp.Any):
        super().__init__(**attrs)
        self.content = content
    def __str__(self) -> str:
        if self["src"] != "":
            return super().__str__()
        if self.content is None:
            content = ""
        elif isinstance(self.content, str):
            content = self.content
        else:
            content = "\n".join(self.content)
        return f"<script>\n{content}\n</script>"    
