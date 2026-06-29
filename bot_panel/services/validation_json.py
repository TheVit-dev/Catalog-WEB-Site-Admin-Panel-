from aiogram.fsm.state import StatesGroup, State
import re


def format_category_tree(data: dict) -> str:
    """
    Принимает JSON вида {"categories": [...]} со связями parent_id 
    и строит красивое текстовое дерево для Telegram.
    """
    categories = data.get("categories", [])
    if not categories:
        return "Категорий пока нет."
    
    # 1. Создаем быстрый индекс всех элементов и добавляем им поле для детей
    nodes = {cat["id"]: {**cat, "children": []} for cat in categories}
    roots = []
    
    # 2. Распределяем элементы: если parent_id нет — это корень, если есть — кидаем к родителю
    for cat_id, node in nodes.items():
        p_id = node.get("parent_id")
        if p_id is None:
            roots.append(node)
        else:
            if p_id in nodes:
                nodes[p_id]["children"].append(node)
            else:
                # На случай, если parent_id указан, но самого родителя в базе нет
                roots.append(node)
                
    # 3. Рекурсивная функция для сборки дерева в красивый текст
    def render_node(node, level=0):
        indent = "   " * level
        # Топ-уровень помечаем папкой, подкатегории — красивой веткой
        prefix = "📁 " if level == 0 else f"{indent}└── 🔹 "
        text = f"{prefix}{node['name']}\n"
        
        for child in node["children"]:
            text += render_node(child, level + 1)
        return text

    # Собираем все корневые элементы в одну строчку
    tree_text = ""
    for root in roots:
        tree_text += render_node(root)
        
    return tree_text.strip()


def validate_category_name(text: str) -> tuple[bool, str]:
    """Проверяет адекватность введенного названия категории."""
    if not text or not text.strip():
        return False, "Название не может быть пустым."
    
    clean_text = text.strip()
    if len(clean_text) < 2 or len(clean_text) > 100:
        return False, "Длина названия должна быть от 2 до 100 символов."
        
    return True, clean_text


def parse_parent_input(text: str) -> str:
    """Очищает ввод пользователя для родительской категории."""
    clean_text = text.strip()
    return "0" if clean_text == "0" else clean_text



def parse_product_input(text: str) -> dict:
    """
    Проверяет ввод пользователя: ссылка это или текст (название).
    Возвращает словарь с типом ввода и значением.
    """
    text = text.strip()
    
    # Регулярка проверяет, начинается ли текст с http/https
    if re.match(r"^https?://", text):
        # Ищем всё, что идет после последнего слэша (обычно это slug или id)
        # Например, из https://site.kz/catalog/super-dildo вытащит "super-dildo"
        match = re.search(r"/([^/]+)/?$", text)
        if match:
            return {"type": "link", "value": match.group(1)}
        else:
            return {"type": "error", "value": "Не удалось распознать товар в ссылке"}
    
    # Если это не ссылка, значит админ ввел точное название или ID
    return {"type": "text", "value": text}

