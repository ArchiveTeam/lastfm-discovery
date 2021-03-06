import gzip
import re
import requests
import string
import sys
import time
import random
import os

DEFAULT_HEADERS = {'User-Agent': 'ArchiveTeam'}


class FetchError(Exception):
    '''Custom error class when fetching does not meet our expectation.'''


def main():
    # Take the program arguments given to this script
    # Normal programs use 'argparse' but this keeps things simple
    urlpart = sys.argv[1]
    item_value = sys.argv[2]
    item_type = sys.argv[3]
    output_filename = sys.argv[4]  # this should be something like myfile.txt.gz
    start_num = "1"

    if item_type == "forum":
        tries = 0
        start_num = "1"
        suffixes = string.digits
        for suffix in suffixes:
            while True:
                url = '{0}{1}'.format(urlpart, suffix)
                if tries > 20:
                    raise Exception('Too many retries, giving up.')
                try:
                    text = fetch(url)
                except FetchError:
                    print('Sleeping for some time...')
                    sys.stdout.flush()
                    time.sleep(15)
                else:
                    if text:
                        max_num = extract_pages(text)
                        if max_num:
                            end_num = str(max_num)
                    else:
                        end_num = "1"
                    break
                tries += 1

            assert start_num <= end_num

            print('Starting', start_num, end_num)
            sys.stdout.flush()

            gzip_file = gzip.GzipFile(output_filename, 'wb')

            for shortcode in check_range(url, start_num, end_num, item_value, item_type):
                # Write the valid result one per line to the file
                line = '{0}\n'.format(shortcode)
                gzip_file.write(line.encode('ascii'))

            gzip_file.close()

    print('Done')


def check_range(urlpart, start_num, end_num, item_value, item_type):
    while int(end_num) > 0:
        shortcode = end_num
        url = '{0}/{1}'.format(urlpart, str(shortcode))
        counter = 0

        while True:
            # Try 10 times before giving up
            if counter > 10:
                # This will stop the script with an error
                raise Exception('Giving up!')
            try:
                text = fetch(url)
            except FetchError:
                # The server may be overloaded so wait a bit
                print('Sleeping...')
                sys.stdout.flush()
                time.sleep(10)
            else:
                if text:
                    if item_type == 'forum':
                        yield 'forum:{0}'.format(urlpart)
                        print('forum:{0}'.format(urlpart))
                    	sys.stdout.flush()

                    for profile in extract_files(text):
			yield 'profile:{0}'.format(profile)
                        print('profile:{0}'.format(profile))
                        sys.stdout.flush()
                break  # stop the while loop

            counter += 1
        end_num = int(end_num) - 1

def extract_pages(html):
    # Return number of pages
    match = re.search(r'class="pages">Page.1.of.([0-9]+)<\/span>', html)
    if match:
        print("return {0}".format(str(match.group(1))))
        sys.stdout.flush()
        return match.group(1)
    else:
	print("return 1")
        return "1"

def fetch(url):
    '''Fetch the URL and check if it returns OK.

    Returns True, returns the response text. Otherwise, returns None
    '''
#    time.sleep(random.randint(30, 70))
    print('Fetch', url)
    sys.stdout.flush()

    response = requests.get(url, headers=DEFAULT_HEADERS)

    # response doesn't have a reason attribute all the time??
    print('Got', response.status_code, getattr(response, 'reason'))

    sys.stdout.flush()

    if response.status_code == 200:
        # The item exists
        if not response.text:
            # If HTML is empty maybe server broke
            raise FetchError()

        return response.text
    elif response.status_code == 404:
        # Does not exist
        return
    else:
        # Problem
        raise FetchError()


def extract_files(text):
    '''Return a list of profiles from the text.'''
    return re.findall(r'"\/user\/([^"]*)"', text)

if __name__ == '__main__':
    main()
