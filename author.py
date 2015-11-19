#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import sqlite3
import argparse
import getpass
import hashlib
import time
import random
import string

if sys.version_info.major == 2:
    input = raw_input

PACKAGE_DIR = os.path.dirname(__file__) + '/jrcms/'
DB_PATH = PACKAGE_DIR + 'jrcms.sqlite3'

# from http://stackoverflow.com/a/23728630
def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def get_next_author_id(dc):
    author_id = dc.execute('SELECT MAX(id) FROM author').fetchone()[0]
    if author_id is None:
        author_id = 0
    return author_id + 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list', action='store_true', help="list all author's information")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--add', action='store_true', help='add a new author')
    group.add_argument('-r', '--remove', action='store_true', help='remove an existing author')
    group.add_argument('-c', '--chname', action='store_true', help="change author's name")
    group.add_argument('-p', '--passwd', action='store_true', help="change author's password")
    parser.add_argument('-u', '--user', help="specify the author's name")

    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    dc = conn.cursor()
    if args.list:
        rows = dc.execute('SELECT id, name, ctime FROM author')
        for r in rows:
            print('%3d%10s%30s' % (r[0], r[1], r[2]))
    else:
        if not args.user:
            print("author's name expected, check option -u", file=sys.stderr)
            return
        if args.add:
            passwd = getpass.getpass('new password: ')
            passwd2 = getpass.getpass('retype password: ')
            if passwd != passwd2:
                print('password do not match', file=sys.stderr)
                return
            salt = random_string(20)
            passwd = hashlib.sha1((passwd + salt).encode()).hexdigest()
            author_id = get_next_author_id(dc)
            dc.execute('INSERT INTO author(id, name, password, salt) VALUES (?, ?, ?, ?)',
                    (author_id, args.user, passwd, salt))
        else:
            passwd = getpass.getpass('current password: ')
            row = dc.execute('SELECT password, salt FROM author WHERE name = ?', (args.user,)).fetchone()
            if row is None:
                print('author %s does not exist' % args.user, file=sys.stderr)
                return
            hashed_passwd, salt = row[0], row[1]
            if hashed_passwd != hashlib.sha1((passwd + salt).encode()).hexdigest():
                print('authencation failed', file=sys.stderr)
                return

            if args.remove:
                dc.execute('DELETE FROM author WHERE name = ?', (args.user,))
            elif args.chname:
                new_name = input('new name: ')
                if new_name is None or new_name == '':
                    print('error: empty new name', file=sys.stderr)
                    return
                dc.execute('UPDATE author SET name = ? WHERE name = ?', (new_name, args.user))
            elif args.passwd:
                passwd = getpass.getpass('new password: ')
                passwd2 = getpass.getpass('retype password: ')
                if passwd != passwd2:
                    print('password do not match', file=sys.stderr)
                    return
                salt = dc.execute('SELECT salt FROM author WHERE name = ?', (args.user,)).fetchone()[0]
                passwd = hashlib.sha1((passwd + salt).encode()).hexdigest()
                dc.execute('UPDATE author SET password = ? WHERE name = ?', (passwd, args.user))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
