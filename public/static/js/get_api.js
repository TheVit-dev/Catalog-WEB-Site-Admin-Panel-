/**
 * API Модуль для работы с каталогом товаров (Secret18+)
 */

// Базовый URL для роутера каталога. 
// ⚠️ Если у тебя в main.py префикс роутера отличается (например, '/api/v1/catalog'), поменяй его здесь.
const CATALOG_BASE_URL = '/api/catalog';

/**
 * 1. Получить всю структуру каталога (категории)
 * Соответствует ручке: @web_catalog_router.get("/structure")
 * * @returns {Promise<Object>} Данные структуры каталога (CatalogStructureResponse)
 */
async function fetchCatalogStructure() {
    try {
        const response = await fetch(`${CATALOG_BASE_URL}/structure`);
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status} при получении структуры каталога`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error [fetchCatalogStructure]:', error);
        throw error; // Пробрасываем ошибку дальше, чтобы фронт мог её отобразить
    }
}

/**
 * 2. Получить пагинированный список товаров (с возможностью фильтрации по категории)
 * Соответствует ручке: @web_catalog_router.get("")
 * * @param {number|null} categoryId - ID категории для фильтрации (опционально)
 * @param {number} page - Номер страницы (по умолчанию 1)
 * @param {number} pageSize - Количество товаров на странице (по умолчанию 12)
 * @returns {Promise<Object>} Пагинированный ответ с товарами (PaginatedProductResponse)
 */
async function fetchProducts(categoryId = null, page = 1, pageSize = 12) {
    try {
        // Удобно собираем Query-параметры через нативный URLSearchParams
        const queryParams = new URLSearchParams({
            page: page,
            page_size: pageSize
        });

        // Если category_id передан, добавляем его в строку запроса
        if (categoryId !== null && categoryId !== undefined) {
            queryParams.append('category_id', categoryId);
        }

        const response = await fetch(`${CATALOG_BASE_URL}?${queryParams.toString()}`);
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status} при получении товаров`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error [fetchProducts]:', error);
        throw error;
    }
}