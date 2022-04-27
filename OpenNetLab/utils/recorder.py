import json
from pathlib import Path


class ElementMatchError(Exception):
    def __init__(self, msg):
        self.msg = msg


class Recorder:
    def __init__(self, outdir_path):
        self.outdir_path = outdir_path
        self.fp = None
        self.cur_idx = -1
        self.headers = None
        self.record = None
        self.records = []

    def set_headers(self, headers):
        self.headers = headers

    def open(self, test_idx):
        if not self.headers:
            return
        output_dir = Path(self.outdir_path)
        if not output_dir.exists():
            output_dir.mkdir()
        self.fp = open(f'{output_dir}/test_record{test_idx}.json', 'w')
        self.headers = self.headers
        return self

    def close(self):
        if self.fp:
            json.dump(self.records, self.fp)
            self.fp.close()

    def add_record(self, test_idx, row_data):
        if not self.headers:
            return
        if test_idx != self.cur_idx:
            self.close()
            self.open(test_idx)
            self.cur_idx = test_idx
        if not self.fp:
            return
        if len(row_data) != len(self.headers):
            raise ElementMatchError(f'Row and Header not matching: '
                                    f'header length: {len(self.headers)}, row length: {len(row_data)}')
        record = {}
        for i, k in enumerate(self.headers):
            record[k] = row_data[i]
        self.records.append(record)
