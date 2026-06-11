// ==========================
// GLOBAL STATE
// ==========================

let currentPage = 1;
let currentTab = "my_reports";
let editingReportId = null;

let allReports = [];
let totalPages = 1;
let reportModalInstance = null;

const BASE_URL =  "http://103.151.63.71:8006";
const TOKEN_URL = "/api/token/";
const REFRESH_URL = "/api/token/refresh/";
const REPORTS_URL = "/api/reports/";

const STATUS_BADGES = {
    DRAFT: "secondary",
    REPORTED: "warning",
    VERIFIED: "info",
    IN_PROGRESS: "primary",
    RESOLVED: "success"
};

const STATUS_PROGRESS = {
    DRAFT: 20,
    REPORTED: 40,
    VERIFIED: 60,
    IN_PROGRESS: 80,
    RESOLVED: 100
};

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
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
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
        <section class="auth-page d-flex justify-content-center align-items-center min-vh-75">
            <div class="auth-card shadow-sm rounded-4 p-4 bg-white" style="max-width: 420px; width: 100%;">
                <div class="auth-header text-center mb-4">
                    <h2>Login Warga</h2>
                    <p class="text-muted">Masuk untuk melihat laporan dan membuat laporan baru.</p>
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
    const response = await apiRequest(`${REPORTS_URL}?tab=${currentTab}&page=${currentPage}`);

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

    const data = await response.json();
    totalPages = Math.max(1, Math.ceil((data.count || 0) / 10));
    allReports = Array.isArray(data.results) ? data.results : [];
    return data;
}

function getReportSummary() {
    return allReports.reduce(
        (summary, report) => {
            if (report.status === "DRAFT") summary.draft += 1;
            if (report.status === "REPORTED") summary.reported += 1;
            if (report.status === "VERIFIED") summary.verified += 1;
            return summary;
        },
        { draft: 0, reported: 0, verified: 0 }
    );
}

function renderSidebar() {
    const summary = getReportSummary();
    const sidebarStats = document.getElementById("sidebarStats");
    if (!sidebarStats) {
        return;
    }

    sidebarStats.innerHTML = `
        <div class="row g-3">
            <div class="col-12">
                <div class="card shadow-sm rounded-4 p-3 h-100">
                    <div class="card-body">
                        <h6 class="text-uppercase text-muted mb-2">Total Draft</h6>
                        <p class="display-6 fw-bold mb-1">${summary.draft}</p>
                        <p class="small text-muted mb-0">Draft di halaman ini</p>
                    </div>
                </div>
            </div>
            <div class="col-12">
                <div class="card shadow-sm rounded-4 p-3 h-100">
                    <div class="card-body">
                        <h6 class="text-uppercase text-muted mb-2">Total Reported</h6>
                        <p class="display-6 fw-bold mb-1">${summary.reported}</p>
                        <p class="small text-muted mb-0">Laporan yang dikirim</p>
                    </div>
                </div>
            </div>
            <div class="col-12">
                <div class="card shadow-sm rounded-4 p-3 h-100">
                    <div class="card-body">
                        <h6 class="text-uppercase text-muted mb-2">Total Verified</h6>
                        <p class="display-6 fw-bold mb-1">${summary.verified}</p>
                        <p class="small text-muted mb-0">Laporan yang diverifikasi</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderTabs() {
    const tabControls = document.getElementById("tabControls");
    if (!tabControls) {
        return;
    }

    const myReportsActive = currentTab === "my_reports" ? "active" : "";
    const feedActive = currentTab === "feed" ? "active" : "";

    tabControls.innerHTML = `
        <div class="btn-group" role="group" aria-label="Tab navigation">
            <button id="tabMyReports" type="button" class="btn btn-outline-primary ${myReportsActive}">Laporan Saya</button>
            <button id="tabFeed" type="button" class="btn btn-outline-primary ${feedActive}">Feed Kota</button>
        </div>
    `;

    document.getElementById("tabMyReports").addEventListener("click", () => changeTab("my_reports"));
    document.getElementById("tabFeed").addEventListener("click", () => changeTab("feed"));
}

function renderReports() {
    const reportCards = document.getElementById("reportCards");
    if (!reportCards) {
        return;
    }

    if (!allReports || allReports.length === 0) {
        reportCards.innerHTML = `
            <div class="empty-state shadow-sm p-4 rounded-4 text-center bg-white">
                <i class="bi bi-journal-x fs-1 text-muted"></i>
                <h5 class="mt-3">Belum ada laporan</h5>
                <p class="text-muted">Gunakan tombol Buat Laporan untuk menambahkan laporan baru.</p>
            </div>
        `;
        document.getElementById("paginationNav").innerHTML = "";
        return;
    }

    reportCards.innerHTML = allReports.map((report) => {
        const badgeClass = STATUS_BADGES[report.status] || "dark";
        const progressValue = STATUS_PROGRESS[report.status] || 0;
        const canEditOrDelete = report.is_owner === true && report.status === "DRAFT";

        return `
            <div class="card shadow-sm rounded-4 mb-4">
                <div class="card-body">
                    <div class="d-flex flex-column flex-md-row justify-content-between gap-3">
                        <div>
                            <h5 class="fw-bold mb-1">${report.title || "Tanpa Judul"}</h5>
                            <p class="text-muted mb-1">${report.category || "Umum"} • ${report.location || "Lokasi tidak tersedia"}</p>
                        </div>
                        <span class="badge bg-${badgeClass} text-uppercase align-self-start">${report.status || "UNKNOWN"}</span>
                    </div>

                    <div class="progress rounded-pill bg-light mt-3" style="height: 10px;">
                        <div class="progress-bar bg-${badgeClass}" role="progressbar" style="width: ${progressValue}%" aria-valuenow="${progressValue}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>

                    <p class="mt-3 mb-2">${report.description || "Tidak ada deskripsi."}</p>

                    <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-3 text-muted small">
                        <span><i class="bi bi-person-circle me-1"></i>${report.reporter_username || "Anonim"}</span>
                        <span><i class="bi bi-calendar-event me-1"></i>${formatDate(report.created_at)}</span>
                    </div>

                    ${canEditOrDelete ? `
                        <div class="mt-3 d-flex gap-2 flex-wrap">
                            <button data-action="edit" data-id="${report.id}" class="btn btn-outline-secondary btn-sm">Edit</button>
                            <button data-action="delete" data-id="${report.id}" class="btn btn-outline-danger btn-sm">Delete</button>
                        </div>
                    ` : ""}
                </div>
            </div>
        `;
    }).join("");

    reportCards.querySelectorAll("button[data-action]").forEach((button) => {
        button.addEventListener("click", async (event) => {
            const action = event.currentTarget.dataset.action;
            const reportId = event.currentTarget.dataset.id;
            const report = allReports.find((item) => String(item.id) === reportId);
            if (!report) {
                return;
            }

            if (action === "edit") {
                openReportModal(report);
            }

            if (action === "delete") {
                await handleDeleteReport(report.id);
            }
        });
    });
}

function renderPagination() {
    const paginationNav = document.getElementById("paginationNav");
    if (!paginationNav) {
        return;
    }

    if (totalPages <= 1) {
        paginationNav.innerHTML = "";
        return;
    }

    let pagesHtml = "";
    for (let page = 1; page <= totalPages; page += 1) {
        pagesHtml += `
            <li class="page-item ${page === currentPage ? "active" : ""}">
                <button class="page-link" type="button" data-page="${page}">${page}</button>
            </li>
        `;
    }

    paginationNav.innerHTML = `
        <nav aria-label="Pagination laporan">
            <ul class="pagination justify-content-center mb-0">
                <li class="page-item ${currentPage === 1 ? "disabled" : ""}">
                    <button class="page-link" type="button" data-page="${currentPage - 1}">Previous</button>
                </li>
                ${pagesHtml}
                <li class="page-item ${currentPage === totalPages ? "disabled" : ""}">
                    <button class="page-link" type="button" data-page="${currentPage + 1}">Next</button>
                </li>
            </ul>
        </nav>
    `;

    paginationNav.querySelectorAll("button[data-page]").forEach((button) => {
        button.addEventListener("click", async (event) => {
            const page = Number(event.currentTarget.dataset.page);
            if (page < 1 || page > totalPages || page === currentPage) {
                return;
            }
            currentPage = page;
            await loadDashboardReports();
        });
    });
}

function changeTab(tab) {
    if (currentTab === tab) {
        return;
    }
    currentTab = tab;
    currentPage = 1;
    loadDashboardReports();
}

function openReportModal(report = null) {
    editingReportId = report ? report.id : null;

    document.getElementById("reportModalTitle").textContent = report ? "Edit Draft" : "Buat Laporan Baru";
    document.getElementById("reportModalHint").textContent = report
        ? "Edit laporan draft Anda, lalu simpan atau ajukan ke feed kota."
        : "Isi laporan baru Anda lalu simpan sebagai draft atau ajukan langsung ke feed kota.";

    document.getElementById("reportTitle").value = report ? report.title : "";
    document.getElementById("reportCategory").value = report ? report.category : "";
    document.getElementById("reportLocation").value = report ? report.location : "";
    document.getElementById("reportDescription").value = report ? report.description : "";

    reportModalInstance.show();
}

function collectReportForm() {
    return {
        title: document.getElementById("reportTitle").value.trim(),
        category: document.getElementById("reportCategory").value.trim(),
        location: document.getElementById("reportLocation").value.trim(),
        description: document.getElementById("reportDescription").value.trim()
    };
}

async function saveReport(status) {
    const reportData = collectReportForm();

    if (!reportData.title || !reportData.category || !reportData.location || !reportData.description) {
        showMessage("Semua field laporan harus diisi.", "warning");
        return;
    }

    reportData.status = status;
    const url = editingReportId ? `${REPORTS_URL}${editingReportId}/` : REPORTS_URL;
    const method = editingReportId ? "PUT" : "POST";
    const actionLabel = editingReportId ? "memperbarui laporan" : "membuat laporan";

    showMessage(`${status === "REPORTED" ? "Mengajukan laporan..." : "Menyimpan draft..."}`, "info");

    try {
        const response = await apiRequest(url, {
            method,
            body: reportData
        });

        if (!response.ok) {
            const errorText = await response.text();
            log("saveReport error", response.status, errorText);
            showMessage(`Gagal ${actionLabel}. Cek konsol.`, "danger");
            return;
        }

        await response.json();
        reportModalInstance.hide();
        showMessage(`Laporan berhasil ${status === "REPORTED" ? "diajukan" : "disimpan sebagai draft"}.`, "success");
        await loadDashboardReports();
    } catch (error) {
        log("saveReport exception", error);
        showMessage(`Terjadi kesalahan saat ${actionLabel}.`, "danger");
    }
}

async function handleDeleteReport(reportId) {
    const confirmed = confirm("Yakin ingin menghapus laporan?");
    if (!confirmed) {
        return;
    }

    showMessage("Menghapus laporan...", "info");
    try {
        const response = await apiRequest(`${REPORTS_URL}${reportId}/`, {
            method: "DELETE"
        });

        if (!response.ok) {
            const errorText = await response.text();
            log("deleteReport error", response.status, errorText);
            showMessage("Gagal menghapus laporan. Cek konsol.", "danger");
            return;
        }

        showMessage("Laporan berhasil dihapus.", "success");
        await loadDashboardReports();
    } catch (error) {
        log("deleteReport exception", error);
        showMessage("Terjadi kesalahan saat menghapus laporan.", "danger");
    }
}

async function loadDashboardReports() {
    const data = await fetchReports();
    if (data === null) {
        return;
    }

    renderSidebar();
    renderTabs();
    renderReports();
    renderPagination();

    const statusText = document.getElementById("dashboardStatus");
    if (statusText) {
        statusText.textContent = `${data.count || 0} laporan ditemukan`;
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
            <div class="dashboard-top d-flex flex-column flex-lg-row justify-content-between align-items-start align-items-lg-center gap-3 mb-4">
                <div>
                    <h2 class="mb-1">Dashboard Laporan</h2>
                    <p class="text-muted mb-0">Kelola laporan Anda dan lihat feed kota secara real-time.</p>
                </div>
                <div class="d-flex flex-column flex-sm-row gap-2">
                    <button id="refreshReportsBtn" class="btn btn-outline-secondary">
                        <i class="bi bi-arrow-clockwise me-1"></i> Segarkan
                    </button>
                    <button id="openReportModalBtn" class="btn btn-primary">
                        <i class="bi bi-plus-lg me-1"></i> Buat Laporan
                    </button>
                </div>
            </div>
            <div class="row g-4">
                <aside class="col-12 col-lg-3">
                    <div id="sidebarStats"></div>
                </aside>
                <div class="col-12 col-lg-9">
                    <div class="card shadow-sm rounded-4 p-4">
                        <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-3 mb-4">
                            <div>
                                <h5 class="mb-1">${currentTab === "feed" ? "Feed Kota" : "Laporan Saya"}</h5>
                                <p class="text-muted mb-0" id="dashboardStatus"></p>
                            </div>
                            <div id="tabControls"></div>
                        </div>
                        <div id="reportCards"></div>
                        <div id="paginationNav" class="mt-4"></div>
                    </div>
                </div>
            </div>
        </section>

        <div class="modal fade" id="reportModal" tabindex="-1" aria-labelledby="reportModalTitle" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content rounded-4">
                    <div class="modal-header">
                        <h5 class="modal-title" id="reportModalTitle">Buat Laporan Baru</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted" id="reportModalHint">Isi laporan baru Anda lalu simpan sebagai draft atau ajukan langsung ke feed kota.</p>
                        <form id="reportForm">
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
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" id="btnSaveDraft" class="btn btn-outline-secondary">Simpan Draft</button>
                        <button type="button" id="btnSubmitReport" class="btn btn-primary">Ajukan Laporan</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    reportModalInstance = new bootstrap.Modal(document.getElementById("reportModal"));
    document.getElementById("refreshReportsBtn").addEventListener("click", async () => {
        showMessage("Menyegarkan daftar laporan...", "info");
        await loadDashboardReports();
    });
    document.getElementById("openReportModalBtn").addEventListener("click", () => openReportModal());
    document.getElementById("reportForm").addEventListener("submit", (event) => event.preventDefault());
    document.getElementById("btnSaveDraft").addEventListener("click", () => saveReport("DRAFT"));
    document.getElementById("btnSubmitReport").addEventListener("click", () => saveReport("REPORTED"));

    await loadDashboardReports();
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
