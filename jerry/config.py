SITE = dict(
    num_per_page=10,
    title='xiaodai的主页',
    url='http://blog.chenjr.cc'
)

if SITE['url'] and SITE['url'][-1] == '/':
	SITE['url'] = SITE['url'][:-1]
