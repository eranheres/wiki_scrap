import argparse
import wptools
import requests
import pathlib
import os.path
import json
import csv
import progressbar
import shutil
import time
from pytrends.request import TrendReq


def data_filename(folder):
    return os.path.join(folder, folder+".json")


def csv_filename(folder):
    return os.path.join(folder, folder+".csv")


def download_image(image_name, url, dest_folder):
    ext = pathlib.Path(url).suffix
    path = dest_folder+"/"+image_name+ext
    #print("downloading {}".format(path))
    if os.path.exists(path):
        return
    while True:
        r = requests.get(url, stream=True)
        if r.status_code!=200:
            time.sleep(1)
            continue
        with open(path, 'wb') as out_file:
            shutil.copyfileobj(r.raw, out_file)
        del r
        break


def info_from_file(folder):
    filename = data_filename(folder)
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as json_file:
        info = json.load(json_file)
    return info


def download_images(folder):
    info = info_from_file(folder)
    i = 0
    with progressbar.ProgressBar(max_value=len(info)) as bar:
        for page in info:
            if page['ok']:
                download_image(page['title'], page['url'], dest_folder=folder)
            i = i+1
            bar.update(i)


def create_csv(folder):
    info = info_from_file(folder)
    rows = []
    with open(csv_filename(folder), "w", newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for title in info:
            if not title['ok']:
                continue
            rows.append([
                '<img src="{}{}">'.format(title['title'], pathlib.Path(title['url']).suffix),
                '<h1>{}</h1>'.format(title['title']),
                title['extract'].replace('\n', ''),
                ' '.join(title['tags'])
            ])
        writer.writerows(rows)


def save_info(info, folder):
    path = data_filename(folder)
    with open(path, 'w') as handler:
        handler.write(json.dumps(info, indent=4))

import logging

def update_popularity(folder):
    pytrends = TrendReq(hl='en-US', tz=360, timeout=5, retries=30, backoff_factor=0.5)
    titles = info_from_file(folder)
    count = 0
    kw_list = ['בר רפאלי']
    with progressbar.ProgressBar(max_value=len(titles)) as bar:
        for title in titles:
            count = count + 1
            bar.update(count)
            title_name = title['title']
            #print(title_name)
            if 'popularity' in title or not title['ok'] or kw_list[0] == title_name:
                continue
            kw_list.append(title['title'])
            try:
                pytrends.build_payload(kw_list, timeframe='today 5-y')
                ds = pytrends.interest_over_time()
                title['popularity'] = int(ds[title_name].sum())
            except:
                d = pytrends.results()
                print("failed to load {}".format(str(kw_list)))
            if count % 10 == 0:
                save_info(info=titles, folder=folder)
            kw_list = ['בר רפאלי']


def download_category(category, lang, name, include_subcat, results, level=""):
    if not os.path.exists(name):
        os.mkdir(name)
    wiki_cat = wptools.category(category, lang=lang, silent=True)
    wiki_cat.get_members()
    category_short = category.split(":")[1]
    print(level+" Scrapping category:{}".format(category))
    if category_short in [x['title'] for x in wiki_cat.data['members']]:
        l = list(filter(lambda x: x['title'] == category_short, wiki_cat.data['members']))
        wiki_cat.data['members'] = l
        if 'subcategories' in wiki_cat.data:
            wiki_cat.data.pop('subcategories')
    if include_subcat and 'subcategories' in wiki_cat.data:
        for subcat in wiki_cat.data['subcategories']:
            download_category(subcat['title'], lang, name, include_subcat, results, level+">")
    for topic in wiki_cat.data['members']:
        title = topic['title']
        if title in [x['title'] for x in results]:
            #print("title:{} ----- (exists)".format(title))
            continue
        try:
            page = wptools.page(title, lang=lang, silent=True).get_query()
        except ValueError:
            results.append({"title": title, "ok": False})
            continue
        thumb_img = page.images(fields='url', token='thumb')
        if thumb_img is None or len(thumb_img) == 0 or thumb_img[0]['url'] is None:
            print("title:{} ----- (no image)".format(title))
            results.append({"title": title, "ok": False})
            continue
        extract = ""
        if 'extract' in page.data:
            extract = page.data['extract']
        page.get_more()
        tags = [tag.split(':')[1].replace(' ', '_') for tag in page.data['categories']]
        url = thumb_img[0]['url']
        info = {"title": title, "ok": True, "url": url, "extract": extract, "tags": tags}
        print("title:{} info:{}".format(title, extract[:100].replace('\n', '')))
        results.append(info)
        save_info(info=results, folder=name)


def main():
    parser = argparse.ArgumentParser(description='Download Wikipedia category images')
    parser.add_argument('--categories', nargs="+")
    parser.add_argument('--lang')
    parser.add_argument('--name', default="")
    parser.add_argument('--skip_scrap', action="store_true")
    parser.add_argument('--exclude_subcat', action="store_true")
    args = parser.parse_args()
    categories = args.categories
    name = args.name
    skip_scrap = args.skip_scrap
    exclude_subcat = args.exclude_subcat

    results = info_from_file(name)
    if not skip_scrap:
        for category in categories:
            download_category(category,
                          args.lang,
                          name,
                          include_subcat=not exclude_subcat,
                          results=results)
    update_popularity(folder=name)
    download_images(folder=name)
    create_csv(folder=name)


if __name__ == "__main__":
    main()

