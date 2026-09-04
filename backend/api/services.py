import json
import random
import re
import time
from io import TextIOWrapper
from queue import Queue
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urlunparse, urljoin

import nltk
import usaddress

nltk.download('punkt_tab')
import openpyxl
import requests
from bs4 import BeautifulSoup

STREET_TYPES = [
    "Avenue", "Ave", "Boulevard", "Blvd", "Street", "St", "Road", "Rd",
    "Drive", "Dr", "Lane", "Ln", "Way", "Court", "Ct", "Place", "Pl",
    "Terrace", "Ter", "Highway", "Hwy", "Parkway", "Pkwy", "Circle", "Cir"
]

class RegexPattern:
    def __init__(self):
        self.url = re.compile(r"https?://(www\.)?\S+")
        self.phone = re.compile(r"(?:\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\.]\w{4}")

        # FIXME: Address validation issue. Need to find third-party libraries other than regular expression standard library.
        self.address = re.compile(
            fr"\d{{2,5}}[a-zA-Z0-9,.# ]+(?:{"|".join(STREET_TYPES)})[a-zA-Z0-9,.# ]+CA(?:,?\s\d{{5}}(?:-\d+)?)",
            re.IGNORECASE)
        self.email = re.compile(r"[a-zA-Z0-9-._]+@[a-zA-Z0-9-._]+\.(?:com|org|net|gov|xyz|edu|la)", re.IGNORECASE)

        self.sdp = re.compile(r"Self[\s\-]?Determination[\s\-]?(?:Program)?|SDP", re.IGNORECASE)

class WebCrawler:
    def __init__(self, max_pages: int=float("inf"), user_agent: str="*"):
        self.regex_pattern = RegexPattern()
        self.max_pages = max_pages
        self.visited_urls = set()
        self.robots_domain = {}

        self.url_frontier = Queue()
        self.programs_url_set = set()

        self.vendor_name = ""       # Based on main title page displayed on tab.
        self.main_vendor_url = ""
        self.has_sdp = False
        self.phone_set = set()
        self.address_hash = dict()
        self.email_set = set()

        self.user_agent = user_agent
        self.headers = {"User-agent": self.user_agent}
        self.robots_txt = "/robots.txt"


    def _is_valid_url(self, url: str) -> bool:
        return re.match(self.regex_pattern.url, url) is not None

    def _is_in_start_path(self, base_url: str, url: str) -> bool:
        start_parse = urlparse(base_url)
        target_parse = urlparse(url)

        start_domain = start_parse.netloc.replace("www.", "")
        target_domain = target_parse.netloc.replace("www.", "")
        if not start_domain == target_domain or target_domain.endswith("." + start_domain):
            return False

        start_path = start_parse.path.rstrip("/") + "/"
        target_path = target_parse.path.rstrip("/") + "/"
        return target_path.startswith(start_path)

    def _parse_robots_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        robots_url = urlunparse((parsed_url.scheme, parsed_url.netloc, self.robots_txt, "", "", ""))
        return robots_url

    def _fetch_robots(self, url: str) -> RobotFileParser:
        robots_url = self._parse_robots_url(url)
        response = requests.get(robots_url, headers=self.headers, timeout=5)

        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(response.text.splitlines())

        response.close()

        return rp

    def norm_phone(self, phone: str) -> str:
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]

        # (000) 000-0000
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    def norm_address(self, address: str) -> list[str]:
        addr = re.sub(r"[^a-zA-Z0-9\s]", "", address)
        tokenizer = nltk.word_tokenize(addr)
        tokenizer = " ".join(tokenizer).title()

        address_tag = usaddress.tag(tokenizer)[0]
        street_tag_list = []

        for key, value in address_tag.items():
            if key == "PlaceName":
                break

            street_tag_list.append(value)

        street = " ".join(street_tag_list)
        city = address_tag.get("PlaceName", "")
        state = address_tag.get("StateName", "").upper()
        zipcode = address_tag.get("ZipCode", "")

        return [street, city, state, zipcode]

    def extract_info(self, soup: BeautifulSoup) -> None:
        text = soup.get_text()

        if self.vendor_name == "":
            title = soup.title.string
            self.vendor_name = title

        for phone in self.regex_pattern.phone.findall(text):
            norm = self.norm_phone(phone)
            self.phone_set.add(norm)

        for address in self.regex_pattern.address.findall(text):
            try:
                street, city, state, zipcode = self.norm_address(address)
                self.address_hash[street] = [street, city, state, zipcode]
            except usaddress.RepeatedLabelError as e:
                print(e)

        for email in self.regex_pattern.email.findall(text):
            email = email.lower()
            self.email_set.add(email)

        if not self.has_sdp:
            is_sdp_included = self.regex_pattern.sdp.search(text)
            if is_sdp_included is not None:
                self.has_sdp = True

    def extract_program_info(self, soup: BeautifulSoup) -> None:
        pass

    def get_htmlparser_soup(self, website: str) -> BeautifulSoup:
        response = requests.get(website, headers=self.headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        response.close()

        return soup

    def crawl(self, url: str) -> None:
        if not self._is_valid_url(url):
            return

        self.url_frontier.put(url)
        self.visited_urls.add(url)
        self.main_vendor_url = url
        while self.url_frontier.qsize() > 0:
            website = self.url_frontier.get()
            print(website)
            base_domain = urlparse(website).netloc

            if base_domain not in self.robots_domain:
                try:
                    rp = self._fetch_robots(website)
                except requests.exceptions.Timeout as e:
                    print(e)
                    continue

                self.robots_domain[base_domain] = rp

            is_crawlable = self.robots_domain[base_domain].can_fetch(self.user_agent, website)
            if not is_crawlable:
                print("No Permission to Crawl!")
                continue

            try:
                soup = self.get_htmlparser_soup(website)
            except Exception as e:
                print(e)
                continue

            self.extract_info(soup)

            links = soup.find_all("a")
            for link in links:
                if len(self.visited_urls) >= self.max_pages:
                    break

                if not link.has_attr("href"):
                    continue

                curr_link = str(link["href"])

                # Skip links defined in input
                if curr_link.rstrip("/") in self.programs_url_set:
                    continue

                if not self._is_valid_url(curr_link):
                    curr_link = urljoin(url, curr_link)

                if curr_link in self.visited_urls or not self._is_in_start_path(url, curr_link):
                    continue

                self.url_frontier.put(curr_link)
                self.visited_urls.add(curr_link)

            crawl_delay = self.robots_domain[base_domain].crawl_delay(self.user_agent)
            if crawl_delay is not None:
                time.sleep(crawl_delay)

    def get_data(self) -> dict:
        return {
            "name": self.vendor_name,
            "domain": self.main_vendor_url,
            "has_sdp": self.has_sdp,
            "main": {
                "location": list({
                    "street": value[0],
                    "city": value[1],
                    "state": value[2],
                    "zipcode": value[3],
                } for value in self.address_hash.values()),
                "contact": [
                    {
                        "email": list(self.email_set),
                        "phone": list(self.phone_set),
                    }
                ]
            }
        }

    def reset(self):
        self.url_frontier.empty()
        self.visited_urls.clear()
        self.robots_domain.clear()

        self.vendor_name = ""
        self.main_vendor_url = ""
        self.has_sdp = False
        self.phone_set.clear()
        self.address_hash.clear()
        self.email_set.clear()

    # def write_data_to_file(self, finfo: TextIOWrapper, input_display: str):
    #     finfo.write(f"{input_display}\n")
    #     finfo.write(f"PHONE:\n-{"\n-".join(phone for phone in self.phone_set)}\n\n")
    #     finfo.write(f"ADDRESS:\n-{"\n-".join(address for address in self.address_set)}\n\n")
    #     finfo.write(f"EMAIL:\n-{"\n-".join(email for email in self.email_set)}\n\n")
    #     # finfo.write(f"Self-Determination Program: {is_sdp}\n\n")
    #     finfo.write(f"{"":-^40}\n")

# For testing purposes, we'll pick random websites in each run to control web traffic.
# FIXME: Loop ends early post function call.
def pick_n_websites(n: int, vendor_col: list) -> list:
    random_ws = random.sample(vendor_col, n)
    return random_ws

# def main(input_path: str):
#     crawler = WebCrawler(max_pages=10)
#     with open("vendor_info.txt", "w") as finfo:
#         finfo.write(f"Dev Build: Not a final product and certain functionalities may not behave normally!\n\n")
#         finfo.write(f"{"[Vendor List]":=^30}\n")
#         finfo.write(f"{"":-^40}\n")
#         if input_path.startswith("http"):
#             crawler.crawl(input_path)
#             crawler.write_data_to_file(finfo, input_path)
#             crawler.clear()
#         else:
#             wb = openpyxl.load_workbook(input_path)
#             ws = wb.active
#
#             vendor_col = ws["A"]
#             # vendor_col = pick_n_websites(5, vendor_col)
#             for vendor in vendor_col:
#                 is_sdp = False
#                 if not vendor.hyperlink:
#                     continue
#
#                 base_url = vendor.hyperlink.target
#                 try:
#                     crawler.crawl(base_url)
#                 except Exception as e:
#                     print(e)
#                 crawler.write_data_to_file(finfo, base_url)
#                 crawler.clear()
#             wb.close()
#         finfo.close()

def main(input_path: str, output_filename: str) -> None:
    if not output_filename.endswith(".json"):
        print("File must end in .json!")
        return

    crawler = WebCrawler(max_pages=20, user_agent="AbilityFamilyBOT")
    with open(input_path, "r") as finfo:
        vendors = json.load(finfo)
        vendors = pick_n_websites(10, vendors)
        finfo.close()

    with open(output_filename, "w") as fout:
        data = []
        for vendor in vendors:
            vendor_url = vendor.get("vendor_url", None)
            if vendor_url is None:
                continue

            vendor_url = vendor_url.rstrip("/") + "/"

            vendor_programs = vendor.get("vendor_programs", [])
            for path in vendor_programs:
                crawler.programs_url_set.add(path.get("path"))

            crawler.crawl(vendor_url)
            for program in vendor_programs:
                url_path = vendor_url + program.get("path", "")

                # The path given will scan adjacent hyperlinks to gather each program information.
                # If false, any hyperlinks included are ignored and will crawl only that page.
                if program.get("scan_programs"):
                    crawler.crawl(url_path)
                else:
                    soup = crawler.get_htmlparser_soup(url_path)
                    crawler.extract_program_info(soup)

            crawl_data = crawler.get_data()
            data.append(crawl_data)
            crawler.reset()

        json.dump(data, fout, indent=4)
        fout.close()

if __name__ == "__main__":
    main("vendor_input.json", "vendor_output.json")
