import os
from urllib import request
from urllib.error import HTTPError


def get_links_from_text(text, min_len, max_len=14):
    
    html_list = text.split("href")[1:]
    
    links = []
    
    for link in html_list:
        # The links we want are in quotes
        link = link[link.index('"')+1:]
        link = link[:link.index('"')]
        if min_len <= len(link) <= max_len:
            links.append(link)
    
    return links


def web_scraper(url):

    # The Masque of the Red Death sort 726
    
    urls = [url]
    
    html_file = request.urlopen(url)
    html_data = html_file.read().decode()
    
    links = get_links_from_text(html_data, 9, 13)
    
    for book_link in links:
        try:
            
            book_file = request.urlopen("https://www.gutenberg.org" + book_link + ".txt.utf-8")
        
        except HTTPError:
            try:
                book_num = book_link.split("/")[-1]
                try:
                    # book_num = book_link.split("/")[-1]
                    new_link = "https://www.gutenberg.org/files/" + book_num + "/" + book_num + "-0.txt"
                    print(book_link, new_link)
                    book_file = request.urlopen(new_link)
                    
                except HTTPError:
                    new_link = "https://www.gutenberg.org/cache/epub/" + book_num + "/pg" + book_num + ".txt"
                    print(book_link, new_link)
                    book_file = request.urlopen(new_link)

            except Exception as e:
                print("https://www.gutenberg.org" + book_link + ".txt.utf-8", "idk why, but this wasn't allowed to open because", e, type(e))
                continue
        
        try:
            book_data = book_file.read().decode()
            # print([f"{book_data[:1000]}"])
                
            book_name = book_data.split("Title: ")[1]
            book_name = book_name.split("\r")[0]
            
            if len(book_name) > 100:
                book_name = book_data.split("Title: ")[1]
                book_name = book_name.split("\n")[0]
                print(book_name)
                
            book_author = book_data.split("Author: ")[1]
            book_author = book_author.split("\r")[0]
            
            if len(book_author) > 100:
                book_author = book_data.split("Author: ")[1]
                book_author = book_author.split("\n")[0]
                print(book_author)
                
            book_language = book_data.split("Language: ")[1]
            book_language = book_language.split("\r")[0]
            
            if len(book_language) > 50:
                book_language = book_data.split("Language: ")[1]
                book_language = book_language.split("\n")[0]
                print(book_language)
                
            book = {"name": book_name, "author": book_author, "language": book_language, "text": book_data}
            
            yield book
        
        except IndexError as i:
            print("ahhh", i)
        
        except Exception as e:
            print("oh no!", e)
            
        finally:
            
            book_file.close()

            
    html_file.close()


def download_books(root_url):
    
    urls = [root_url]

    for x in range(726, 1000, 25):
        urls.append(root_url + f"&start_index={x}")
    
    for url in urls:
        
        print(url)
        
        for book in web_scraper(url):
            
            path = "Books"
            
            try:
                os.mkdir(os.path.join(path, book["language"]))
            except FileExistsError:
                pass
            
            path = os.path.join(path, book["language"])
            
            try:
                os.mkdir(os.path.join(path, book["author"]))
            except FileExistsError:
                pass
            
            try:
                with open(os.path.join(path, book["author"], book["name"]), "w") as book_file:
                    book_file.write(book["text"])
            except Exception:
                continue


if __name__ == "__main__":
    root_urls = ["https://www.gutenberg.org/ebooks/search/?sort_order=title", "https://www.gutenberg.org/ebooks/search/?sort_order=release_date"] # "https://www.gutenberg.org/ebooks/search/?sort_order=downloads"
    for root_url in root_urls:
        # title 726
        download_books(root_url)
