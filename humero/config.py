from dynaconf import Dynaconf
import git
from pathlib import Path

def get_project_root():
    return Path(git.Repo('.', search_parent_directories=True).working_tree_dir)

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.yaml', '.secrets.yaml'],
    environments=True,
    load_dotenv=True,
    root_path=get_project_root()
)