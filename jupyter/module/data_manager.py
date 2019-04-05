# -*- coding: utf-8 -*-
from datetime import datetime as dt, datetime
import gzip
from io import BytesIO
import json
import pickle
import random
import string
import time

import boto3
from boto3 import Session
import requests
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.engine import url as sa_url
from sqlalchemy import Sequence
from sqlalchemy.orm.session import sessionmaker
from boto3.dynamodb.conditions import Key,Attr

import traceback
from pathlib import Path
import sys
import csv


from logging import getLogger, StreamHandler, DEBUG, INFO, WARN, ERROR, FATAL

logger_level = DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(logger_level)
logger.setLevel(logger_level)
logger.addHandler(handler)
logger.propagate = False

def load_json(file_name):
    try:
        with open(file_name, "r") as f:
            return json.load(f)
        return None
    except BaseException as e:
        print(e)
        return None


def rand_maker():
    source_str = 'abcdefghijklmnopqrstuvwxyz'
    return "".join([random.choice(source_str) for x in range(10)])


def make_query_str_values(values):
    ret = ""
    for v in values:
        if v is None:
            ret += "NULL,"
        elif type(v) is str:
            ret += "'%s'," % v
        else:
            ret += "%f," % v
    return ret[:-1]


def load_pickle(file_name):
    with open(file_name, "rb") as f:
        return pickle.load(f)
    return None


def save(data, file_name, mode):
    try:
        with open(file_name, mode) as f:
            f.write(data)
    except BaseException as e:
        print(e)


def make_rand_str(digit):
    random_str = ''.join([random.choice(string.ascii_letters + string.digits)
                          for _ in range(digit)])
    return random_str


def unix_to_utc_str(unix_time):
    datetime_obj = dt.fromtimestamp(unix_time)
    return dt_utc_to_str_utc(datetime_obj)


def now_str():
    return dt_utc_to_str_utc(dt.now())


def dt_utc_to_str_utc(dt_utc):
    return dt_utc.strftime('%Y-%m-%d %H:%M:%S')


def data_loader(url):
    try:
        r = requests.get(url)
        res = r.content.decode('utf-8')
        return json.loads(res)
    except BaseException as e:
        print(e)


def post(url, params):
    r = requests.post(url, params)
    print("url", url, "params", params)
    res = r.content
    print("raw_res:{}".format(res))
    try:
        print("json.loads:{}".format(json.loads(res)))
        return json.loads(res)
    except:
        print("JSONDecodeError happened")
        print(traceback.format_exc())
        print("res is None")
        return None
    else:
        print("else")
        return None


def read_csv(file_path,is_col=False):
    if is_col:
        with open(file_path, "r") as f:
            data = csv.reader(f)
            return [d for d in data]
    else:
        with open(file_path, "r") as f:
            data = csv.reader(f)
            return [d for d in data][1:]

def csv_write(file_path, data, mode="a"):
    with open(file_path, mode, newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)


class DynamoDBManager():
    def __init__(self, region_name, endpoint_url=None, env=None):
        if env == 'localhost':
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name, endpoint_url=endpoint_url)
            self.client = boto3.client('dynamodb', region_name=region_name, endpoint_url=endpoint_url)
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            self.client = boto3.client('dynamodb', region_name=region_name)

    def create_table(self, table_name, key_schema, attribute_definitions, provisioned_throughput):
        table = self.dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            ProvisionedThroughput=provisioned_throughput
        )
        print("Table status:", table.table_status)

    def update_item(self,table_name,hash_key,hash_value,sort_key,sort_value,update_hash):
        table = self.dynamodb.Table(table_name)
        res = table.update_item(
            Key={hash_key:hash_value,
                 sort_key:sort_value},
            AttributeUpdates=update_hash
        )
        return res

    def batch_write(self, table_name, data, overwrite_by_pkeys=None):
        table = self.dynamodb.Table(table_name)
        if overwrite_by_pkeys is None:
            with table.batch_writer() as batch:
                for d in data:
                    batch.put_item(Item=d)
        elif overwrite_by_pkeys is not None:
            with table.batch_writer(overwrite_by_pkeys=overwrite_by_pkeys) as batch:
                for d in data:
                    batch.put_item(Item=d)

    def fetch_all(self, table_name, hash_key=None, hash_value=None, sort_key=None, start="1919-01-01"):
        table = self.dynamodb.Table(table_name)
        if hash_value is not None:
            ExclusiveStartKey = None

            results = []

            while True:
                if ExclusiveStartKey is None:
                    response = table.query(KeyConditionExpression=Key(hash_key).eq(hash_value)
                                                                  & Key(sort_key).gt(start))

                    results = results + response["Items"]
                else:
                    response = table.query(KeyConditionExpression=Key(hash_key).eq(hash_value)
                                                                  & Key(sort_key).gt(start),
                                           ExclusiveStartKey=ExclusiveStartKey)
                    results = results + response["Items"]

                if ("LastEvaluatedKey" in response) == True:
                    ExclusiveStartKey = response["LastEvaluatedKey"]
                else:
                    break
            return results
        else:
            ExclusiveStartKey = None

            results = []

            while True:
                if ExclusiveStartKey is None:
                    response = table.scan()
                    results = results + response["Items"]
                else:
                    response = table.scan(ExclusiveStartKey=ExclusiveStartKey)
                    results = results + response["Items"]

                if ("LastEvaluatedKey" in response) == True:
                    ExclusiveStartKey = response["LastEvaluatedKey"]
                else:
                    break
            return results

    def fetch_latest_row(self, table_name, hash_key="timeseries_fixed_value", hash_value=None):
        if hash_value is None:
            hash_value = table_name
        table = self.dynamodb.Table(table_name)
        res = table.query(
            KeyConditionExpression=Key(hash_key).eq(hash_value),
            Limit=1,
            ScanIndexForward=False
        )["Items"][0]
        return res

    def fetch_latest_n_rows(self, table_name, hash_key="timeseries_fixed_value", hash_value=None, rows_count=100):
        if hash_value is None:
            hash_value = table_name
        table = self.dynamodb.Table(table_name)
        res = table.query(
            KeyConditionExpression=Key(hash_key).eq(hash_value),
            Limit=rows_count,
            ScanIndexForward=False
        )["Items"][0]
        return res

class S3Manager:
    def __init__(self, bucket_name, location):
        self.conn = boto3.resource('s3')
        self.bucket_name = bucket_name
        self.s3client = Session().client('s3')
        self.location = location

    def save(self, data, file_name):
        obj = self.conn.Object(self.bucket_name, file_name)
        obj.put(Body=json.dumps(data, ensure_ascii=False))

    def download(self, file_key):
        obj = self.conn.Object(self.bucket_name, file_key)
        response = obj.get()["Body"].read()
        buf = BytesIO(response)
        gzip_f = gzip.GzipFile(fileobj=buf)
        body = gzip_f.read().decode('utf-8')
        return body

    def get_created_at(self, file_key):
        obj = self.conn.Object(self.bucket_name, file_key)
        return obj.last_modified

    def get_all_file_names(self, prefix='', keys=[], marker=''):
        response = self.s3client.list_objects(Bucket=self.bucket_name,
                                              Prefix=prefix, Marker=marker)
        if 'Contents' in response:
            keys.extend([content['Key'] for content in response['Contents']])
            if 'IsTruncated' in response:
                return self.get_all_file_names(prefix=prefix, keys=keys, marker=keys[-1])
        return keys

    def upload(self, remote_file_key, local_file_name,is_public=None):
        if is_public:
            self.s3client.upload_file(local_file_name, self.bucket_name, remote_file_key,
                                      ExtraArgs={'ContentType': "image/png",'ACL': 'public-read'})
            return "Ok"

        self.s3client.upload_file(local_file_name, self.bucket_name, remote_file_key)
        return "Ok"
