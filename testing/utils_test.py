from wxfrog.utils import DataStructure, get_unit_registry

Q = get_unit_registry().Quantity

def test_get(sample_structure):
    path = ("Heater", "Shell", "Pr")
    assert float(sample_structure.get(path)) == 0.7

def test_set(sample_structure):
    path = ("Heater", "Shell", "Pr")
    new_value = 0.8
    sample_structure.set(path, Q(new_value))
    assert float(sample_structure.get(path)) == new_value

def test_tojson(sample_structure):
    result = sample_structure.to_jsonable()
    assert result["Heater"]["Tube"]["U"] == "800 W / K / m ** 2"

def test_from_jsonable():
    inp = {
        "a": {
            "b": "3 degC",
            "c": "5 m^3/h"},
        "d": "20 bar",
        "e": "100"
    }
    s = DataStructure.from_jsonable(inp)
    assert s["e"] == 100.0

def test_all_paths(sample_structure):
    result = sample_structure.all_paths
    assert len(result) == 9
    assert ('Heater', 'Tube', 'Re') in result