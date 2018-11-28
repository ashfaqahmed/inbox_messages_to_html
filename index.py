from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
import email
from oauth2client import file, client, tools
import base64
import unicodecsv
import json
from bs4 import BeautifulSoup
from lxml.html.clean import Cleaner
import re
import os

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

# out folder to save emails as html

OUT_PATH = "mails"

# url regex to remove urls (optional) and commented
URL_REGEX = re.compile(r'http.+? ', re.DOTALL)

# url regex to remove urls (optional) and commented in method html_to_text():
def remove_urls(text):
    return re.sub(URL_REGEX, '', text)

# fixing spaces
def fix_spaces_cr_lf(input_str):
    input_str = input_str.replace("&nbsp;", " ").replace("\r", " ")\
        .replace("\n", " ").strip()
    return " ".join(input_str.split()).strip()

# process raw message
def process_raw_msg(raw_msg, lbl,msg_id,append=True):
    try:
        data = raw_msg.decode()
        mime_msg = email.message_from_bytes(raw_msg)
    except AttributeError:
        mime_msg = email.message_from_string(raw_msg)
    text = clean_punctuation(html_to_text(concat_email_text(mime_msg)))
    subject = mime_msg.get("Subject")
    subject = clean_punctuation(subject.replace("\r", " ").replace("\n", " "))
    sender_domain = mime_msg.get("From").split("@")[1].split(">")[0]

    # these fields are available if you want to modify content or file name with these
    #sender_domain, subject, text

    # check if directory not exist and create it
    if not os.path.exists(OUT_PATH + "/" + lbl):
         os.makedirs(OUT_PATH + "/" + lbl)
    # save message in label directory with named of from domain + message id
    save_html(text,OUT_PATH + "/" + lbl + "/" + sender_domain + "_" + msg_id + ".html")

# return all messages in label
def list_messages_with_label(service, user_id, label_ids=[]):
    try:
        response = service.users().messages().list(userId=user_id,
                   labelIds=label_ids).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id,
                       labelIds=label_ids, pageToken=page_token).execute()
            messages.extend(response['messages'])
        return messages
    except Exception as inst:
          print(type(inst))
          print(inst.args)
          print(inst)

# get / return messages raw by id
def get_raw_message_from_id(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id,format='raw').execute()
        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ascii'))
        return msg_str
    except errors.HttpError as error:
        print("An error occured: %s" % error)

# remove punctuation (optional we are not using it you can modify this if you want)
def clean_punctuation(text):
    return text

def html_to_text(html_page_string):
    '''
        just skiped for now you can update it here if you want any modification or replacing in html
    '''
    #remove_urls(" ".join(soup.findAll(text=True)))
    return html_page_string

def concat_email_text(mime_msg):
    text = ""
    for part in mime_msg.walk():
        payload = part.get_payload(decode=True)
        if payload is not None:
            text += " "
            text += payload.decode('UTF-8')
    return text

def list_messages(gs,user,lbl):
    # get message in this label
    msg_id_list = list_messages_with_label(gs, user,lbl)
    # count messages in this label
    num_msgs = len(msg_id_list)
    # print total message with label name
    print("Total messages:", num_msgs, " In Label", lbl)
    count = 1
    # move further if label have any messages
    if num_msgs > 0:
        # loop through message list
        for msg in msg_id_list:
            # extract raw message by message id
            raw = get_raw_message_from_id(gs, user, msg['id'])
            # if not none move further to process the message
            if raw is not None:
                process_raw_msg(raw, lbl,msg['id'])
                # print Processed message count
                print("Processed", count, "of", num_msgs)
                count += 1

# save html file with content
def save_html(cont,name):
    Html_file= open(name,"w")
    Html_file.write(cont)
    Html_file.close()

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))

    # Call the Gmail API
    results = service.users().labels().list(userId='me').execute()
    # get all labels
    labels = results.get('labels', [])
    # loop through the each label
    for label in labels:
        # extract the messages in each label
        list_messages(service,'me',label['name'])

if __name__ == '__main__':
    main()
