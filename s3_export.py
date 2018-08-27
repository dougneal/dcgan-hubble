import boto3
import io
import imageio
import numpy

s3 = boto3.resource('s3')
bucket = s3.Bucket('jh-dn-dcgan-hubble')


def export_images_to_s3(images, timestamp, training=False, epoch=None, setnum=None):
    # Map the -1.0 to 1.0 range back up to the 0-255 range
    images = (images + 1.0) * 127.5
    images = images.astype(numpy.uint8)

    for i in range(len(images)):
        bytesio = io.BytesIO()
        imageio.imwrite(
            uri=bytesio,
            im=images[i],
            format='png',
        )
        bytesio.seek(0)

        if training:
            s3key = "{0}/training/epoch_{1}/{2}.png".format(
                timestamp, epoch, i
            )
        else:
            s3key = "{0}/set_{1}/{2}.png".format(
                timestamp, setnum, i
            )

        s3obj = bucket.Object(s3key)
        s3obj.upload_fileobj(bytesio)
