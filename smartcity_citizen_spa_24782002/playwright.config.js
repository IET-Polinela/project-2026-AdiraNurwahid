// @ts-check
const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

/**
 * Playwright config untuk SmartCity Citizen SPA
 * 
 * SPA_URL di spec: http://127.0.0.1:5500/smartcity_citizen_spa_24782002/index.html
 * Maka serve root harus satu level di ATAS folder ini (yaitu folder server_smartcity)
 * supaya path /smartcity_citizen_spa_24782002/index.html valid.
 */
module.exports = defineConfig({
    testDir: './tests/playwright',
    timeout: 30_000,
    expect: { timeout: 10_000 },
    fullyParallel: false,
    workers: 1,
    reporter: 'list',

    use: {
        headless: false,
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],

    /**
     * Otomatis jalankan static file server di port 5500
     * sebelum test dimulai, lalu matikan setelahnya.
     *
     * serve .. → melayani folder PARENT (server_smartcity/) di port 5500
     * sehingga URL /smartcity_citizen_spa_24782002/index.html bekerja.
     */
    webServer: {
        command: 'npx serve .. --listen 5500 --no-clipboard',
        url: 'http://127.0.0.1:5500',
        reuseExistingServer: true,
        timeout: 15_000,
    },
});
