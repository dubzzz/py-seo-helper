#!/usr/bin/python

import sys
sys.path.insert(0, '../src/')

from webpageparser import WebPageParser, WebPageNode

htmlpage = """<html>
<head>
    <title>A stupid title</title>
    <META NAME="test" CONTENT="test" />
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
        <span data-whoiam="I am a span"></span>
    </div>
    <div class="footer">
        <a href="#">link</a>
    </div>
</body>
</html>"""

# css selector, attribute (none=data), expected value, expected number of elements
check_list = [
# Only tags
    ("div", None, None, 6),
    ("html head title", None, "A stupid title", 1),
# Custom attributes
    ("[name]", None, None, 3),
    ("head [name]", None, None, 3),
    ("meta[name]", None, None, 3),
    ("meta[name=description]", "content", "Test WebPageParser", 1),
    ("meta[name=test]", "content", "test", 1),
    ("div[id^=elt]", "class", "elt", 3),
    ("div[id|=elt]", None, None, 3),
    ("div[id|=elt-]", None, None, 0),
    ("div[class$=er]", None, None, 3),
    ("div[id$='-1']", None, "This is 1", 1),
    ("html body div[class*=ain] div[id$=-1]", None, "This is 1", 1),
    ("a[href=#]", None, "link", 1),
    ("a[href=\"#\"]", None, "link", 1),
    ("a[href='#']", None, "link", 1),
# Class/ID
    ("#elt-1", None, None, 1),
    ("div#elt-2", None, None, 1),
    ("div #elt-1", None, None, 1),
    (".footer", None, None, 1),
    ("div.header", None, None, 1),
    ("html * .container *", None, None, 4),
# Wildcard
    (".header *", None, None, 2),
    ("div.header *", None, None, 2),
    ("* * * *", None, None, 7),
# element , element
    ("h1 , div", None, None, 7),
    ("#elt-1 , html body [class^=cont] .elt[id$=2]", "class", "elt", 2),
    ("head [name=keywords] , meta[content='keyword test page']", None, None, 1),
# element + element
    ("img + h1", None, "Test Page", 1),
    ("div + div", None, None, 4),
    ("div.elt + .elt + div", "id", "elt-3", 1),
    ("#elt-1 + #elt-3", None, None, 0),
# element ~ element
    ("img ~ h1", None, "Test Page", 1),
    ("div ~ div", None, None, 4),
    ("div.elt ~ .elt ~ div", "id", "elt-3", 1),
    ("#elt-1 ~ #elt-3", None, None, 1),
# element > element
    ("img > h1", None, None, 0),
    (".container > div", "class", "elt", 3),
    ("html > head > .container > span", None, None, 0),
    ("html > body > * > div", "class", "elt", 3),
    ("html > * > * > span", "data-whoiam", "I am a span", 1),
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

