// ГЛОБАЛЬНОЕ СОСТОЯНИЕ КАТАЛОГА
let allCategories = []; 
let currentCategoryId = null;
let currentPage = 1;
const itemsPerPage = 12; // Сколько товаров отдавать на одну страницу

document.addEventListener('DOMContentLoaded', async () => {
    const catContainer = document.getElementById('categories-container');
    const prodContainer = document.getElementById('products-container');

    if (!catContainer || !prodContainer) return;

    try {
        const responseData = await fetchCatalogStructure();
        allCategories = responseData.categories || [];
        renderCategories(null);
        prodContainer.innerHTML = '';
    } catch (error) {
        console.error('Ошибка при инициализации каталога:', error);
    }
});

const safePlaceholder = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 3 4' fill='%2313131a'><rect width='100%' height='100%'/><text x='50%' y='50%' fill='%23333' font-size='0.3' text-anchor='middle' dominant-baseline='middle' font-family='sans-serif'>НЕТ ФОТО</text></svg>";

function renderCategories(parentId = null) {
    const catContainer = document.getElementById('categories-container');
    const prodContainer = document.getElementById('products-container');
    const detailContainer = document.getElementById('product-detail-container');
    const paginationContainer = document.getElementById('pagination-container') || document.querySelector('.custom-pagination');
    
    if (catContainer) catContainer.style.removeProperty('display');
    if (prodContainer) prodContainer.style.removeProperty('display');
    if (detailContainer) detailContainer.style.setProperty('display', 'none', 'important');

    const currentLevelCategories = allCategories.filter(cat => cat.parent_id === parentId);
    catContainer.innerHTML = '';

    if (parentId === null) {
        prodContainer.innerHTML = ''; 
        if (paginationContainer) paginationContainer.innerHTML = ''; // Скрываем страницы на главной каталога
    }

    if (parentId !== null) {
        const backCard = document.createElement('div');
        backCard.className = 'custom-cat-card custom-back-card';
        backCard.innerHTML = `<h2 class="custom-cat-title">⬅ НАЗАД</h2>`;
        backCard.addEventListener('click', () => {
            const currentParent = allCategories.find(cat => cat.id === parentId);
            renderCategories(currentParent ? currentParent.parent_id : null);
        });
        catContainer.appendChild(backCard);
    }

    currentLevelCategories.forEach(category => {
    const hasChildren = allCategories.some(cat => cat.parent_id === category.id);
    const card = document.createElement('div');
    card.className = 'custom-cat-card';
    
    // Получаем картинку, чистим путь
    let catImg = category.image_url || category.image || safePlaceholder;
    if (catImg && !catImg.startsWith('http') && !catImg.startsWith('data:')) {
        if (!catImg.startsWith('/')) catImg = '/' + catImg;
    }

    // ВАЖНО: Используем setProperty с !important
    card.style.setProperty('background-image', `linear-gradient(180deg, rgba(0,0,0,0) 10%, rgba(0,0,0,0.85) 100%), url('${catImg}')`, 'important');
    card.style.backgroundSize = 'cover';
    card.style.backgroundPosition = 'center';

    card.innerHTML = `
        <div class="custom-cat-content">
            <h2 class="custom-cat-title">${(category.name || category.title || 'Категория').toUpperCase()}</h2>
            <button class="custom-cat-btn">${hasChildren ? 'Открыть' : 'Смотреть'}</button>
        </div>
    `;

    card.addEventListener('click', async () => {
        if (hasChildren) {
            renderCategories(category.id);
        } else {
            await renderCatalogProducts(category.id, 1);
        }
    });

    catContainer.appendChild(card);
});
}

// МОДЕРНИЗИРОВАННАЯ ФУНКЦИЯ ЗАГРУЗКИ ТОВАРОВ С ПАГИНАЦИЕЙ
async function renderCatalogProducts(categoryId = null, page = 1) {
    currentCategoryId = categoryId;
    currentPage = page;

    const container = document.getElementById('products-container');
    container.innerHTML = '<div class="catalog-loading">Загрузка товаров...</div>';

    // Ищем контейнер пагинации на странице, либо создадим его динамически ниже сетки товаров
    let paginationContainer = document.getElementById('pagination-container');
    if (!paginationContainer) {
        paginationContainer = document.querySelector('.custom-pagination');
        if (!paginationContainer) {
            paginationContainer = document.createElement('div');
            paginationContainer.className = 'custom-pagination';
            paginationContainer.id = 'pagination-container';
            container.parentNode.insertBefore(paginationContainer, container.nextSibling);
        }
    }
    paginationContainer.innerHTML = ''; 

    try {
        // Отправляем динамические параметры страницы на бэкенд
        const responseData = await fetchProducts(categoryId, page, itemsPerPage);
        const products = responseData.items || responseData.products || (Array.isArray(responseData) ? responseData : []);
        container.innerHTML = '';

        if (products.length === 0) {
            container.innerHTML = '<div class="catalog-empty">В этой категории товаров пока нет</div>';
            return;
        }

        // Отрендерим товары
        products.forEach(product => {
            const productName = product.name || product.title || 'Без названия';
            const productPrice = product.price || 0;

            let productImg = safePlaceholder;
            if (typeof product.main_image === 'string' && product.main_image.trim() !== '') {
                productImg = product.main_image;
            } else if (product.gallery && Array.isArray(product.gallery) && product.gallery.length > 0) {
                productImg = product.gallery[0];
            }

            if (productImg && !productImg.startsWith('http') && !productImg.startsWith('data:')) {
                if (!productImg.startsWith('/')) productImg = '/' + productImg;
            }

            const card = document.createElement('div');
            card.className = 'custom-prod-card';
            card.setAttribute('data-id', product.id);
            
            card.innerHTML = `
                <div class="custom-prod-img-wrap">
                    <img src="${productImg}" alt="${productName}" onerror="this.onerror=null; this.src='${safePlaceholder}';">
                </div>
                <div class="custom-prod-footer">
                    <div class="custom-prod-title">${productName}</div>
                    <div class="custom-prod-price">${productPrice} ТГ</div>
                </div>
            `;

            card.addEventListener('click', () => {
                showProductDetail(product);
            });

            container.appendChild(card);
        });

        // ЛОГИКА ГЕНЕРАЦИИ КНОПОК СТРАНИЦ
        // Забираем total_pages или общее количество записей из ответа FastAPI (в зависимости от твоего пагинатора)
        let totalPages = 1;
    if (responseData.meta && responseData.meta.total_pages) {
        totalPages = responseData.meta.total_pages;
    }

    console.log("--- ДЕБАГ ПАГИНАЦИИ ---");
    console.log("1. Всего страниц получено:", totalPages);
    console.log("2. Контейнер пагинации найден:", !!paginationContainer);

    if (totalPages > 1) {
        console.log("3. Условие (totalPages > 1) пройдено!");
        
        // Проверяем, существует ли вообще функция отрисовки кнопок
        if (typeof renderPaginationControls === 'function') {
            console.log("4. Запускаем renderPaginationControls...");
            renderPaginationControls(paginationContainer, totalPages, page);
        } else {
            console.error("🚨 ОШИБКА: Функция renderPaginationControls не существует! Ты точно скопировал её в свой JS-файл?");
        }
    } else {
        console.log("3. Кнопки не рисуем, так как страниц <= 1");
    }

} catch (error) {
    console.error('Ошибка при загрузке товаров:', error);
}
}

// ФУНКЦИЯ РИСОВАНИЯ СТРАНИЦ КАТАЛОГА
function renderPaginationControls(container, totalPages, activePage) {
    container.innerHTML = '';

    // Кнопка "Назад"
    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn';
    prevBtn.innerHTML = '&#10094;';
    prevBtn.disabled = activePage === 1;
    prevBtn.addEventListener('click', () => {
        if (activePage > 1) renderCatalogProducts(currentCategoryId, activePage - 1);
    });
    container.appendChild(prevBtn);

    // Цикл по страницам
    for (let i = 1; i <= totalPages; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-btn ${i === activePage ? 'active-page' : ''}`;
        pageBtn.innerText = i;
        
        pageBtn.addEventListener('click', () => {
            if (i !== activePage) renderCatalogProducts(currentCategoryId, i);
        });
        container.appendChild(pageBtn);
    }

    // Кнопка "Вперед"
    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn';
    nextBtn.innerHTML = '&#10095;';
    nextBtn.disabled = activePage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (activePage < totalPages) renderCatalogProducts(currentCategoryId, activePage + 1);
    });
    container.appendChild(nextBtn);
}

// ФУНКЦИЯ ОТКРЫТИЯ СТРАНИЦЫ ТОВАРА (СО СТРЕЛОЧКАМИ И СВАЙПАМИ)
function showProductDetail(product) {
    const catContainer = document.getElementById('categories-container');
    const prodContainer = document.getElementById('products-container');
    const detailContainer = document.getElementById('product-detail-container');
    const paginationContainer = document.getElementById('pagination-container') || document.querySelector('.custom-pagination');

    


    

    if (catContainer) catContainer.style.setProperty('display', 'none', 'important');
    if (prodContainer) prodContainer.style.setProperty('display', 'none', 'important');
    if (paginationContainer) paginationContainer.style.setProperty('display', 'none', 'important');
    if (detailContainer) detailContainer.style.setProperty('display', 'block', 'important');

    let allImages = [];
    if (product.main_image) allImages.push(product.main_image);
    if (product.gallery && Array.isArray(product.gallery)) {
        product.gallery.forEach(img => {
            if (img && !allImages.includes(img)) allImages.push(img);
        });
    }
    if (allImages.length === 0) allImages.push(safePlaceholder);

    let currentImgIdx = 0;

    detailContainer.innerHTML = `
        <button class="detail-back-btn" id="back-to-catalog-btn">⬅ НАЗАД В КАТАЛОГ</button>
        
        <div class="product-detail-layout">
            <div class="product-detail-gallery">
                <div class="main-image-window" id="gallery-swipe-zone">
                    <button class="gallery-arrow prev-arrow" id="gallery-prev-btn">&#10094;</button>
                    <img id="active-detail-img" src="${allImages[0]}" alt="${product.title || 'Товар'}">
                    <button class="gallery-arrow next-arrow" id="gallery-next-btn">&#10095;</button>
                </div>
                <div class="thumbnails-track">
                    ${allImages.map((img, idx) => `
                        <div class="thumb-wrapper ${idx === 0 ? 'thumb-active' : ''}" data-idx="${idx}">
                            <img src="${img}" onerror="this.onerror=null; this.src='${safePlaceholder}';">
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="product-detail-info">
                <h1 class="detail-product-title">${product.title || product.name || 'Без названия'}</h1>
                <div class="detail-product-price">${product.price || 0} ТГ</div>
                
                <div class="detail-divider"></div>
                
                <div class="detail-desc-block">
                    <h3>Описание</h3>
                    <p>${product.description || 'Описание товара пока отсутствует.'}</p>
                </div>
                
                <button class="detail-buy-btn">ЗАКАЗАТЬ</button>
                
            </div>
        </div>
    `;

    
    const mainImgWindow = document.getElementById('active-detail-img');
    const thumbWrappers = detailContainer.querySelectorAll('.thumb-wrapper');
    const prevBtn = document.getElementById('gallery-prev-btn');
    const nextBtn = document.getElementById('gallery-next-btn');
    const swipeZone = document.getElementById('gallery-swipe-zone');

    function updateGalleryState(newIdx) {
        currentImgIdx = newIdx;
        mainImgWindow.src = allImages[currentImgIdx];
        
        thumbWrappers.forEach((thumb, idx) => {
            if (idx === currentImgIdx) {
                thumb.classList.add('thumb-active');
                thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            } else {
                thumb.classList.remove('thumb-active');
            }
        });
    }

    if (allImages.length <= 1) {
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
    } else {
        prevBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            let idx = currentImgIdx - 1;
            if (idx < 0) idx = allImages.length - 1;
            updateGalleryState(idx);
        });

        nextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            let idx = currentImgIdx + 1;
            if (idx >= allImages.length) idx = 0;
            updateGalleryState(idx);
        });
    }

    thumbWrappers.forEach(thumb => {
        thumb.addEventListener('click', function() {
            const targetIdx = parseInt(this.getAttribute('data-idx'), 10);
            updateGalleryState(targetIdx);
        });
    });

    // СВАЙПЫ
    let touchStartX = 0;
    let touchEndX = 0;

    swipeZone.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    swipeZone.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        if (allImages.length <= 1) return;
        const deltaX = touchStartX - touchEndX;
        if (deltaX > 40) {
            let idx = currentImgIdx + 1;
            if (idx >= allImages.length) idx = 0;
            updateGalleryState(idx);
        } else if (deltaX < -40) {
            let idx = currentImgIdx - 1;
            if (idx < 0) idx = allImages.length - 1;
            updateGalleryState(idx);
        }
    }, { passive: true });

    // Кнопка Назад
    document.getElementById('back-to-catalog-btn').addEventListener('click', () => {
        if (detailContainer) detailContainer.style.setProperty('display', 'none', 'important');
        if (catContainer) catContainer.style.removeProperty('display');
        if (prodContainer) prodContainer.style.removeProperty('display');
        if (paginationContainer) paginationContainer.style.removeProperty('display');
    });

    // === ЖЕЛЕЗОБЕТОННАЯ ЛОГИКА ЗАКАЗА ===
    const buyBtn = detailContainer.querySelector('.detail-buy-btn');
    
    if (buyBtn) {
        // Убираем старые обработчики (если они были)
        const newBuyBtn = buyBtn.cloneNode(true);
        buyBtn.parentNode.replaceChild(newBuyBtn, buyBtn);

        newBuyBtn.addEventListener('click', () => {
            const modal = document.getElementById('order-modal');
            const waBtn = document.getElementById('modal-wa-btn');
            
            if (modal) {
                // Подставляем текст сообщения
                const productName = product.title || product.name || 'Товар';
                const waText = encodeURIComponent(`Здравствуйте! Хочу заказать: "${productName}"`);
                
                if (waBtn) {
                    waBtn.href = `https://wa.me/77777777777?text=${waText}`; // Твой номер
                }

                // ПРИНУДИТЕЛЬНОЕ отображение
                modal.style.setProperty('display', 'flex', 'important');
                console.log("Модальное окно принудительно открыто");
            } else {
                console.error("Критическая ошибка: модальное окно #order-modal не найдено в DOM!");
            }
        });
    } else {
        console.error("Ошибка: кнопка .detail-buy-btn не найдена в контейнере!");
    }

    // Глобальный слушатель для закрытия модалки
    document.addEventListener('click', (e) => {
    const modal = document.getElementById('order-modal');
    
    // Если нажали на кнопку "Закрыть" ИЛИ на фон (сам overlay)
    if (e.target.id === 'close-modal-btn' || e.target.id === 'order-modal') {
        modal.classList.remove('is-visible');
    }
    });


    

}







// ФУНКЦИЯ ОТРИСОВКИ КНОПОК ПАГИНАЦИИ В КАТАЛОГЕ
function renderPaginationControls(container, totalPages, currentPage) {
    // Очищаем контейнер перед новой отрисовкой
    container.innerHTML = '';

    // Кнопка НАЗАД (Стрелочка влево)
    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn nav-btn';
    prevBtn.innerHTML = '&#10094;'; // Юникод стрелочки <
    prevBtn.disabled = currentPage === 1; // Отключаем на первой странице
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            renderCatalogProducts(currentCategoryId, currentPage - 1);
        }
    });
    container.appendChild(prevBtn);

    // Кнопки с номерами страниц
    for (let i = 1; i <= totalPages; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.addEventListener('click', () => {
            if (i !== currentPage) {
                renderCatalogProducts(currentCategoryId, i);
            }
        });
        container.appendChild(pageBtn);
    }

    // Кнопка ВПЕРЕД (Стрелочка вправо)
    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn nav-btn';
    nextBtn.innerHTML = '&#10095;'; // Юникод стрелочки >
    nextBtn.disabled = currentPage === totalPages; // Отключаем на последней странице
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            renderCatalogProducts(currentCategoryId, currentPage + 1);
        }
    });
    container.appendChild(nextBtn);
}