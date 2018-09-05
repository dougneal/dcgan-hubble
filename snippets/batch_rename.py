import boto3
import sys
#import IPython

from_prefix = sys.argv[1]
to_prefix = sys.argv[2]

s3 = boto3.client('s3')

cursor = None

while True:
    if cursor is None:
        objects = s3.list_objects_v2(
            Bucket='jh-dn-dcgan-hubble',
            Prefix=from_prefix,
        )
    else:
        objects = s3.list_objects_v2(
            Bucket='jh-dn-dcgan-hubble',
            Prefix=from_prefix,
            StartAfter=cursor,
        )

    for obj in objects['Contents']:
        old_key = obj['Key']
        new_key = old_key.replace(from_prefix, to_prefix)
        print("Copying {0} to {1}".format(old_key, new_key))
        s3.copy_object(
            CopySource={
                'Bucket': 'jh-dn-dcgan-hubble',
                'Key': old_key,
            },
            Bucket='jh-dn-dcgan-hubble',
            Key=new_key,
        )

    cursor = objects['Contents'][-1]['Key']
