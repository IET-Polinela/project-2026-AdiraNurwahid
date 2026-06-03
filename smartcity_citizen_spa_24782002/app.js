const BASE_URL = "http://127.0.0.1:8000";
const TOKEN_URL = "/api/token/";
const REFRESH_URL = "/api/token/refresh/";
const REPORTS_URL = "/api/reports/";

function log(...args) {
    console.log("[SmartCitySPA]", ...args);
}

function getToken(key) {
    return localStorage.getItem(key);
}

function setToken(key, value) {
    localStorage.setItem(key, value);
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

function parseJwt(token) {
    if (!token) {
        return null;
    }

    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map((c) => {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        return JSON.parse(jsonPayload);
    } catch (error) {
        log('parseJwt error', error);
        return null;
    }
}

function isTokenExpired(token) {
    const payload = parseJwt(token);

    if (!payload || !payload.exp) {
        return true;
    }

    const nowSeconds = Date.now() / 1000;
    return nowSeconds >= payload.exp - 10;
}

async function refreshAccessToken() {
    const refreshToken = getToken("refresh_token");

    if (!refreshToken) {
        log("No refresh token available.");
        throw new Error("Token refresh diperlukan tetapi refresh token tidak ditemukan.");
    }

    log("Memperbarui access token dengan refresh token...");

    const response = await fetch(BASE_URL + REFRESH_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ refresh: refreshToken })
    });

    if (!response.ok) {
        log("Refresh token gagal", response.status);
        throw new Error("Refresh token gagal");
    }

    const data = await response.json();
    setToken("access_token", data.access);
    log("Access token berhasil diperbarui.");
    return data.access;
}

async function apiRequest(endpoint, { method = "GET", body = null, headers = {} } = {}, retry = true) {
    const accessToken = getToken("access_token");

    if (accessToken && isTokenExpired(accessToken)) {
        log("Access token kadaluarsa, mencoba refresh sebelum request...");
        try {
            await refreshAccessToken();
        } catch (error) {
            log("Refresh token gagal sebelum request", error);
        }
    }

    const requestHeaders = {
        "Content-Type": "application/json",
        ...headers
    };

    const token = getToken("access_token");
    if (token) {
        requestHeaders["Authorization"] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers: requestHeaders
    };

    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    log("fetch", BASE_URL + endpoint, options);
    const response = await fetch(BASE_URL + endpoint, options);
    log("fetch response", endpoint, response.status);

    if (response.status === 401 && retry) {
        log("401 diterima, mencoba refresh token dan retry...");
        try {
            await refreshAccessToken();
            const newToken = getToken("access_token");
            if (newToken) {
                requestHeaders["Authorization"] = `Bearer ${newToken}`;
            }

            const retryResponse = await fetch(BASE_URL + endpoint, options);
            log("retry response", endpoint, retryResponse.status);
            return retryResponse;
        } catch (error) {
            log("Retry setelah refresh gagal", error);
            logout(false);
            return response;
        }
    }

    return response;
}

function isLoggedIn() {
    const accessToken = getToken("access_token");
    const refreshToken = getToken("refresh_token");
    return !!accessToken && !!refreshToken;
}

function updateNav() {
    const navMenu = document.getElementById("nav-menu");

    if (!navMenu) {
        return;
    }

    if (isLoggedIn()) {
        navMenu.innerHTML = `
            <button id="logoutBtn" class="btn btn-outline-light btn-sm">
                <i class="bi bi-box-arrow-right me-1"></i> Logout
            </button>
        `;

        const logoutBtn = document.getElementById("logoutBtn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => logout(true));
        }
    } else {
        navMenu.innerHTML = `
            <a class="btn btn-outline-light btn-sm" href="#login">
                <i class="bi bi-box-arrow-in-right me-1"></i> Login
            </a>
        `;
    }
}

function showMessage(message, type = "info") {
    const messageBox = document.getElementById("messageBox");
    if (!messageBox) {
        console.warn("messageBox tidak ditemukan");
        return;
    }

    messageBox.innerHTML = `
        <div class="alert alert-${type}" role="alert">
            ${message}
        </div>
    `;
}
function logout(showAlert = true) {
    clearTokens();
    updateNav();

    if (showAlert) {
        showMessage("Logout berhasil. Silakan login kembali.", "success");
    }

    window.location.hash = "#login";
}

function formatDate(dateString) {
    if (!dateString) {
        return "-";
    }

    const date = new Date(dateString);
    return date.toLocaleString("id-ID", {
        day: "2-digit",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}

function renderLogin() {
    updateNav();

    document.getElementById("app-content").innerHTML = `
        <section class="auth-page">
            <div class="auth-card shadow-sm">
                <div class="auth-header text-center mb-4">
                    <h2>Login Warga</h2>
                    <p>Masuk untuk melihat laporan dan membuat laporan baru.</p>
                </div>

                <div id="messageBox"></div>

                <form id="loginForm" class="auth-form">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" id="loginUsername" class="form-control" placeholder="Username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" id="loginPassword" class="form-control" placeholder="Password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 btn-lg">Masuk</button>
                </form>
            </div>
        </section>
    `;

    const loginForm = document.getElementById("loginForm");
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const username = document.getElementById("loginUsername").value.trim();
        const password = document.getElementById("loginPassword").value;

        if (!username || !password) {
            showMessage("Username dan password harus diisi.", "warning");
            return;
        }

        showMessage("Sedang mencoba login...", "info");
        log("Mencoba login", username);

        try {
            const response = await apiRequest(TOKEN_URL, {
                method: "POST",
                body: { username, password }
            }, false);

            const data = await response.json();

            if (!response.ok) {
                log("Login gagal", response.status, data);
                showMessage("Login gagal. Periksa username dan password.", "danger");
                return;
            }

            setToken("access_token", data.access);
            setToken("refresh_token", data.refresh);
            log("Login berhasil", data);
            showMessage("Login berhasil! Mengalihkan ke dashboard...", "success");
            window.location.hash = "#dashboard";
        } catch (error) {
            log("Login error", error);
            showMessage("Terjadi kesalahan saat login. Cek konsol untuk detail.", "danger");
        }
    });
}

async function fetchReports() {
    log("Meminta daftar laporan...");
    const response = await apiRequest(REPORTS_URL, { method: "GET" });

    if (response.status === 401) {
        showMessage("Token tidak valid atau kadaluarsa. Silakan login ulang.", "warning");
        return null;
    }

    if (!response.ok) {
        const error = await response.text();
        log("fetchReports error", response.status, error);
        showMessage("Gagal memuat laporan. Cek konsol.", "danger");
        return null;
    }

    const reports = await response.json();
    log("Daftar laporan diterima", reports);
    return reports;
}

function renderReports(reports) {
    const reportCards = document.getElementById("reportCards");
    if (!reportCards) {
        return;
    }

    if (!reports || reports.length === 0) {
        reportCards.innerHTML = `
            <div class="empty-state shadow-sm p-4 rounded-3 text-center">
                <i class="bi bi-journal-x fs-1 text-muted"></i>
                <h5 class="mt-3">Belum ada laporan</h5>
                <p class="text-muted">Buat laporan baru untuk melihatnya di sini.</p>
            </div>
        `;
        return;
    }

    reportCards.innerHTML = reports.map((report) => {
        const statusBadge = {
            DRAFT: "secondary",
            REPORTED: "warning",
            VERIFIED: "info",
            IN_PROGRESS: "primary",
            RESOLVED: "success"
        }[report.status] || "dark";

        return `
            <article class="report-card shadow-sm rounded-4 p-4">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h5 class="fw-bold mb-1">${report.title || 'Tanpa Judul'}</h5>
                        <p class="text-muted mb-1">${report.category || 'Umum'} • ${report.location || 'Lokasi tidak tersedia'}</p>
                    </div>
                    <span class="badge bg-${statusBadge} text-uppercase">${report.status || 'UNKNOWN'}</span>
                </div>
                <p class="report-description">${report.description || 'Tidak ada deskripsi.'}</p>
                <div class="d-flex justify-content-between align-items-center mt-3 text-muted small">
                    <span><i class="bi bi-person-circle"></i> ${report.reporter_username || 'Anonim'}</span>
                    <span><i class="bi bi-calendar-event"></i> ${formatDate(report.created_at)}</span>
                </div>
            </article>
        `;
    }).join('');
}

async function handleCreateReport(event) {
    event.preventDefault();
    const title = document.getElementById("reportTitle").value.trim();
    const category = document.getElementById("reportCategory").value.trim();
    const location = document.getElementById("reportLocation").value.trim();
    const description = document.getElementById("reportDescription").value.trim();

    if (!title || !category || !location || !description) {
        showMessage("Semua field laporan harus diisi.", "warning");
        return;
    }

    showMessage("Menyimpan laporan...", "info");
    log("Membuat laporan baru", { title, category, location });

    try {
        const response = await apiRequest(REPORTS_URL, {
            method: "POST",
            body: {
                title,
                category,
                location,
                description
            }
        });

        if (!response.ok) {
            const errorData = await response.text();
            log("createReport error", response.status, errorData);
            showMessage("Gagal membuat laporan. Cek konsol.", "danger");
            return;
        }

        const report = await response.json();
        log("Laporan dibuat", report);
        showMessage("Laporan berhasil dibuat.", "success");
        document.getElementById("reportForm").reset();
        await loadDashboard();
    } catch (error) {
        log("createReport exception", error);
        showMessage("Terjadi kesalahan saat membuat laporan.", "danger");
    }
}

async function loadDashboard() {
    if (!isLoggedIn()) {
        window.location.hash = "#login";
        return;
    }

    updateNav();

    document.getElementById("app-content").innerHTML = `
        <section class="dashboard-page">
            <div id="messageBox"></div>
            <div class="dashboard-top mb-4">
                <div>
                    <h2>Dashboard Laporan</h2>
                    <p class="text-muted">Lihat semua laporan warga dan kirim laporan baru dengan cepat.</p>
                </div>
                <button id="refreshReportsBtn" class="btn btn-outline-secondary">
                    <i class="bi bi-arrow-clockwise me-1"></i> Segarkan
                </button>
            </div>
            <div class="row gy-4">
                <div class="col-12 col-xl-4">
                    <div class="card shadow-sm rounded-4 p-4">
                        <h4 class="fw-bold mb-3">Buat Laporan Baru</h4>
                        <form id="reportForm" class="report-form">
                            <div class="mb-3">
                                <label class="form-label">Judul</label>
                                <input type="text" id="reportTitle" class="form-control" placeholder="Judul laporan" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Kategori</label>
                                <input type="text" id="reportCategory" class="form-control" placeholder="Contoh: Jalan rusak" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Lokasi</label>
                                <input type="text" id="reportLocation" class="form-control" placeholder="Contoh: Jalan Merdeka" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Deskripsi</label>
                                <textarea id="reportDescription" class="form-control" rows="5" placeholder="Deskripsi masalah" required></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Kirim Laporan</button>
                        </form>
                    </div>
                </div>
                <div class="col-12 col-xl-8">
                    <div id="reportCards" class="report-grid"></div>
                </div>
            </div>
        </section>
    `;

    document.getElementById("reportForm").addEventListener("submit", handleCreateReport);
    document.getElementById("refreshReportsBtn").addEventListener("click", async () => {
        showMessage("Menyegarkan daftar laporan...", "info");
        await initReportList();
    });

    await initReportList();
}

async function initReportList() {
    const reports = await fetchReports();
    if (reports === null) {
        return;
    }
    renderReports(reports);
}

function route() {
    const hash = window.location.hash || "#login";
    log("Routing ke", hash);

    if (hash === "#dashboard") {
        if (!isLoggedIn()) {
            log("Tidak ada token, kembali ke login");
            window.location.hash = "#login";
            return;
        }
        loadDashboard();
    } else {
        renderLogin();
    }
}

window.addEventListener("hashchange", route);
window.addEventListener("DOMContentLoaded", () => {
    updateNav();
    if (isLoggedIn() && window.location.hash === "#login") {
        window.location.hash = "#dashboard";
    }
    route();
});