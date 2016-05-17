import base64
import csv
import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import hashlib
import hmac
import json
import os
import smtplib
import tempfile
import requests

APPLICATION_ID = os.getenv('APPLICATION_ID')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
FROM = os.getenv('FROM')
TO = os.getenv('TO')

URL = '/r2/access/search?show_expired=true'

message = bytes("GET {}").format(URL).encode('utf-8')
secret = bytes(PRIVATE_KEY).encode('utf-8')

# don't ask me why these substitutions are here:
signature = base64.b64encode(hmac.new(
    secret, message, digestmod=hashlib.sha256).digest()).replace(
            '+', '-').replace('/', '_').rstrip('=')

auth_header = "{}:{}".format(APPLICATION_ID, signature)

url = 'https://api.tinypass.com{}'.format(URL)

response = requests.get(url,
        headers={'Authorization': '{}'.format(auth_header)})

body = json.loads(response.text)

data = body['data']
keys = data[0].keys()


def send_mail(send_from, send_to, subject, text, files=None,
              server="smtp"):
    assert isinstance(send_to, list)

    msg = MIMEMultipart(
        From=send_from,
        To=COMMASPACE.join(send_to),
        Date=formatdate(localtime=True),
        Subject=subject
    )
    msg['Subject'] = subject
    msg['To'] = COMMASPACE.join(send_to)
    msg['From'] = send_from

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            msg.attach(MIMEApplication(
                fil.read(),
                Content_Disposition='attachment; filename="tinypass.csv"',
                Name='tinypass.csv',
            ))

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


def convert_date(unix_date):
    if unix_date < 1:
        return 0
    return datetime.datetime.fromtimestamp(int(unix_date)).strftime(
            '%Y-%m-%d %H:%M:%S')

for item in data:
    try:
        expires = item['expires']
    except KeyError:
        expires = 0
    item['expires'] = convert_date(expires)
    item['created'] = convert_date(item['created'])

temp_file = tempfile.NamedTemporaryFile(delete=False)
w = csv.DictWriter(temp_file, keys)
w.writeheader()
w.writerows(data)

send_mail(FROM, [TO],
    subject='Tinypass export',
    text='Attached find the latest export from Tinypass.',
    files=[temp_file.name])

os.unlink(temp_file.name)
