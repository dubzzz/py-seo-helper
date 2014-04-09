#!/usr/bin/python

import sys
sys.path.insert(0, '../src/')

from webpageparser import WebPageParser, WebPageNode

htmlpage = """<html>
<head>
    <title>A stupid title</title>
    <meta name="description" content="Test WebPageParser" />
    <meta name="keywords" content="keyword test page" />
</head>
<body>
    <div class="header">
        <img src="/logo.png" alt="logo" />
        <h1>Test Page</h1>
    </div>
    <div class="container">
        <div id="elt-1" class="elt">This is 1</div>
        <div id="elt-2" class="elt">This is 2</div>
        <div id="elt-3" class="elt">This is 3</div>
    </div>
    <div class="footer"></div>
</body>
</html>"""

# css selector, attribute (none=data), expected value, expected number of elements
check_list = [
# Only tags
    ("div", None, None, 6),
    ("html head title", None, "A stupid title", 1),
# Custom attributes
    ("[name]", None, None, 2),
    ("head [name]", None, None, 2),
    ("meta[name]", None, None, 2),
    ("meta[name=description]", "content", "Test WebPageParser", 1),
    ("div[id^=elt]", "class", "elt", 3),
    ("div[id|=elt]", None, None, 3),
    ("div[id|=elt-]", None, None, 0),
    ("div[class$=er]", None, None, 3),
    ("div[id$='-1']", None, "This is 1", 1),
    ("html body div[class*=ain] div[id$=-1]", None, "This is 1", 1),
# Class/ID
    ("#elt-1", None, None, 1),
    ("div#elt-2", None, None, 1),
    ("div #elt-1", None, None, 1),
    (".footer", None, None, 1),
    ("div.header", None, None, 1),
    ("html * .container *", None, None, 3),
# Wildcard
    (".header *", None, None, 2),
    ("div.header *", None, None, 2),
    ("* * * *", None, None, 5),
]

wp = WebPageParser()
wp.feed(htmlpage)

for check in check_list:
    print "Check '%s'" % check[0]
    result_list = wp.find(check[0])

    if check[2]:
        for res in result_list:
            if check[1]:
                try:
                    if res.get_attrs()[check[1]] != check[2]:
                        print "> Unexpected value - '%s' instead of '%s'" % (res.get_attrs()[check[1]], check[2])
                except KeyError:
                    print "> Unable to access the attribute '%s'" % check[1]
            else:
                if res.get_data() != check[2]:
                    print "> Unexpected value - '%s' instead of '%s'" % (res.get_data(), check[2])

    if len(result_list) != check[3]:
        print "> Unexpected number of elements - %d instead of %d" % (len(result_list), check[3])

