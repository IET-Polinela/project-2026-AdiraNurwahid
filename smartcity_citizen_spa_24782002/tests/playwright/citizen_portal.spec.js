const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';
const SPA_URL  = 'http://127.0.0.1:5500/smartcity_citizen_spa_24782002/index.html';

const TEST_CITIZEN_USERNAME = 'testwarga';
const TEST_CITIZEN_PASSWORD = 'testpassword123';
const TEST_ADMIN_USERNAME   = 'admin';
const TEST_ADMIN_PASSWORD   = 'admin123';

const EXPIRED_ACCESS_TOKEN  = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjAwMDAwMDAwLCJpYXQiOjE2MDAwMDAwMDAsImp0aSI6ImZha2VfYWNjZXNzX2lkIiwidXNlcl9pZCI6MX0.fake_signature_for_testing';
const EXPIRED_REFRESH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTYwMDAwMDAwMCwiaWF0IjoxNjAwMDAwMDAwLCJqdGkiOiJmYWtlX3JlZnJlc2hfaWQiLCJ1c2VyX2lkIjoxfQ.fake_signature_for_testing';

// Login ke SPA via form (real login ke Django)
async function loginSPA(page, username, password) {
    await page.goto(`${SPA_URL}#login`);
    await page.waitForSelector('#loginForm', { state: 'visible', timeout: 10000 });

    page.on('dialog', async (d) => await d.accept());

    await page.locator('#loginUsername').fill(username);
    await page.locator('#loginPassword').fill(password);
    await page.locator('#loginForm button[type="submit"]').click();

    // Tunggu redirect ke #dashboard setelah login berhasil
    await page.waitForFunction(
        () => window.location.hash === '#dashboard',
        null,
        { timeout: 15000 }
    );
    // Tunggu tombol Buat Laporan muncul (dashboard sudah ter-render)
    await page.waitForSelector('#openReportModalBtn', { state: 'visible', timeout: 15000 });
}

// Login ke portal admin Django
async function loginAdmin(page, username, password) {
    await page.goto(`${BASE_URL}/auth/login/`);
    await page.waitForSelector('form', { state: 'visible', timeout: 10000 });
    await page.locator('input[name="username"]').fill(username);
    await page.locator('input[name="password"]').fill(password);
    await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle', timeout: 15000 }),
        page.locator('button[type="submit"]').click()
    ]);
}

async function clearAuthTokens(page) {
    await page.evaluate(() => localStorage.clear());
}

// =============================================================================
// MODUL 1: OTORISASI & SESI (AUTH-04, AUTH-05, AUTH-06)
// =============================================================================
test.describe('Modul 1: Otorisasi & Sesi (AUTH-04, AUTH-05, AUTH-06)', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(SPA_URL);
        await clearAuthTokens(page);
    });

    test('AUTH-04: Akses #dashboard tanpa token → redirect ke #login', async ({ page }) => {
        // Pastikan tidak ada token
        const tokenBefore = await page.evaluate(() => localStorage.getItem('access_token'));
        expect(tokenBefore).toBeNull();

        // Navigasi langsung ke #dashboard tanpa token
        await page.goto(`${SPA_URL}#dashboard`);

        // app.js route(): if (!isLoggedIn()) → window.location.hash = "#login"
        await page.waitForFunction(
            () => window.location.hash === '#login',
            null,
            { timeout: 8000 }
        );

        await expect(page).toHaveURL(/#login/);
        await expect(page.locator('#loginForm')).toBeVisible({ timeout: 5000 });

        console.log('[AUTH-04] ✅ Redirect #dashboard → #login berhasil');
    });

    test('AUTH-05: Token kadaluarsa → interceptor menangani 401 dan redirect ke #login', async ({ page }) => {
        // Set token expired di localStorage
        await page.evaluate(({ access, refresh }) => {
            localStorage.setItem('access_token', access);
            localStorage.setItem('refresh_token', refresh);
        }, { access: EXPIRED_ACCESS_TOKEN, refresh: EXPIRED_REFRESH_TOKEN });

        // Mock semua API return 401
        await page.route('**/api/**', async (route) => {
            await route.fulfill({
                status: 401,
                contentType: 'application/json',
                body: JSON.stringify({ detail: 'Token not valid', code: 'token_not_valid' })
            });
        });

        page.on('dialog', async (d) => {
            console.log(`[AUTH-05] Dialog: "${d.message()}"`);
            await d.accept();
        });

        // Buka dashboard — app.js akan coba refresh token, gagal, lalu logout()
        await page.goto(`${SPA_URL}#dashboard`);
        await page.waitForTimeout(3000);

        await page.waitForFunction(
            () => window.location.hash === '#login',
            null,
            { timeout: 12000 }
        );

        await expect(page).toHaveURL(/#login/);

        // app.js logout() memanggil clearTokens()
        const tokenAfter   = await page.evaluate(() => localStorage.getItem('access_token'));
        const refreshAfter = await page.evaluate(() => localStorage.getItem('refresh_token'));
        expect(tokenAfter).toBeNull();
        expect(refreshAfter).toBeNull();

        console.log('[AUTH-05] ✅ Token expired: localStorage bersih, redirect ke #login');
    });

    test('AUTH-06: Kedua token kadaluarsa → localStorage dibersihkan, redirect ke #login', async ({ page }) => {
        // Set kedua token expired
        await page.evaluate(({ access, refresh }) => {
            localStorage.setItem('access_token', access);
            localStorage.setItem('refresh_token', refresh);
        }, { access: EXPIRED_ACCESS_TOKEN, refresh: EXPIRED_REFRESH_TOKEN });

        const accessBefore  = await page.evaluate(() => localStorage.getItem('access_token'));
        const refreshBefore = await page.evaluate(() => localStorage.getItem('refresh_token'));
        expect(accessBefore).not.toBeNull();
        expect(refreshBefore).not.toBeNull();

        // Mock semua API return 401
        await page.route('**/api/**', async (route) => {
            await route.fulfill({
                status: 401,
                contentType: 'application/json',
                body: JSON.stringify({ detail: 'Token expired', code: 'token_not_valid' })
            });
        });

        page.on('dialog', async (d) => {
            console.log(`[AUTH-06] Dialog: "${d.message()}"`);
            await d.accept();
        });

        await page.goto(`${SPA_URL}#dashboard`);
        await page.waitForTimeout(3000);

        await page.waitForFunction(
            () => window.location.hash === '#login',
            null,
            { timeout: 12000 }
        );

        await expect(page).toHaveURL(/#login/);

        // Verifikasi localStorage bersih
        expect(await page.evaluate(() => localStorage.getItem('access_token'))).toBeNull();
        expect(await page.evaluate(() => localStorage.getItem('refresh_token'))).toBeNull();

        await expect(page.locator('#loginForm')).toBeVisible({ timeout: 5000 });

        console.log('[AUTH-06] ✅ Kedua token expired: localStorage bersih, redirect ke #login');
    });
});

// =============================================================================
// MODUL 5: INTERAKTIVITAS UI (UI-01 through UI-06)
// =============================================================================
test.describe('Modul 5: Interaktivitas UI (UI-01 through UI-06)', () => {

    test('UI-01: Chart.js di Dashboard Admin ter-render dengan benar', async ({ page }) => {
        await loginAdmin(page, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD);
        await page.goto(`${BASE_URL}/auth/dashboard/`);
        await page.waitForLoadState('networkidle');

        const statusChartCanvas   = page.locator('#statusChart');
        const categoryChartCanvas = page.locator('#categoryChart');

        await expect(statusChartCanvas).toBeVisible({ timeout: 15000 });
        await expect(categoryChartCanvas).toBeVisible({ timeout: 15000 });

        const chartsRendered = await page.evaluate(() => {
            if (typeof Chart === 'undefined') return false;
            return Object.keys(Chart.instances || {}).length >= 2;
        });
        expect(chartsRendered).toBe(true);

        console.log('[UI-01] ✅ Chart.js statusChart dan categoryChart ter-render');
    });

    test('UI-02: Live Search pada daftar laporan admin berfungsi', async ({ page }) => {
        await loginAdmin(page, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD);
        await page.goto(`${BASE_URL}/laporan/`);
        await page.waitForLoadState('networkidle');

        const searchInput = page.locator('#searchInput');
        const tableBody   = page.locator('#reportTableBody');

        await expect(searchInput).toBeVisible({ timeout: 10000 });
        await expect(tableBody).toBeVisible({ timeout: 10000 });

        const initialRowCount = await tableBody.locator('tr').count();
        console.log(`[UI-02] Jumlah baris awal: ${initialRowCount}`);

        const searchKeyword = 'Laporan';
        const responsePromise = page.waitForResponse(
            (response) => response.url().includes('/laporan/search/') && response.status() === 200,
            { timeout: 15000 }
        );

        await searchInput.click();
        await searchInput.fill('');
        await searchInput.type(searchKeyword, { delay: 100 });

        const searchResponse = await responsePromise;
        expect(searchResponse.status()).toBe(200);

        await page.waitForTimeout(1000);
        console.log('[UI-02] ✅ Live search berfungsi');
    });

    test('UI-03: Pagination Feed Kota — maks 10 kartu, kontrol pagination muncul', async ({ page }) => {
        page.on('dialog', async (d) => await d.accept());

        // Login real ke SPA supaya token valid dan dashboard ter-render
        await loginSPA(page, TEST_CITIZEN_USERNAME, TEST_CITIZEN_PASSWORD);

        // Klik tab Feed Kota (id="tabFeed" di app.js renderTabs())
        const tabFeed = page.locator('#tabFeed');
        await expect(tabFeed).toBeVisible({ timeout: 5000 });
        await tabFeed.click();
        await page.waitForTimeout(2000);

        // Hitung kartu di reportCards (id="reportCards" di app.js)
        const reportCards = page.locator('#reportCards');
        await expect(reportCards).toBeVisible();

        const cards = reportCards.locator('.card');
        const cardCount = await cards.count();

        // Maksimal 10 kartu per halaman
        expect(cardCount).toBeLessThanOrEqual(10);
        expect(cardCount).toBeGreaterThanOrEqual(0);

        // Pagination di paginationNav (id="paginationNav" di app.js)
        const paginationNav = page.locator('#paginationNav');
        await expect(paginationNav).toBeVisible();

        console.log(`[UI-03] ✅ ${cardCount} kartu di Feed Kota`);
    });

    test('UI-04: Klik tombol Buat Laporan → modal #reportModal muncul', async ({ page }) => {
        page.on('dialog', async (d) => await d.accept());

        // Login real ke SPA
        await loginSPA(page, TEST_CITIZEN_USERNAME, TEST_CITIZEN_PASSWORD);

        // Tombol Buat Laporan: id="openReportModalBtn" (app.js loadDashboard())
        const btnBukaModal = page.locator('#openReportModalBtn');
        await expect(btnBukaModal).toBeVisible({ timeout: 10000 });

        const reportModal = page.locator('#reportModal');
        await expect(reportModal).not.toBeVisible();

        await btnBukaModal.click();

        // Modal harus muncul dengan class 'show'
        await expect(reportModal).toBeVisible({ timeout: 5000 });
        const hasShowClass = await reportModal.evaluate((el) => el.classList.contains('show'));
        expect(hasShowClass).toBe(true);

        // Verifikasi semua elemen form (id dari app.js openReportModal())
        await expect(page.locator('#reportForm')).toBeVisible();
        await expect(page.locator('#reportTitle')).toBeVisible();
        await expect(page.locator('#reportCategory')).toBeVisible();
        await expect(page.locator('#reportLocation')).toBeVisible();
        await expect(page.locator('#reportDescription')).toBeVisible();
        // Tombol footer dari app.js loadDashboard()
        await expect(page.locator('#btnSaveDraft')).toBeVisible();
        await expect(page.locator('#btnSubmitReport')).toBeVisible();

        const modalTitle = page.locator('#reportModalTitle');
        await expect(modalTitle).toContainText('Buat Laporan Baru');

        console.log('[UI-04] ✅ Modal #reportModal terbuka dengan semua elemen form');
    });

    test('UI-05: Isi form dan simpan draft → modal tutup, notifikasi muncul', async ({ page }) => {
        page.on('dialog', async (d) => await d.accept());

        // Login real ke SPA
        await loginSPA(page, TEST_CITIZEN_USERNAME, TEST_CITIZEN_PASSWORD);

        // Buka modal
        await page.locator('#openReportModalBtn').click();
        await expect(page.locator('#reportModal')).toBeVisible({ timeout: 5000 });

        // Isi form (id dari app.js collectReportForm())
        await page.locator('#reportTitle').fill('AC Mati di Lab CPS 1');
        await page.locator('#reportCategory').fill('Infrastruktur');
        await page.locator('#reportLocation').fill('Gedung Lab Lantai 2');
        await page.locator('#reportDescription').fill('Unit AC tidak berfungsi sejak pagi hari.');

        // Klik Simpan Draft (id="btnSaveDraft" di app.js)
        await page.locator('#btnSaveDraft').click();
        await page.waitForTimeout(3000);

        // Modal harus tertutup setelah berhasil (app.js saveReport → reportModalInstance.hide())
        await expect(page.locator('#reportModal')).not.toBeVisible({ timeout: 8000 });

        // Notifikasi sukses di messageBox (id="messageBox" di app.js showMessage())
        const messageBox = page.locator('#messageBox');
        await expect(messageBox).toBeVisible({ timeout: 5000 });
        await expect(messageBox).toContainText('berhasil', { timeout: 5000 });

        console.log('[UI-05] ✅ Draft tersimpan: modal tutup, notifikasi muncul');
    });

    test('UI-06: Responsive navbar pada viewport mobile (400x800)', async ({ page }) => {
        await page.setViewportSize({ width: 400, height: 800 });

        // index.html memiliki <nav class="navbar navbar-expand-lg ...">
        await page.goto(SPA_URL);
        await page.waitForLoadState('domcontentloaded');

        const navbar = page.locator('nav.navbar');
        await expect(navbar).toBeVisible({ timeout: 5000 });

        // index.html: navbar-expand-lg → toggler muncul di < 992px
        const navbarToggler = page.locator('.navbar-toggler');
        const togglerCount  = await navbarToggler.count();

        if (togglerCount > 0) {
            await expect(navbarToggler.first()).toBeVisible();
            console.log('[UI-06] ✓ Navbar toggler terlihat di mobile');
        } else {
            const box = await navbar.boundingBox();
            expect(box).not.toBeNull();
            expect(box.width).toBeLessThanOrEqual(420);
            console.log('[UI-06] ✓ Navbar ada dan sesuai viewport mobile');
        }

        const mobileBox   = await navbar.boundingBox();
        const mobileWidth = mobileBox?.width || 0;

        await page.setViewportSize({ width: 1280, height: 800 });
        await page.waitForTimeout(500);

        const desktopBox   = await navbar.boundingBox();
        const desktopWidth = desktopBox?.width || 0;

        expect(desktopWidth).toBeGreaterThan(mobileWidth);
        console.log(`[UI-06] ✅ Responsive: mobile=${mobileWidth}px, desktop=${desktopWidth}px`);

        await page.setViewportSize({ width: 1280, height: 720 });
    });
});