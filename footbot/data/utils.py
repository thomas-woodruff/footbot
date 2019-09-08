import unidecode as u


def get_safe_web_name(web_name):
    '''remove accents and casing from web name'''
    return u.unidecode(web_name).lower()