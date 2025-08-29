import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


from clif_bot.state import StatusStore


def test_table_poc_persistence(tmp_path):
    data_file = tmp_path / "data.json"
    store = StatusStore(data_file=str(data_file))
    store.set_table_poc("table_a", "user1")
    assert store.get_table_poc("table_a") == "user1"

    store2 = StatusStore(data_file=str(data_file))
    assert store2.get_table_poc("table_a") == "user1"

