#!/usr/bin/env python

import argparse
import sys

from glob import glob
from minio import Minio
from pathlib import Path


class Uploader(object):

    def __init__(self, project_name, obj_store_location, access_key, secret_key, file_location):
        self.project_name = project_name
        self.files = glob(file_location)

        self.obj_store = Minio(obj_store_location,
                               access_key=access_key,
                               secret_key=secret_key,
                               secure=True)

    def run(self):
        if not self.obj_store.bucket_exists(self.project_name):
            self.obj_store.make_bucket(self.project_name)

        for file in self.files:
            self.obj_store.fput_object(
                bucket_name=self.project_name,
                object_name=Path(file).name,
                file_path=file
            )

        sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Uploads .deb file to object storage")

    parser.add_argument(
        '--obj-store-location', required=True, default="ci-object-store.netsoc.co",
        help="Address for the object store")

    parser.add_argument('--project-name', required=True,
                        help="Project name (alphanumeric)")
    parser.add_argument('--access-key', required=True, help="Access key")
    parser.add_argument('--secret-key', required=True, help="Secret key")
    parser.add_argument('--file-location', required=True,
                        help="Absolute path to the file to be uploaded")

    args = parser.parse_args()

    uploader = Uploader(
        args.project_name, args.obj_store_location, args.access_key,
        args.secret_key, args.file_location)
    uploader.run()
