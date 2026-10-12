from pathlib import Path
import shutil

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"

def create_and_clear_results_folder() -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for item in RESULTS_DIR.iterdir():
        if item.is_symlink() or not item.is_dir():
            item.unlink()
        else:
            shutil.rmtree(item)
    return RESULTS_DIR

def create_algorithm_data_text(number: int, path) -> Path:
    file_name = f"algorithm_data_{number}.txt"
    file_path = path / file_name
    file_path.touch(exist_ok=True)
    return file_path

