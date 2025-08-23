from pathlib import Path
import re
import ctypes
import subprocess

SOURCE_FILE_PATTERN = re.compile(r"^test_.*\.c$")
HEADER_FILE_PATTERN = re.compile(r".*\.h$")
OBJECT_FILE_PATTERN = re.compile(r"^test_.*\.o$")
SHARED_FILE_PATTERN = re.compile(r"^test_.*\.(so|dll|dynlib)$")


class TestFunction:
    def __init__(self, func_ptr, filename: Path):
        self.func = func_ptr
        self.__name__ = func_ptr.__name__
        self.__file__ = filename

    def __call__(self) -> str | None:
        return self.func()

    def __repr__(self) -> str:
        return f"<TestFunction({self.__name__}@{self.func}, {self.__file__})>"

    def __str__(self) -> str:
        return f"{self.__file__}::{self.__name__}"


class TestModule:
    def __init__(self, path: Path):
        self.path = path
        self.lib = self._load_library()
        self.tests = []
        self.setup = None
        self.teardown = None
        self.ctst_failed = None
        self.ctst_succeeded = None
        self.ctst_skipped = None
        self._read_symbols()

    @property
    def failed(self) -> int:
        if self.ctst_failed is None:
            return -1
        return self.ctst_failed.value

    @property
    def succeeded(self) -> int:
        if self.ctst_succeeded is None:
            return -1
        return self.ctst_succeeded.value

    @property
    def skipped(self) -> int:
        if self.ctst_skipped is None:
            return -1
        return self.ctst_skipped.value

    def run(self, test_func):
        if self.setup:
            self.setup()
        result = test_func()
        if self.teardown:
            self.teardown()
        if result:
            result = result.decode("utf-8")
        return result

    def _load_library(self) -> ctypes.CDLL:
        return ctypes.CDLL(str(self.path))

    def _read_symbols(self):
        process = subprocess.run(
            ["nm", "-gU", str(self.path)], capture_output=True, text=True
        )
        if process.returncode != 0:
            raise RuntimeError(
                f"Failed to read symbols from {self.path}: {process.stderr}"
            )
        for line in process.stdout.splitlines():
            parts = line.split()
            if len(parts) == 3:
                _, symbol_type, name = parts
                if symbol_type in ("T", "t"):
                    func = TestFunction(getattr(self.lib, name), self.path)
                    if name.startswith("test_"):
                        func.func.restype = ctypes.c_char_p
                        self.tests.append(func)
                    elif name.startswith("skip_"):
                        func.func.restype = ctypes.c_char_p
                        self.tests.append(func)
                    elif name == "__ctst_setup":
                        self.setup = func
                    elif name == "__ctst_teardown":
                        self.teardown = func
                elif symbol_type in ("B", "b", "D", "d"):
                    var_reference = ctypes.c_int.in_dll(self.lib, name)
                    match name:
                        case "__ctst_failed":
                            self.ctst_failed = var_reference
                        case "__ctst_succeeded":
                            self.ctst_succeeded = var_reference
                        case "__ctst_skipped":
                            self.ctst_skipped = var_reference


def find_tests_dir(base_dir: Path) -> Path:
    """Find the 'tests' directory by traversing up the directory tree."""
    base_dir = base_dir.resolve()
    paths = [base_dir]
    history = {base_dir}
    while paths:
        parent = paths.pop()
        for subpath in parent.iterdir():
            subpath = subpath.resolve()
            if subpath.is_dir():
                if subpath.name in ("test", "tests"):
                    return subpath
                elif subpath not in history:
                    paths.append(subpath)

    raise FileNotFoundError("Could not find 'tests' directory.")


def find_files_regex(base_dir: Path, regex: re.Pattern) -> list[Path]:
    """Find all test files in the given 'tests' directory."""
    base_dir = base_dir.resolve()
    paths = [base_dir]
    history = {base_dir}
    test_files = []
    while paths:
        parent = paths.pop()
        for subpath in parent.iterdir():
            subpath = subpath.resolve()
            if subpath.is_dir() and subpath not in history:
                paths.append(subpath)
                history.add(subpath)
            elif subpath.is_file() and regex.match(subpath.name):
                test_files.append(subpath)
    return test_files


def discover(tests_dir: Path | None = None) -> list[TestModule]:
    """Discover and return all test modules in the 'tests' directory."""
    tests_dir = find_tests_dir(tests_dir or Path.cwd())
    shared_files = find_files_regex(tests_dir, SHARED_FILE_PATTERN)
    test_modules = [
        test_module
        for path in shared_files
        if (test_module := TestModule(path)) and test_module.tests
    ]
    return test_modules


def main():
    """Main function to find and run test modules."""
    test_modules = discover()
    total_failed = 0
    total_succeeded = 0
    total_skipped = 0
    results_summary = []
    for module in test_modules:
        print(f"Running tests in {module.path}:")
        for test in module.tests:
            result = module.run(test)
            if result is None:
                result_msg = f"  [OK] {test}"
            elif test.__name__.startswith("skip_"):
                result_msg = f"  [SKIP] {test}"
            else:
                result_msg = f"  [FAIL] {test}: {result}"
            print(result_msg)
            results_summary.append(result_msg)
        total_failed += module.failed
        total_succeeded += module.succeeded
        total_skipped += module.skipped
    print("\nSummary:")
    for line in results_summary:
        print(line)
    print("\nTotals:")
    print(f"  Total Succeeded: {total_succeeded}")
    print(f"  Total Failed: {total_failed}")
    print(f"  Total Skipped: {total_skipped}")
    if total_failed > 0:
        exit(1)
    exit(0)


if __name__ == "__main__":
    main()
