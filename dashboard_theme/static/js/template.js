function addFields(matches) {
    const container = document.getElementById('template-fields-container');
    const templateField = document.getElementById('template-field');
    container.innerHTML = '';

    matches.forEach((match, index) => {
        const newField = templateField.cloneNode(true);

        const fieldName = newField.querySelector('#field-name');
        const fieldType = newField.querySelector('#field-type');

        fieldName.id = `field-name-${index + 1}`;
        fieldName.name = `field-name-${index + 1}`;
        fieldName.value = match;

        fieldType.id = `field-type-${index + 1}`;
        fieldType.name = `field-type-${index + 1}`;

        const nameLabel = newField.querySelector('label[for="field-name"]');
        nameLabel.textContent = `Nazwa pola ${index + 1}`;

        const typeLabel = newField.querySelector('label[for="field-type"]');
        typeLabel.textContent = `Typ pola ${index + 1}`;
        newField.style.display = "block";

        container.appendChild(newField);
    });
}

function getFields() {
    const editorContent =CKEDITOR.instances.editor.getData();
    const markerRegex = /{{(.*?)}}/g;
    return [...editorContent.matchAll(markerRegex)].map(match => match[1])
}

function fieldSynchronize() {
    const matches = getFields();
    addFields(matches);
    const fieldNumber = document.getElementById('fields-numbers');
    fieldNumber.value = matches.length;
}


function submitForm(event) {
    event.preventDefault();
    const form = document.getElementById('data-form');
    const fields = getFields();
    let errors = [];

    const elements = form.elements;
    const formValues = [];
    const formTypes = [];

    for (let i = 0; i < elements.length; i++) {
        const element = elements[i];
        if (element.name && element.name.startsWith('field-name-')) {
            formValues.push(element.value.trim());
            if (!element.value.trim()) {
                errors.push("Nazwa pola nie może być pusta");
            }
        }
        if (element.name && element.name.startsWith('field-type-')) {
            if (!element.value.trim()) {
                errors.push("Nie wszystkie pola mają wybrane typy");
            }
        }
    }

    const missingInForm = fields.filter(field => !formValues.includes(field));
    const extraInForm = formValues.filter(value => !fields.includes(value));

    const uniqueFields = new Set(fields);
    if (fields.length !== uniqueFields.size) {
        errors.push("Każda nazwa pola może być tylko raz użyta w szablonie");
    }

    if (missingInForm.length > 0) {
        errors.push(`Nie opisałeś następujących pól: ${missingInForm.join(', ')}`);
    }

    if (extraInForm.length > 0) {
        errors.push(`W szablonie nie znajdują się pola: ${extraInForm.join(', ')}`);
    }

    const name = document.getElementById('name');
    const description = document.getElementById('description');
    const editorContent = CKEDITOR.instances.editor.getData();

    if (name.value.trim() === '') {
        errors.push('Pole nazwa nie może być puste.');
    }

    if (description.value.trim() === '') {
        errors.push('Pole opis nie może być puste.');
    }

    if (editorContent === '') {
        errors.push('Szablon nie może być pusty');
    }

    if (errors.length > 0) {
        alert(errors.join("\n"));
    } else {
        form.submit();
    }
}