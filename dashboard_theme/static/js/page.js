function submitForm(event) {
    event.preventDefault();
    const form = document.getElementById('data-form');
    let errors = [];

    const title = document.getElementById('title');
    const editorContent = CKEDITOR.instances.editor.getData();

    if (title.value.trim() === '') {
        errors.push('Pole tytuł nie może być puste.');
    }

    if (title.value.length >= 200) {
        errors.push('Pole tytuł musi być krótsze niż 200 znaków.');
    }

    if (editorContent === '') {
        errors.push('Strona nie może być pusta.');
    }

    if (errors.length > 0) {
        alert(errors.join("\n"));
    } else {
        form.submit();
    }
}