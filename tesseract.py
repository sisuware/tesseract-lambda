from __future__ import print_function

import json
import urllib
import boto3
import os
import subprocess
import tempfile
import uuid

print('Loading tesseract-lambda')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(SCRIPT_DIR, 'lib')

tmp_dir = tempfile.mkdtemp()
tmp_file_name = str(uuid.uuid4()) + '.txt'
tmp_result_path = os.path.join(tmp_dir, tmp_file_name)

s3 = boto3.client('s3')

def download_file(bucket, key):
    path = os.path.join(tmp_dir, key_name(key))
    s3.download_file(bucket, key, path)
    return path

def upload_file(file, bucket, name):
    s3.upload_file(file, bucket, name)

def key_name(key):
    return key.split('/')[-1]

def tesseract(image_file):
    command = 'LD_LIBRARY_PATH={} TESSDATA_PREFIX={} {}/tesseract {} {}'.format(
        LIB_DIR,
        os.path.join(SCRIPT_DIR, 'tessdata'),
        SCRIPT_DIR,
        image_file,
        tmp_result_path,
    )

    print('Tesseract command: ' + command)

    try:
        output = subprocess.check_output(command, shell=True)
        print(output)
        return tmp_result_path
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise e

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).decode('utf8')

    try:
        print("Bucket: " + bucket)
        print("Key: " + key)

        image_file = download_file(bucket, key)
        result_file = tesseract(image_file)
        upload_file(result_file, bucket, key_name(key))
    except Exception as e:
        print(e)
        print('Error processing object {} from bucket {}.'.format(key, bucket))
        raise e