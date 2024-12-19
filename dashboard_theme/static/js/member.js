function submitForm(event) {
    event.preventDefault();
    const form = document.getElementById('data-form');
    let errors = [];

    const first_name = document.getElementById('first_name');
    const last_name = document.getElementById('last_name');
    const birth_date = new Date(document.getElementById('birth_date').value);
    const description = document.getElementById('description');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    birth_date.setHours(0, 0, 0, 0);

    if (first_name.value.trim() === '') {
        errors.push('Pole imię nie może być puste.');
    }
    if (first_name.value.length > 150) {
        errors.push('Pole imię może mieć maksymalnie 150 znaków.')
    }

    if (last_name.value.trim() === '') {
        errors.push('Pole nazwisko nie może być puste.');
    }
    if (last_name.value.length > 150) {
        errors.push('Pole nazwisko może mieć maksymalnie 150 znaków.')
    }

    if (description.value.trim() === '') {
        errors.push('Pole opis nie może być puste.');
    }

    if (birth_date > today) {
        errors.push('Nieprawidłowa data.');
    }

    if (errors.length > 0) {
        alert(errors.join("\n"));
    } else {
        form.submit();
    }
}