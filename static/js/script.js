document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.getAttribute("data-confirm");
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll("form[data-validate]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const mode = form.getAttribute("data-validate");
            const get = (name) => (form.querySelector(`[name="${name}"]`)?.value || "").trim();

            if (mode === "login") {
                if (!get("email") || !form.querySelector('[name="password"]').value) {
                    event.preventDefault();
                    alert("Email and password are required.");
                }
                return;
            }

            if (mode === "register") {
                if (!get("name") || !get("email") || !form.querySelector('[name="password"]').value) {
                    event.preventDefault();
                    alert("All fields are required.");
                    return;
                }
                const password = form.querySelector('[name="password"]').value;
                const confirmPassword = form.querySelector('[name="confirm_password"]').value;
                if (password !== confirmPassword) {
                    event.preventDefault();
                    alert("Password and confirm password must match.");
                }
                return;
            }

            if (mode === "task") {
                if (!get("title") || !get("due_date") || !get("priority")) {
                    event.preventDefault();
                    alert("Title, due date, and priority are required.");
                }
            }
        });
    });
});
