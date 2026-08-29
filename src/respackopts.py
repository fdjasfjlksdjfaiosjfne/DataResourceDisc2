import re

RT_COMPARATOR = "§f\ue101"
RT_CLOCK = "§f\ue102"

FORMATTING_LIST = {
    "0": "black",
    "1": "dblue",
    "2": "dgreen",
    "3": "daqua",
    "4": "dred",
    "5": "dpurple",
    "6": "gold",
    "7": "gray",
    "8": "dgray",
    "9": "blue",
    "a": "green",
    "b": "aqua",
    "c": "red",
    "d": "lpurple",
    "e": "yellow",
    "f": "white",
    "k": "obfus",
    "l": "bold",
    "m": "strike",
    "n": "uline",
    "o": "italic",
    "r": "reset",
}

def mu_ternary(condition: str, true: str, false: str) -> str:
    return f' {condition} ? {true} : {false} '

def mu_enum_equals(enumOption: str, value: str) -> str:
    return f'("" || {enumOption}) == "{value}"'

def mu_enum_nequals(enumOption: str, value: str) -> str:
    return f'("" || {enumOption}) != "{value}"'

def mu_string(content: str) -> str:
    return f'"{re.sub(r"(?<!\\)(?:\\\\)*[\"']", lambda m: f"\\{m.group(0)}", content)}"'

def mu_contains(container: str, content: str):
    return f"contains({container}, {content})"

def mu_object(d: dict) -> str:
    return "{%s}" % ",".join(f"`{k}` = {v}" for k, v in d.items())