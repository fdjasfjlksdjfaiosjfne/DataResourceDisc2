from data import DATA
from json5 import dumps

def add_trigger_objective(objective: str) -> str:
    return f"scoreboard objectives add {objective} trigger"

def set_objective(to: str, objective: str, value: int):
    return f"scoreboard players set {to} {objective} {value}"

def enable_objective(to: str, objective: str) -> str:
    return f"scoreboard players enable {to} {objective}"

def trigger_set(objective: str, value: int) -> str:
    return f"trigger {objective} set {value}"

def exe_as(to: str, command: str):
    return f"execute as {to} run {command}"

def exe_as_all_with_pred(predicate: str, command: str):
    return exe_as(f"@a[predicate={DATA.our_namespace}:{predicate}]", command)

def run_function(function: str):
    return f"function {DATA.our_namespace}:{function}"

def tellraw(to: str, component: dict | str):
    return f"tellraw {to} {f"'{component}'" if isinstance(component, str) else dumps(component, trailing_commas = False)}"

def exe_if_item_mainhand(to: str, pred: str, command: str) -> str:
    return f"execute if items entity {to} weapon.mainhand {pred} run {command}"