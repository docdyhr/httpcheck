#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import requests


def get_page(url):
    try:
        res = requests.get(url, timeout=2)
        return res.status_code
    except requests.exceptions.ReadTimeout:
        return None


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--urlfile', type=argparse.FileType('rt'), default=sys.stdin)
    parser.add_argument('urls', nargs='*')
    args = parser.parse_args(argv)

    for url in args.urls:
        code = get_page(url)
        print(code, url)

    for line in args.urlfile:
        url = line.strip()
        code = get_page(url)
        print(code, url)


if __name__ == '__main__':
    main()
