__author__ = 'nitori'

import asyncio
import json
import sys

from okuu import Okuu

okuu = Okuu('okuu.cfg')

loop = asyncio.get_event_loop()

url_info = loop.run_until_complete(okuu.get_url_info(sys.argv[1]))
if url_info is None:
    sys.exit(1)

print('Okuus output:')
print(json.dumps(url_info, indent=4))
