def normalize(items):
    result = []
    for item in items:
        if item == '' or item is None:
            result.append('null')
        elif isinstance(item, str):
            result.append(f"'{item}'")
        elif isinstance(item, bool):
            result.append('true' if item else 'false')
        else:
            result.append(f'{item}')
    return result

def get_to_set(data, primary_key=[]):
    result = []
    values = normalize(data.values())
    for i, key in enumerate(data.keys()):
        if key not in primary_key:
            result.append(f'"{key}" = {values[i]}')
    return ', '.join(result)
