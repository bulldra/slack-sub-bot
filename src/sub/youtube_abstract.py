import os
import tempfile

import google.cloud

storage_client = google.cloud.storage.Client()

with tempfile.TemporaryDirectory() as tmpdir:
    with open(os.path.join(tmpdir, "testfile"), "w") as fp:
        fp.write("test script")
        bucket = storage_client.bucket("bulldra-api-storage")
        blob = bucket.blob("sample.txt")
        blob.upload_from_file(fp)
