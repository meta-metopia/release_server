import re


def check_format(string: str) -> bool:  # define a function that takes a string as input
    # check if string contains only numbers, dots and words
    if not re.match(r"^[a-zA-Z0-9.]*$", string):
        return False  # return False if it doesn't

    substrings = string.split(".")  # split the string by dot and store the result in a list
    if len(substrings) > 1:  # check if the list has more than one element
        for substring in substrings:  # loop through each element in the list
            if substring == "":  # check if the element is empty
                return False  # return False
        return True  # return True after checking all elements
    else:  # otherwise
        return False  # return False
