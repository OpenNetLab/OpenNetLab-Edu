import json
from pathlib import Path


class ElementMatchError(Exception):
    def __init__(self, msg):
        self.msg = msg


class Recorder:
    def __init__(self, outdir_path):
        self.outdir_path = outdir_path
        self.fp = None
        self.testcase_idx = 0
        self.all_records = []

    def open(self):
        output_dir = Path(self.outdir_path)
        if not output_dir.exists():
            output_dir.mkdir()
        self.fp = open(f'{self.outdir_path}/test_record{self.testcase_idx}.json', 'w')
        return self

    def close(self):
        if self.fp:
            json.dump(self.all_records, self.fp)
            self.fp.close()

    def start_next_testcase(self):
        self.close()
        self.all_records.clear()
        self.testcase_idx += 1
        self.open()

    def add_send_record(self, packet):
        if not self.fp:
            return
        record = {
            'type': 1,
            'packet': packet
        }
        self.all_records.append(record)


    def add_recv_record(self, packet):
        if not self.fp:
            return
        record = {
            'type': 0,
            'packet': packet
        }
        self.all_records.append(record)
