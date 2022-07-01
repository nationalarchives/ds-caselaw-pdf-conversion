import json
from copy import deepcopy

BUCKET = "tna-caselaw-assets"

records = []
record_template = {
    "s3": {
        "bucket": {"name": BUCKET},
        "object": {
            "key": "PLACEHOLDER",
            "eTag": "PLACEHOLDER",
        },
    }
}

with open("/tmp/files.txt") as f:
    files = [x.strip() for x in f.readlines()]

for i, file in enumerate(files):
    record = deepcopy(record_template)
    record["s3"]["object"]["key"] = file
    record["s3"]["object"]["eTag"] = str(i)
    records.append(record)

out = {"Records": records}

with open("/tmp/out.json", "w") as f:
    json.dump(out, f, indent=2)
