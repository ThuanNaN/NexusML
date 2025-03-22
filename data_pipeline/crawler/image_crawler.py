import urllib.request
from threading import Thread
import time
import random
import os

class DownloadImagesFromUrls:
    def __init__(self, nThreads, urls, destinate_folder):
        self.nThreads = nThreads
        self.urls = urls
        self.n = len(urls)
        self.destinate_folder = destinate_folder

    def download_url(self, start, end):
        for i in range(start, end):
            a = random.random()
            try:
                urllib.request.urlretrieve(self.urls[i], f"{self.destinate_folder}/{a}.jpg")
            except:
                print(f"cannot access {self.urls[i]}")
            print('.', end=" ")

    def __call__(self):
        threads = []
        batch = self.n // self.nThreads
        for i in range(0, self.n, batch):
            start = i
            end = i + batch
            if end >= self.n:
                end = self.n
            threads.append(Thread(target=self.download_url, args=(start, end)))

        start = time.time()
        for i in range(self.nThreads):
            threads[i].start()
        for i in range(self.nThreads):
            threads[i].join()
        end = time.time()

        print(f"\nTime handle download urls = {end - start:.2f}s\n")

def get_image_from_txts(topic_names, topics):
    for dir, names in zip(topic_names, topics):
        dir_path_images = f"data_crawl/images"
        dir_path_urls = f"data/{dir}/urls"
        if not os.path.exists(dir_path_images):
            os.makedirs(dir_path_images)

        txts = [name for name in os.listdir(dir_path_urls) if name.endswith(".txt")]
        for txt in txts:
            folder_txt = f"{dir_path_urls}/{txt}"
            with open(folder_txt, "r") as f:
                content_txt = f.readlines()

            folder_image = f"{dir_path_images}/{txt}"
            if not os.path.exists(folder_image[:-4]):
                os.makedirs(folder_image[:-4])
            print(folder_image[:-4])

            n_threads = 10
            DownloadImagesFromUrls(min(n_threads, len(content_txt) // 2), content_txt, folder_image[:-4])()