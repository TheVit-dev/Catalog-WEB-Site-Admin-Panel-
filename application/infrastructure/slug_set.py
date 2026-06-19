def generate_slug(text: str) -> str:
    """Простейший транслит для перевода русских названий в читаемые ссылки (slug)"""
    cyrillic = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя '
    latin = ['a','b','v','g','d','e','yo','zh','z','i','y','k','l','m','n','o','p','r','s','t','u','f','kh','ts','ch','sh','shch','','y','','e','yu','ya','-']
    tr = {c: l for c, l in zip(cyrillic, latin)}
    
    text = text.lower().strip()
    # Заменяем кириллицу, оставляем только буквы, цифры и дефисы
    slug = "".join(tr.get(c, c) for c in text if c.isalnum() or c == ' ' or c == '-')
    # Убираем двойные дефисы, если они появились
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug