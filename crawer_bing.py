from bing import search

keywords = [line.rstrip('\n') for line in open('keywords.txt')]

for words in keywords:
    for url in search(words, num=1, start=0):
        print(url)