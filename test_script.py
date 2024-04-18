import unittest
import coverage
import sys
from termcolor import colored
from flake8.api.legacy import get_style_guide


if __name__ == "__main__":
    cov = coverage.Coverage(source=['./src/algorithm/'])
    cov.start()
    print(colored("\n================== unittest ==================\n", "yellow"))
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir='./tests/algorithm/',
        pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

    print(colored("\n================== coverage ==================\n", "yellow"))
    cov.stop()
    cov.report()

    print(colored("\n==================  flake8  ==================\n", "yellow"))
    style_guide = get_style_guide()
    report = style_guide.check_files(['src', 'tests'])
