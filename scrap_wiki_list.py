
import wptools
import requests
import pathlib

lang = 'he'

def get_category_pages(category):
    wiki_cat = wptools.category(category, lang=lang)
    wiki_cat.get_members()
    results = []
    for topic in wiki_cat.data['members']:
        title = topic['title']
        try:
            page = wptools.page(title, lang=lang).get_query()
        except ValueError:
            continue
        thumbimg = page.images(fields='url', token='thumb')
        if thumbimg is None or len(thumbimg) == 0 or thumbimg[0]['url'] is None:
            continue
        url = thumbimg[0]['url']
        results.append({"title": title, "url":url})
    return results


def download_image(image_name, url):
    img_data = requests.get(url).content
    ext = pathlib.Path(url).suffix
    with open(image_name+"."+ext, 'wb') as handler:
        handler.write(img_data)


category = 'Category:Best_Actor_Academy_Award_winners'
category = 'קטגוריה:שרי ממשלת ישראל ה-35'
results = get_category_pages(category)
for result in results:
    print(result)
    download_image(result["title"], result["url"])
u = 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Benny_morris.jpg/214px-Benny_morris.jpg'
download_image("t", u)
