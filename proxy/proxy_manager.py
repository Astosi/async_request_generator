import os
import sys


# Get the directory path of the logs module
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the logs directory to the Python path
sys.path.append(app_dir)

from logs.str_tool import boxify

import argparse
import csv

import requests
from bs4 import BeautifulSoup
import schedule
import time
import itertools
import sys

from logs.Logger import get_logger

logger = get_logger(__name__)


class ProxyManager:
    def __init__(self, proxy_list_size: int, schedule_period=1, filepath='data/proxies.csv'):
        self.filepath = filepath
        self.proxy_list_size = proxy_list_size
        self.schedule_period = schedule_period
        self.proxies = []
        self.proxy_cycle = itertools.cycle(self.proxies)
        self.load_proxies()

    @staticmethod
    def testing_proxy() -> str:
        proxy_url = 'zproxy.lum-superproxy.io:22225'
        proxy_user = 'brd-customer-hl_d2e1ca27-zone-data_center'
        proxy_password = 'dr9llhmkxpzi'

        return f'http://{proxy_user}:{proxy_password}@{proxy_url}'


    # Convert proxies into string format
    @staticmethod
    def proxy_to_string(proxy: dict) -> [str, None]:
        if proxy:
            return f"http://{proxy['ip']}:{proxy['port']}"
        return None

    def scrape_proxies_p2(self):
        url = 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=https&timeout=500&country=all&ssl=all&anonymity=all'
        response = requests.get(url)
        proxies_data = response.text.split('\r\n')[:-1]

        proxies = []

        for data in proxies_data:
            proxy_info = data.split(':')
            proxy = {
                'ip': proxy_info[0],
                'port': proxy_info[1],
                'country': '',
                'https': 'no',
                'rank': 5
            }
            proxies.append(proxy)

        logger.info(f"Found {len(proxies)} proxies from ProxyScrape")
        return proxies

    def scrape_proxies_p1(self):
        logger.info("Getting free proxies")
        url = 'https://www.sslproxies.org/'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        proxies_table = soup.find(class_='table table-striped table-bordered')

        proxies = []

        for row in proxies_table.tbody.find_all('tr'):
            columns = row.find_all('td')
            proxy = {
                'ip': columns[0].string,
                'port': columns[1].string,
                'country': columns[3].string,
                'https': 'yes' if columns[6].string == 'yes' else 'no',
                'rank': 5
            }
            proxies.append(proxy)

        logger.info(f"Found {len(proxies)} proxies from sslproxies.org")
        return proxies

    def save_proxies_to_csv(self):
        with open(self.filepath, 'w', newline='') as csvfile:
            fieldnames = ['ip', 'port', 'country', 'https', 'rank']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for proxy in self.proxies:
                writer.writerow(proxy)

        logger.info(f"Saved {len(self.proxies)} proxies to csv")

    def load_proxies(self):
        self.proxies = []

        try:
            with open(self.filepath, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    proxy = {'ip': row['ip'], 'port': row['port'], 'country': row['country'], 'https': row['https'],
                             'rank': int(row['rank']) if row['rank'] else 0}
                    self.proxies.append(proxy)

            self.proxy_cycle = itertools.cycle(self.proxies)
            logger.critical(f"Loaded {len(self.proxies)} proxies from csv")

        except FileNotFoundError:
            logger.error("proxies.csv not found. Creating new file")

    def reset_proxies(self):
        self.proxies = []
        self.proxy_cycle = itertools.cycle(self.proxies)
        self.save_proxies_to_csv()

    def find_and_save_proxies(self):
        self.load_proxies()
        new_proxies = self.scrape_proxies_p1()
        new_proxies_p2 = self.scrape_proxies_p2()

        new_proxies.extend(new_proxies_p2)

        # Get the proxies only with rank > 3, the others will be replaced
        self.proxies = [proxy for proxy in self.proxies if proxy['rank'] > 3]

        if len(self.proxies) >= self.proxy_list_size:
            return

        # Get the number of proxies needed to reach the proxy_list_size
        proxies_needed = self.proxy_list_size - len(self.proxies)
        logger.info(f"Need {proxies_needed} proxies to reach {self.proxy_list_size} proxies")

        # Add only the required number of new proxies
        new_proxies = new_proxies[:proxies_needed]

        # Remove the proxies that already exist in the list
        existing_ips = [proxy['ip'] for proxy in self.proxies]
        new_proxies = [proxy for proxy in new_proxies if proxy['ip'] not in existing_ips]

        self.proxies.extend(new_proxies)
        self.proxies = sorted(self.proxies, key=lambda x: x['rank'], reverse=True)[:self.proxy_list_size]

        self.proxy_cycle = itertools.cycle(self.proxies)
        self.save_proxies_to_csv()

        logger.info(f"Updated proxy list with {len(new_proxies)} new proxies")

    def get_proxy(self):
        try:
            return next(self.proxy_cycle)
        except StopIteration:
            # If the proxy is not found in the list itertools throws this error.
            logger.warning("Proxy list is empty. Loading proxies from csv")
            time.sleep(5)
            self.load_proxies()
            return next(self.proxy_cycle)

    def update_proxy_rank(self, proxy: dict, delta: int):
        try:
            proxy_index = next(
                i for i, p in enumerate(self.proxies) if p['ip'] == proxy['ip'] and p['port'] == proxy['port'])
        except StopIteration:
            logger.warning(f"Proxy {proxy['ip']}:{proxy['port']} not found in the list.")
            return

        logger.info(f"Updating proxy rank for {proxy['ip']}:{proxy['port']} with "
                    f"rank {self.proxies[proxy_index]['rank']} by {delta}")

        proxy = self.proxies[proxy_index]
        proxy_rank = proxy['rank']

        # I set 20 as the maximum rank value because I don't want to have a proxy with rank 1000,
        # it will take quite a long time to pop it from the list
        new_rank = proxy_rank + delta if proxy_rank + delta <= 20 else proxy_rank

        proxy['rank'] = new_rank

        if new_rank < 0:
            self.proxies.pop(proxy_index)
        else:
            # Move the updated proxy to its new position in the sorted list
            while (proxy_index > 0 and
                   self.proxies[proxy_index]['rank'] > self.proxies[proxy_index - 1]['rank']):
                self.proxies[proxy_index], self.proxies[proxy_index - 1] = self.proxies[proxy_index - 1], self.proxies[
                    proxy_index]
                proxy_index -= 1

            while (proxy_index < len(self.proxies) - 1 and
                   self.proxies[proxy_index]['rank'] < self.proxies[proxy_index + 1]['rank']):
                self.proxies[proxy_index], self.proxies[proxy_index + 1] = self.proxies[proxy_index + 1], self.proxies[
                    proxy_index]
                proxy_index += 1

        self.proxy_cycle = itertools.cycle(self.proxies)
        self.save_proxies_to_csv()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=0,
                        help="Interval (in seconds) to refresh the proxy pool")
    parser.add_argument('--proxy_count', type=int, default=50,
                        help='Number of proxies to maintain in the pool')
    args = parser.parse_args()

    print(boxify(header="~~~~~~~~~~~~~~~ Proxy Manager ~~~~~~~~~~~~~~~",
                 params={'Interval': args.interval, 'Proxy Count': args.proxy_count}), '\n')

    proxy_manager = ProxyManager(args.proxy_count, args.interval)
    proxy_manager.find_and_save_proxies()

    schedule.every(args.interval).seconds.do(proxy_manager.find_and_save_proxies)

    while True:
        schedule.run_pending()
        time.sleep(1)
