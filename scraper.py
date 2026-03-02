import requests
from bs4 import BeautifulSoup
import json
import time

def fetch_page_data(start_index, active_session, root_url):
    target_url = f"{root_url}/solutions/products/product-catalog/?start={start_index}&type=1"
    try:
        raw_response = active_session.get(target_url, timeout=10)
        soup_content = BeautifulSoup(raw_response.content, "html.parser")
        found_items = []
        table_rows = soup_content.find_all("tr")
        for row in table_rows:
            link_tag = row.find("a")
            if not link_tag:
                continue
            item_name = link_tag.text.strip()
            item_path = link_tag.get("href", "")
            if not item_name or not item_path:
                continue
            item_url = root_url + item_path if item_path.startswith("/") else item_path
            type_badges = row.find_all("span", class_=lambda c: c and "product-catalogue__key" in c)
            item_types = [badge.text.strip() for badge in type_badges]
            all_cells = row.find_all("td")
            remote_flag = "No"
            adaptive_flag = "No"
            for cell in all_cells:
                green_dot = cell.find("span", class_=lambda c: c and "catalogue__circle" in c)
                if green_dot:
                    remote_flag = "Yes"
                    break
            if len(all_cells) >= 4:
                last_cell = all_cells[-1]
                adaptive_dot = last_cell.find("span", class_=lambda c: c and "catalogue__circle" in c)
                if adaptive_dot:
                    adaptive_flag = "Yes"
            found_items.append({
                "name": item_name,
                "url": item_url,
                "remote_support": remote_flag,
                "adaptive_support": adaptive_flag,
                "test_type": item_types,
                "description": "",
                "duration": 0
            })
        return found_items
    except Exception as err:
        print(f"Error at offset {start_index}: {err}")
        return []

def fetch_item_details(item_url, active_session):
    try:
        detail_page = active_session.get(item_url, timeout=10)
        detail_soup = BeautifulSoup(detail_page.content, "html.parser")
        desc_block = detail_soup.find("div", class_=lambda c: c and "product-catalogue__description" in c)
        item_description = desc_block.text.strip() if desc_block else ""
        if not item_description:
            meta_tag = detail_soup.find("meta", attrs={"name": "description"})
            item_description = meta_tag.get("content", "") if meta_tag else ""
        item_duration = 0
        duration_text = detail_soup.find(string=lambda t: t and "minute" in t.lower())
        if duration_text:
            words = duration_text.split()
            for i, word in enumerate(words):
                if "minute" in word.lower() and i > 0:
                    try:
                        item_duration = int(words[i - 1])
                        break
                    except ValueError:
                        pass
        return item_description, item_duration
    except Exception as err:
        print(f"Could not get details for {item_url}: {err}")
        return "", 0

def start_scraping():
    shl_root = "https://www.shl.com"
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    http_session = requests.Session()
    http_session.headers.update(request_headers)
    master_list = []
    seen_urls = set()
    print("=" * 50)
    print("Scraping SHL Individual Test Solutions...")
    print("=" * 50)
    for offset in range(0, 400, 12):
        print(f"Fetching page offset {offset}...")
        page_items = fetch_page_data(offset, http_session, shl_root)
        if not page_items:
            print("No more items found. Stopping.")
            break
        for item in page_items:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                master_list.append(item)
                print(f"  + {item['name']}")
        time.sleep(1.5)
    print(f"\nNow fetching details for {len(master_list)} assessments...")
    for idx, item in enumerate(master_list):
        print(f"  Detail {idx + 1}/{len(master_list)}: {item['name']}")
        item["description"], item["duration"] = fetch_item_details(item["url"], http_session)
        time.sleep(0.5)
    print(f"\nTotal collected: {len(master_list)}")
    if len(master_list) < 377:
        print("WARNING: Less than 377 found!")
    else:
        print("SUCCESS: 377+ assessments collected!")
    with open("assessments.json", "w", encoding="utf-8") as out_file:
        json.dump(master_list, out_file, indent=2, ensure_ascii=False)
    print("Saved to assessments.json!")

if __name__ == "__main__":
    start_scraping()
