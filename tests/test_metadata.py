import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from clif_bot.metadata import parse_repo


def test_parse_repo_reads_readme():
    repo = "https://github.com/Common-Longitudinal-ICU-data-Format/CLIF-eligibility-for-mobilization"
    metadata = parse_repo(repo)
    assert metadata.project_name
    assert metadata.description
