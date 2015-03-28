__author__ = 'nitori'

import sys

from okuu import Okuu

okuu = Okuu('okuu.cfg')

url_info = okuu.get_url_info(sys.argv[1])
if url_info is None:
    sys.exit(1)

print('Okuus output:')
print(url_info)
