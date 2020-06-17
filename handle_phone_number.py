mts = [str(i) for i in range(910, 920)] + [str(i) for i in range(980, 990)]
megafon = [str(i) for i in range(920, 940)]
beline = [str(i) for i in range(902, 907)] + [str(i) for i in range(960, 970)]
tele2 = [str('952')]
codes = ['8', '7', '359', '55', '1']


def check_phone_number(number):
    number = number.strip()

    if not number.startswith('+') and number[0] not in '78':
        raise ValueError('неверный формат')

    if number.startswith('-') or number.endswith('-'):
        raise ValueError('неверный формат')

    if any(i.isalpha() for i in number):
        raise ValueError('неверный формат')

    if '(' in number or ')' in number:
        if not (number.count('(') == 1 and number.count(')') == 1):
            raise ValueError('неверный формат')
        if number.index('(') > number.index(')'):
            raise ValueError('неверный формат')

    if any(number[i] == number[i + 1] == '-' for i in range(len(number) - 1)):
        raise ValueError('неверный формат')

    res = ''.join(filter(str.isdigit, number))

    if len(res) != 11:
        raise ValueError('неверное количество цифр')

    if number[0] in '+' and not any(number.startswith(f"+{i}") for i in codes):
        raise ValueError('не определяется код страны')

    if res[0] in '78':
        code = res[1:4]
        if not (code in megafon or code in mts or code in beline or code in tele2):
            raise ValueError('не определяется оператор сотовой связи')

    if res.startswith('8'):
        return '+7' + res[1:]

    return '+' + res
