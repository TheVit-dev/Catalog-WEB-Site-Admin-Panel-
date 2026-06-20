from aiogram.fsm.state import StatesGroup, State

class CategoryFSM(StatesGroup):
    name = State()
    parent = State()
    photo = State()



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