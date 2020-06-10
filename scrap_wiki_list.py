
import wptools
import requests
import pathlib

def get_category_pages(category):
    wiki_cat = wptools.category(category)
    wiki_cat.get_members()
    results = []
    for topic in wiki_cat.data['members'][:5]:
        title = topic['title']
        try:
            page = wptools.page(title).get_query()
        except ValueError:
            continue
        thumbimg = page.images(fields='url', token='thumb')
        url = thumbimg[0]['url']
        results.append({"title": title, "url":url})
    return results


def download_image(image_name, url):
    img_data = requests.get(url).content
    ext = pathlib.Path(url).suffix
    with open(image_name+"."+ext, 'wb') as handler:
        handler.write(img_data)


category = 'Category:Best_Actor_Academy_Award_winners'
results = get_category_pages(category)
print(results)
for result in results:
    download_image(result["title"], result["url"])
