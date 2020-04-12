import requests
import json
from datetime import date
import glob
import os
from os import path
import shutil
from config import *
# need groupme api token
# need DeepAI image similarity api token

#### This program will return the name of the memeber of the groupme who reposts a meme that is:
####        (1) identical to a meme in database
####        (2) is not the same message


class DetectRepost:
    def __init__(self, input_name):
        self.name = input_name
        self.group_id = self.get_group_id()
        self.count = self.get_count()

    def get_group_id(self):
        endpoint = f'https://api.groupme.com/v3/groups?token={GM_TOKEN}'
        response = requests.get(endpoint)
        response = json.loads(response.text)
        response = response['response']
        for i in range(0, len(response)):
            if response[i]['name'] == self.name:
                return response[i]['group_id']

    def get_count(self):
        count = self.get_messages()['response']['count']
        return count

    def get_messages(self):
        endpoint = f'https://api.groupme.com/v3/groups/{self.group_id}/messages?limit=10&token={GM_TOKEN}'
        response = requests.get(endpoint)
        messages = json.loads(response.text)
        return messages

    def get_urls_of_memes(self, messages):
        response = messages['response']['messages']
        urls = []
        for i in range(0, len(response)):
            if len(response[i]['attachments']) > 0:
                type = response[i]['attachments'][0]['type']
                if (type == 'image'):
                    url = response[i]['attachments'][0]['url']
                    likes = len(response[i]['favorited_by'])
                    if (likes >= 0) & (type == 'image'):
                        urls.append(url)
        return urls

    def download_images(self, meme_url_list):
        today = date.today()
        for i in range(len(meme_url_list)):
            count = self.count - i
            img_data = requests.get(meme_url_list[i]).content
            filename = f'meme_{today}_{count}.jpeg'
            with open(filename, 'wb') as handler:
                handler.write(img_data)

    def get_meme_messages(self, messages):
        response = messages['response']['messages']
        meme_messages = []
        for i in range(0, len(response)):
            if len(response[i]['attachments']) > 0:
                type = response[i]['attachments'][0]['type']
                if (type == 'image'):
                    if (type == 'image'):
                        meme_messages.append(response[i])
        return meme_messages

################################################################

def similar(file1_path, file2_path):
    r = requests.post(
        "https://api.deepai.org/api/image-similarity",
        files={
            'image1': open(file1_path, 'rb'),
            'image2': open(file2_path, 'rb'),
        },
        headers={'api-key': DEEP_AI_KEY}
    )
    distance = r.json()['output']['distance']
    return distance

################################################################

def find_repost(group_name):
    detect_repost = DetectRepost(group_name)
    messages = detect_repost.get_messages()
    urls = detect_repost.get_urls_of_memes(messages)
    detect_repost.download_images(urls)

    new_memes_list = glob.glob("/Users/Garrett/Desktop/Projects/GroupMeThanos/*jpeg")
    old_memes_list = glob.glob("/Users/Garrett/Desktop/Projects/GroupMeThanos/MemeDB/*jpeg")

    # if every old meme is to be compared, set amount_ago to negative number. otherwise, set amount ago to as far
    # back to look at old memes e.g. if amount_ago = 20 you would compare every new meme to the last 20 memes
    amount_ago = -1
    if amount_ago < 0:
        most_recent_memes = old_memes_list
    else:
        try:
            most_recent_memes = old_memes_list[len(old_memes_list) - amount_ago:len(old_memes_list)]
        except:
            most_recent_memes = old_memes_list

    # compares all new memes to all old memes to see if any are duplicates. saves duplicates
    indices_of_reposts = []
    new_memes_list = new_memes_list[::-1]
    for new_meme in new_memes_list:
        # if the new_meme is not already in database
        found_repost = 0
        if not path.exists(new_meme[:46]+"MemeDB/"+new_meme[46:]):
            for old_meme in most_recent_memes:
                if found_repost != 1:
                    print('comparing', new_meme, 'with', old_meme)
                    if similar(new_meme, old_meme) <= 2:
                        # if not the same meme
                        count_length = len(str(detect_repost.count))
                        # maybe comparing different lengthed counts e.g. count 10 with 5
                        while (count_length != 0) & (found_repost != 1):
                            try:
                                if int(new_meme[len(new_meme) - (5 + count_length):len(new_meme) - 5]) != int(
                                        old_meme[len(old_meme) - (5 + count_length):len(old_meme) - 5]):

                                    indices_of_reposts.append(new_memes_list.index(new_meme))
                                    found_repost = 1
                                exit()
                            except:
                                count_length -= 1
        else:
            print(
                f'{new_meme} is already in DB ... checking {new_memes_list.index(new_meme) + 1}/{len(new_memes_list)}')


    if len(indices_of_reposts) == 0:
        print('no reposts detected')
    else:
        for repost_index in indices_of_reposts:
            memes = detect_repost.get_meme_messages(messages)
            name = memes[repost_index]['name']
            sender_id = memes[repost_index]['sender_id']
            print(name, sender_id, "reposted!!!!")

    filenames_to_remove = glob.glob("/Users/Garrett/Desktop/Projects/GroupMeThanos/*jpeg")
    for filename in filenames_to_remove:
        try:
            shutil.move(filename, 'MemeDB')
        except:
            try:
                os.remove(filename)
            except:
                print(f'{filename} is in MemeDB')

if __name__ == "__main__":
    group_name = "UVa Chess Club"
    find_repost(group_name)



