# -*- coding:utf-8 -*-
import requests
import os
import time
import traceback
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys

# === Logger 类：用于同时输出到屏幕和文件 ===
class Logger(object):
    def __init__(self, filename="spider.txt", stream=sys.stdout):
        self.terminal = stream
        self.log = open(filename, "a", encoding="utf-8")
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.path.insert(0, sys.path[0]+"/../")

class FDroidSpider:
    def __init__(self,
                 base_list_url="https://f-droid.org/zh_Hans/packages/",
                 base_domain="https://f-droid.org",
                 download_dir=r"D:\LibProbe\whitebox_apk_source"):
        
        self.base_list_url = base_list_url
        self.base_domain = base_domain
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

        self.proxies = {
            "http": "http://127.0.0.1:10809",
            "https": "http://127.0.0.1:10809"
        }

    def get_categories(self):
        resp = requests.get(self.base_list_url, timeout=30, proxies=self.proxies)
        resp.encoding = 'utf-8'
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        category_list = []
        h3_tags = soup.find_all('h3')
        for h3_tag in h3_tags:
            cat_name = h3_tag.get_text(strip=True)
            p_tag = h3_tag.find_next_sibling('p')
            if p_tag:
                link_tag = p_tag.find('a')
                if link_tag:
                    cat_url = link_tag.get('href')
                    if cat_url:
                        full_cat_url = urljoin(self.base_domain, cat_url)
                        category_list.append((cat_name, full_cat_url))
        return category_list

    def parse_category_page(self, category_name, category_page_url):
        resp = requests.get(category_page_url, timeout=30, proxies=self.proxies)
        resp.encoding = 'utf-8'
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        page_h3 = soup.find('h3')
        page_cat_name = page_h3.get_text(strip=True) if page_h3 else category_name

        app_links = []
        package_headers = soup.find_all("a", class_="package-header")
        for header in package_headers:
            href = header.get('href')
            if href:
                full_link = urljoin(self.base_domain, href)
                app_links.append(full_link)

        next_page_url = None
        ul_nav = soup.find("ul", class_="browse-navigation")
        if ul_nav:
            li_next = ul_nav.find("li", class_="nav next")
            if li_next and li_next.find("a"):
                next_href = li_next.find("a").get('href', '')
                next_page_url = urljoin(self.base_domain, next_href)

        return page_cat_name, app_links, next_page_url
        
    def get_app_info_and_download_source(self, app_detail_url, app_type):
            try:
                resp = requests.get(app_detail_url, timeout=30, proxies=self.proxies)
                resp.encoding = 'utf-8'
                resp.raise_for_status()
                soup = BeautifulSoup(resp.content, 'html.parser')

                app_name_tag = soup.find('h3', class_='package-name')
                app_name = app_name_tag.get_text(strip=True) if app_name_tag else "未知"
                package_name = app_detail_url.strip('/').split('/')[-1]

                # 寻找源码 tarball 链接
                tarball_link = None
                latest_block = soup.find('li', class_='package-version', id='latest')
                if not latest_block:
                    all_versions = soup.find_all('li', class_='package-version')
                    latest_block = all_versions[0] if all_versions else None

                if latest_block:
                    a_tags = latest_block.find_all('a')
                    for a in a_tags:
                        href = a.get('href', '')
                        if href.endswith('_src.tar.gz'):
                            tarball_link = urljoin(self.base_domain, href)
                            break
                
                # 如果没找到下载链接，直接返回
                if not tarball_link:
                    print(f"[警告] 未找到源码 tarball: {app_name} ({package_name})")
                    return

                # 构建本地文件路径
                file_name = tarball_link.split('/')[-1]
                local_path = os.path.join(self.download_dir, file_name)

                # === 关键修改：检查文件是否已存在 ===
                # 如果存在，打印跳过信息并直接 return，不再执行后续下载代码
                if os.path.exists(local_path):
                    # 为了确保文件不是下载了一半的坏文件，你也可以在这里检查一下文件大小是否 > 0
                    if os.path.getsize(local_path) > 0:
                        print(f"[跳过] 源码已存在且不为空: {file_name}")
                        return
                    else:
                        print(f"[覆盖] 源码文件存在但大小为0，重新下载: {file_name}")

                # === 开始下载 ===
                print(f"[信息] 正在下载: {file_name}")
                start_time = time.time()
                r = requests.get(tarball_link, stream=True, proxies=self.proxies)
                r.raise_for_status()

                is_too_large = False
                with open(local_path, 'wb') as f:
                    total_downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_downloaded += len(chunk)
                            # 150MB 限制
                            if total_downloaded > 150 * 1024 * 1024:
                                print(f"[删除] 文件超过 150MB，停止下载: {file_name}")
                                is_too_large = True
                                break

                end_time = time.time()
                
                # 后处理：过大则删除
                if is_too_large:
                    if os.path.exists(local_path):
                        os.remove(local_path)
                        print(f"[已删除] 文件超限: {file_name}")
                else:
                    # 再次校验最终文件大小
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 150 * 1024 * 1024:
                        os.remove(local_path)
                        print(f"[已删除] 文件超限: {file_name}")
                    else:
                        print(f"[完成] 下载耗时 {end_time - start_time:.1f} 秒: {file_name}")

            except Exception as e:
                traceback.print_exc()
                print(f"解析详情失败: {app_detail_url}, 错误: {e}")
                return

    def run(self):
        categories = self.get_categories()
        print(f"[信息] 获取到 {len(categories)} 个分类。")
        if not categories:
            return

        for idx, (cat_name, cat_url) in enumerate(categories):
            print(f"\n\n===== [分类 {idx+1}/{len(categories)}] {cat_name} =====")
            
            page_url = cat_url
            page_count = 0
            MAX_PAGES = 25  # 设置最大爬取页数

            while page_url and page_count < MAX_PAGES:
                page_count += 1
                print(f"[分类] {cat_name} - 第 {page_count} 页: {page_url}")

                real_cat_name, app_links, next_page = self.parse_category_page(cat_name, page_url)
                
                for i, link in enumerate(app_links):
                    print(f"   [应用] {i+1}/{len(app_links)}: {link}")
                    self.get_app_info_and_download_source(link, app_type=real_cat_name)

                # 翻页逻辑
                if next_page:
                    page_url = next_page
                else:
                    print(f"[信息] 分类 {cat_name} 没有更多页面了。")
                    page_url = None

            print(f"[信息] 分类 '{cat_name}' 结束，共处理 {page_count} 页。")

        print("[信息] 所有任务结束。")

if __name__ == '__main__':
    # 启用日志重定向
    sys.stdout = Logger('spider.txt', sys.stdout)
    sys.stderr = Logger('spider.txt', sys.stderr)
    
    spider = FDroidSpider()
    spider.run()