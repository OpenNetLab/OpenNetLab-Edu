import argparse
import json
import sys
from abc import abstractmethod, ABC
from pathlib import Path

FormatErr = "Testcase file format error"


class Testing(ABC):
    def __init__(self, tester_file: str) -> None:
        testcases_path = Path(tester_file).absolute().parent.joinpath("testcases.json")
        if not testcases_path.is_file():
            print(f"{testcases_path} is not a regular file")
            sys.exit(1)
        with testcases_path.open("r") as fp:
            raw_data = json.load(fp)
        self._global_cfg = None
        if "config" in raw_data:
            self._global_cfg = raw_data["config"]
        if "testcases" not in raw_data:
            print("no testcases in the testcases file")
            sys.exit(1)
        self._testcases = raw_data["testcases"]
        self._total_ranks = 0
        self._get_ranks = 0
        self._failed = list()
        self._debug = False
        self._log = False
        self._log_dir = testcases_path.parent.joinpath("logs")
        self._log_file_template = "testcase{:d}.log"

    @property
    def grade(self):
        return int(self._get_ranks * 100.0 / self._total_ranks)

    @abstractmethod
    def judge_testcase(self, input, cfg, debug):
        """unimplement, subclass should implement this function"""

    def compare_output_with_expected(self, output, expected_output) -> bool:
        return output == expected_output

    def run_all_testcases(self):
        for index in range(1, len(self._testcases) + 1):
            self.run_testcase(index)
        if len(self._failed) == 0:
            print("All testcases passed, grade is 100")
        else:
            print(f"Failed testcases: {self._failed}, grade is {self.grade}")

    def _check(self, testcase, key):
        if key not in testcase:
            print(f"{FormatErr}: testcase{key}'s entry doesn't have input")
            sys.exit(1)

    def run_testcase(self, index: int):
        testcase = self._testcases[index - 1]
        cfg = testcase["config"] if "config" in testcase else None
        self._check(testcase, "input")
        input = testcase["input"]
        self._check(testcase, "output")
        expected_output = testcase["output"]
        self._check(testcase, "rank")
        rank = testcase["rank"]

        print(f"Running testcase {index}: ", end="", file=sys.__stdout__)
        log_file = None
        passed = False
        if self._log:
            if not self._log_dir.exists():
                self._log_dir.mkdir()
            log_file_path = self._log_dir.joinpath(
                self._log_file_template.format(index)
            )
            log_file = open(str(log_file_path), "w")
            sys.stdout = log_file
        try:
            output = self.judge_testcase(
                input, cfg if cfg else self._global_cfg, self._debug
            )
            if self.compare_output_with_expected(output, expected_output):
                passed = True
            else:
                print(
                    f"failed\n"
                    f"expected output: {expected_output}\nyour output: {output}",
                    file=sys.__stdout__,
                )
        except Exception as _:
            pass
        finally:
            if self._log:
                assert log_file
                log_file.close()
                sys.stdout = sys.__stdout__

        self._total_ranks += rank
        if passed:
            print("passed", file=sys.__stdout__)
            self._get_ranks += rank
        else:
            self._failed.append(index)

    def run(self):
        parser = argparse.ArgumentParser(
            prog="Tester",
            description="Testing onl program",
            epilog="Get more help on onl online doc",
        )
        parser.add_argument(
            "-t",
            "--testcase",
            type=int,
            metavar="testcase_index",
            help="running the ith testcase",
        )
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="use debug mode to show program output",
        )
        parser.add_argument(
            "-l",
            "--log",
            action="store_true",
            help="redirect testcase output to a log file",
        )
        args = parser.parse_args()
        if args.debug:
            self._debug = True
        if args.log:
            self._debug = True
            self._log = True
        if args.testcase:
            assert type(args.testcase) == int
            if not (1 <= args.testcase <= len(self._testcases)):
                print(
                    f"There is only {len(self._testcases)} testcases, {args.testcase} is an invalid index"
                )
                sys.exit(1)
            self.run_testcase(args.testcase)
            return
        self.run_all_testcases()
