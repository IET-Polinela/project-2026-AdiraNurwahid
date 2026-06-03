const routes = {

    "#login": `

    <div class="row justify-content-center mt-5">

        <div class="col-lg-4">

            <div class="card shadow border-0 p-4">

                <h3 class="text-center fw-bold mb-4">
                    Login Warga
                </h3>

                <form id="loginForm">

                    <input
                        type="text"
                        id="loginUsername"
                        class="form-control mb-3"
                        placeholder="Username"
                        required
                    >

                    <input
                        type="password"
                        id="loginPassword"
                        class="form-control mb-3"
                        placeholder="Password"
                        required
                    >

                    <button class="btn btn-primary w-100">
                        Login
                    </button>

                </form>

            </div>

        </div>

    </div>
    `,

    "#dashboard": `

    <div class="row g-4">

        <aside class="col-12 col-lg-3">

            <div class="card border-0 shadow-sm p-3">

                <h5 class="fw-bold">
                    <i class="bi bi-person-circle me-2"></i>
                    Citizen
                </h5>

            </div>

        </aside>

        <section class="col-12 col-lg-6">

            <div class="card border-0 shadow-sm p-4 text-center">

                <h3 class="fw-bold">
                    Selamat Datang
                </h3>

                <p>
                    Portal Smart City
                </p>

            </div>

        </section>

        <aside class="col-12 col-lg-3">

            <div class="card border-0 shadow-sm p-3">

                <button
                    class="btn btn-danger w-100"
                    onclick="logout()"
                >
                    Logout
                </button>

            </div>

        </aside>

    </div>
    `
};

function handleRouting(){

    const hash = window.location.hash || "#login";

    document.getElementById("app-content").innerHTML =
        routes[hash];

    if(hash === "#login"){
        setupLoginForm();
    }
}

window.addEventListener(
    "hashchange",
    handleRouting
);

window.addEventListener(
    "DOMContentLoaded",
    handleRouting
);