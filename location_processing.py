#location operations
from lingua_franca.format import pronounce_number
import re


def location_format(location):
    """
    Finds all digits in store's location and
    formats them to numeral words.
    Args:
        location (str): location info
        from stores info
    Returns:
        if digits were found:
            pronounced (str): utterance with
            pronounced digits
        else:
            location (str): not changed utterance
    Examples:
        'level 1' -> 'level one'
    """
    floor = re.findall(r'\d+', location)
    if len(floor) > 0:
        floor = floor[0]
        num = pronounce_number(int(floor), ordinals=False)
        pronounced = re.sub(r'\d+', num, location)
        return pronounced
    else:
        return location

def store_selection_by_floors(user_request, found_stores):
    """
    If there are several stores in found stores list
    and user agrees to select store by floor.
    Finds all digits in store's location and
    formats them to ordinal and cardinal numerals.
    Matches formated numerals with user's request.
    If store was found appends it to the new found
    list.
    Args:
        user_request (str): floor from user
        found_stores (list): found stores on user's
        request
    Returns:
        stores_by_floor (list): stores that was found by floor
    """
    stores_by_floor = []
    for store in found_stores:
        numbers = re.findall(r'\d+', store['location'])
        if len(numbers) > 0:
            numbers = numbers[0]
            num = pronounce_number(int(numbers), ordinals=False)
            num_ordinal = pronounce_number(int(numbers), ordinals=True)
            if num in user_request or num_ordinal in user_request:
                stores_by_floor.append(store)
    return stores_by_floor