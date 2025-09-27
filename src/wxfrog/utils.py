from pint import Unit

def fmt_unit(unit: Unit):
    result = f"{unit:~P#}"
    return result.replace(" ", "")