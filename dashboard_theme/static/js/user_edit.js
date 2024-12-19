function handleForm(event) {
    event.preventDefault();
    const form = document.getElementById("data-form");

    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const first_name = document.getElementById("first_name").value.trim();
    const last_name = document.getElementById("last_name").value.trim();
    const password1 = document.getElementById("password1").value.trim();
    const password2 = document.getElementById("password2").value.trim();

    let isValid = true;
    const errors = [];
    if (!username) errors.push("Nazwa użytkownika jest wymagana.");
    if (!email || !/\S+@\S+\.\S+/.test(email)) errors.push("Wymagany jest poprawny adres e-mail.");
    if (!first_name) errors.push("Imię jest wymagane.");
    if (!last_name) errors.push("Nazwisko jest wymagane.");
    if (password1 !== ""){
        if (!password1 || password1.length < 6) errors.push("Hasło musi zawierać co najmniej 6 znaków.");
        if (password1 !== password2) errors.push("Hasła nie są zgodne.");
    }

    if (errors.length > 0) {
        alert(errors.join("\n"));
        isValid = false;
    }

    if (isValid) {
        form.submit()
    }
}