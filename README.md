# SEO Helper

## Search Engine Optimization Tool

SEO Helper is a Search engine optimization tool. It carries out tests on several functionalities that are required for a top-ranked website.

It raises points that can be enhanced in an attempt to improve the ranking of the website on Search Engines.

## Tested functionalities

SEO Helper tests 27 points that can enhanced your ranking. Among those:
+ robots.txt exists?
+ broken links
+ broken ressources
+ duplicated title
+ duplicated description
+ balance between internal and external links
+ at least one h1 tag
+ title and description meta
+ 3-click rule

All these tests are defined in init method of WebSite class. Results can then be exported to PDF and sent by email.

## Make it work

This project requires [wkhtmltopdf](https://github.com/wkhtmltopdf/wkhtmltopdf) to work properly. wkhtmltopdf exports reports to PDF. It needs to be put in ./bin/wkhtmltopdf.

The code to launch the scan is in ./src/scan.py.
eg.: ./src/scan.py --url=http://portfolio.dubien.me/ --nofollow --noindex

Parameters for scan.py:
+ **-h, --help**: Display help.
+ **-u [url], --url=[url]**: URL where the analysis will start. The crawler will then crawl from page to page. The URL must end by /.
+ **-d [max-depth], --max-depth=[max-depth]**: Specify a different value for max-depth. By default: max-depth=5.
+ **--nofollow**: By default, the crawler follows every link in the page. By using this option, the crawler will not follow links tagged with rel='nofollow'.
+ **--noindex**: By default, the output includes every page of your website that can be reached in max-depths clicks. By using --noindex option results with <meta name='robots' content='noindex' /> will not be diplayed
+ **-m [me@domain.com], --email=[me@domain.com]**: Specify the email address of the user that should received the PDF report. Not specified implies no email, but PDF generation in ./output/pdf.pdf.
+ **-a, --deep**: Deep analysis. Instead of asking only for the header of external webpages (default behaviour), it will ask the complete webpage.
This kind of analysis will certainly be a bit longer. It allows to follow redirections and check whether or not the targetted element is accessible.
+ **-n, --retry=[num-retry]**: Specify the number of times to retry queries before failing.
+ **-c, --color**: Colored output. Default: no-colors.

## What's next?

Some functionalities are still missing:
+ Sitemap in robots.txt
+ Broken-links in Sitemap
+ URL that can be read and understood (not ?id=782)
