__author__ = 'nitori'

from datetime import timedelta


def get_number_and_suffix(string):
    string = ''.join(string.split())
    digits = ''
    while True:
        char, string = string[0:1], string[1:]
        if not char or not char.isdigit():
            string = char + string
            break
        digits += char
    digits = int(digits)
    return digits, string


def calculate_size(size_string):
    number, suffix = get_number_and_suffix(size_string)
    suffix_upper = suffix.upper()
    suffixes = ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    if suffix_upper not in suffixes:
        raise ValueError('No such suffix: {}'.format(suffix))
    return number << (suffixes.index(suffix_upper)*10)


def calculate_time(time_string):
    number, suffix = get_number_and_suffix(time_string)
    suffix_upper = suffix.upper()
    # seconds, minutes, hours, days, weeks, years
    if suffix_upper not in ('', 'S', 'M', 'H', 'D', 'W', 'Y'):
        raise ValueError('No such suffix: {}'.format(suffix))
    seconds = number * {
        '': 1,
        'S': 1,
        'M': 60,
        'H': 3600,
        'D': 86400,
        'W': 604800,
        'Y': 31536000,
    }[suffix_upper]
    return timedelta(seconds=seconds)