import re
from urllib.parse import urlparse

def has_ip(url):
    return 1 if re.search(r'\d+\.\d+\.\d+\.\d+', url) else 0

def count_special_chars(url):
    return sum(url.count(c) for c in ['?', '=', '&', '%'])

def has_suspicious_words(url):
    return 1 if re.search(r'login|secure|bank|verify|update', url.lower()) else 0

def is_shortened(url):
    shorteners = ["bit.ly", "tinyurl", "goo.gl", "t.co"]
    return 1 if any(short in url for short in shorteners) else 0

def count_subdomains(domain):
    return domain.count('.')

def extract_features(url):
    parsed = urlparse(url)
    domain = parsed.netloc

    return [
        len(url),
        url.count('.'),
        url.count('@'),
        1 if 'https' in url else 0,
        1 if '-' in url else 0,
        len(domain),
        url.count('//'),
        sum(c.isdigit() for c in url),
        has_suspicious_words(url),
        has_ip(url),
        count_special_chars(url),
        count_subdomains(domain),
        is_shortened(url)
    ]