import urllib2
import urllib
import json

test_data = {"appId":1,"userId":"bc9f5e06ac9749b19568f566bfe3e485","type":1}
# test_data_urlencode = json.dumps(test_data)
test_data_urlencode = urllib.urlencode(test_data)
requrl = "http://192.168.1.3/php_huskar/public/shake"
# requrl = "http://127.0.0.1:9000/web/shake"
for i in range(500):
    req = urllib2.Request(url=requrl, data=test_data_urlencode)

    res_data = urllib2.urlopen(req)
    res = res_data.read()
    print res
