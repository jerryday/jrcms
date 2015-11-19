#encoding: utf-8
from __future__ import unicode_literals

SITE = dict(
    num_per_page=10,
    title='小呆的主页',
    url='http://blog.chenjr.cc'
)

if SITE['url'] and SITE['url'][-1] == '/':
	SITE['url'] = SITE['url'][:-1]
