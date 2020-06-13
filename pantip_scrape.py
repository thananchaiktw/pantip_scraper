import os
import time
import random
import requests

import re
import json
import codecs
import glob
import argparse

from bs4 import BeautifulSoup

headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Authorization': 'pantip.com',
    'Accept-encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'cache-control': 'no-cache'}

def delay(sec):
    time.sleep(sec)

class PantipScraper():
    def __init__(self):
        self.base_url = 'https://pantip.com/'
    
    def get_data(self, id):
        page_exist = True
        self.result = {
            "title":"",
            "date":0,
            "tag":[],
            "user":"",
            "message":"",
            "emoji_count":0,
            "emojis":[],
            "comment_count":0,
            "comments":[]
        }
        
        try:
            self.get_topic(id)
            params = {
                'tid':str(id),
                'param':'',
                'type':1,
                'time':random.random()
            }

            self.get_comment(params)
        except Exception as e:
            # print(e)
            page_exist = False
            
        return page_exist, self.result
    
    def get_topic(self, id):
        
        r = requests.get(self.base_url+'topic/'+str(id)) 
        soup = BeautifulSoup(r.content, 'html.parser')

        self.result['title'] = soup.find('h2',{'class':'display-post-title'}).text
        self.result['date'] = soup.find('abbr',{'class':'timeago'})['data-utime']
        self.result['tag'] = [t.text for t in soup.find_all('a',{'class':'cs-tag_topic_title'})]
        self.result['user'] = soup.find('a',{'class':'owner'}).text
        self.result['message'] = soup.find('div',{'class':'display-post-story'}).text
        self.result['message'] = self.result['message'].replace('&nbsp;', ' ').replace('\r', '').replace('\t', '')
        self.result['message'] = re.sub('<[^>]*>', '', self.result['message'])

        emoji = soup.find_all('span', {'class':'emotion-choice-score'})
        self.result['emotion_count'] = soup.find('span', {'class':'emotion-score'}).text
        self.result['emotion'] = {
            "like": int(emoji[1].text),
            "laugh": int(emoji[2].text),
            "love":int(emoji[3].text),
            "impress":int(emoji[4].text),
            "scary":int(emoji[5].text),
            "surprised":int(emoji[6].text)
        }
    
    def get_comment(self, params):
        # print(True)
        r = requests.get(self.base_url+'forum/topic/render_comments', params=params, headers=headers) 
        data = r.json()
        if 'comments' in data.keys():
            self.result['comment_count'] = data['count']
            for comment in data['comments']:
                if 'message' in comment.keys():
                    comment['message'] = re.sub('<div class="spoil-style" style="display:none;">(.|\n)*?</div>', '', comment['message'])
                    comment['message'] = re.sub('<[^>]*>', '', comment['message'])
                    comment['message'] = comment['message'].replace('&nbsp;', ' ').replace('\r', '').replace('\t', '')
                    comment['message'] = comment['message'].encode('utf-8').decode('utf-8')
                    if 'replies' in comment.keys():
                        for reply in comment['replies']:
                            reply['message'] = re.sub('<div class="spoil-style" style="display:none;">(.|\n)*?</div>', '', reply['message'])
                            reply['message'] = re.sub('<[^>]*>', '', reply['message'])
                            reply['message'] = reply['message'].replace('&nbsp;', ' ').replace('\r', '').replace('\t', '')
                            reply['message'] = reply['message'].encode('utf-8').decode('utf-8')
                self.result['comments'].append(comment)
                
            if len(self.result['comments']) < self.result['comment_count']:
                # print(True)
                _params = {
                    'tid':params['tid'],
                    'param':'page'+str(data["paging"]["page"]+1),
                    'type':1,
                    'page':data["paging"]["page"]+1,
                    'parent':data["paging"]["page"]+1,
                    'expand':','.join([str(i) for i in range(int(data["paging"]["page"]+1))]),
                    'time':random.random()
                }
                delay(1)
                self.get_comment(_params)

    
if __name__ == "__main__":
    scraper = PantipScraper()
    parser = argparse.ArgumentParser(description="Scrape text from www.pantip.com")
    parser.add_argument("--path", type=str, default="pantip/json")
    parser.add_argument("--sleep", type=int, default=5)
    args = parser.parse_args()
    
    start_id = 30006510
    index = 0
    files = sorted(glob.glob(args.path+"/*.json"))

    if len(files)>0: ## check for continue scrape from last time
        start_id = int(re.findall(r'\d+', files[-1])[0])+1 # get id number
        
    max_page_exist = 10 
    not_exist_count = 0
    # get_count = 0
    
    while(1):
        print("Start scrapping from https://pantip.com/topic/"+str(start_id+index))
        exist, data = scraper.get_data(start_id+index)
        
        with open(os.path.join(args.path, "pantip_{}.json".format(start_id+index)), 'w+') as file:
            json.dump(data, file, ensure_ascii=False)
        
        if not exist:
            not_exist_count+=1
        else:
            not_exist_count=0
            
        if not_exist_count > max_page_exist: ## if number of page exist to limit decide that no more pages
            break
        

        index +=1

        delay(args.sleep)
    print("Finish")
    # print(_d)
    # pass