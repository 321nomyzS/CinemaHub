function submitForm(event) {
    event.preventDefault();
    const form = document.getElementById('data-form');
    const crewMembersCount = document.getElementById('crew-members-count').value;
    const titleInput = document.getElementById('title');
    const releaseDateInput = document.getElementById('release_date');
    const descriptionInput = document.getElementById('description');
    const category = document.getElementById('category');

    let errors = [];

    if (!titleInput.value) {
        errors.push("Tytuł jest wymagany.");
    } else if (titleInput.value.length > 150) {
        errors.push("Tytuł nie może mieć więcej niż 150 znaków.");
    }
    if (!releaseDateInput.value) {
        errors.push("Data premiery jest wymagana.");
    }
    if (!descriptionInput.value) {
        errors.push("Opis jest wymagany.");
    }
    if (!category.value) {
        errors.push(`Kategoria musi być wybrana.`);
    }

    for (let i = 1; i <= crewMembersCount; i++) {
        const memberSelect = document.getElementById(`member-${i}`);
        const roleSelect = document.getElementById(`role-${i}`);
        const characterNameInput = document.getElementById(`character_name-${i}`);

        if (!memberSelect.value) {
            errors.push(`Członek obsady (formularz ${i}) musi być wybrany.`);
        }

        if (!roleSelect.value) {
            errors.push(`Rola (formularz ${i}) musi być wybrana.`);
        }

        if (characterNameInput.value && characterNameInput.value.length > 150) {
            errors.push(`Nazwa postaci (formularz ${i}) nie może mieć więcej niż 150 znaków.`);
        }
    }

    if (errors.length > 0) {
        alert(errors.join("\n"));
    } else {
        form.submit();
    }
}


let memberCount = 0;

window.onload = function () {
    const memberCountElement = document.getElementById('crew-members-count');
    if (memberCountElement) {
        memberCount = parseInt(memberCountElement.value, 10);
    }
};

function addMember() {
    const defaultMember = document.getElementById('default-crew-member');
    const container = document.getElementById('crew-members');
    const crewMembersCount = document.getElementById('crew-members-count');

    memberCount++;
    crewMembersCount.value = memberCount;

    const newMember = defaultMember.cloneNode(true);
    newMember.style.display = 'grid';
    newMember.id = `crew-member-${memberCount}`;

    const memberSelect = newMember.querySelector('#member');
    memberSelect.id = `member-${memberCount}`;
    memberSelect.name = `member-${memberCount}`;

    const roleSelect = newMember.querySelector('#role');
    roleSelect.id = `role-${memberCount}`;
    roleSelect.name = `role-${memberCount}`;

    const characterNameInput = newMember.querySelector('#character_name');
    characterNameInput.id = `character_name-${memberCount}`;
    characterNameInput.name = `character_name-${memberCount}`;

    const deleteButton = newMember.querySelector('a');
    deleteButton.setAttribute('onclick', `deleteMember(${memberCount})`);

    container.appendChild(newMember);
    new TomSelect(`#member-${memberCount}`);
}

function deleteMember(id) {
    const memberToDelete = document.getElementById(`crew-member-${id}`);
    const crewMembersCount = document.getElementById('crew-members-count');

    if (memberToDelete) {
        memberToDelete.remove();
    } else {
        console.error(`Nie znaleziono członka obsady o id 'crew-member-${id}'`);
    }
    updateIds();
    memberCount--;
    crewMembersCount.value = memberCount;
}

function updateIds() {
    const container = document.getElementById('crew-members');
    const members = container.querySelectorAll('[id^="crew-member-"]'); // Znajdujemy wszystkie formularze w kontenerze

    let newMemberCount = 0;  // Licznik dla nowych id

    members.forEach(member => {
        newMemberCount++;

        // Aktualizujemy id formularza
        member.id = `crew-member-${newMemberCount}`;

        // Zmieniamy id i name dla wszystkich pól wewnątrz formularza
        const memberSelect = member.querySelector('[id^="member-"]');
        if (memberSelect) {
            memberSelect.id = `member-${newMemberCount}`;
            memberSelect.name = `member-${newMemberCount}`;
        }

        const roleSelect = member.querySelector('[id^="role-"]');
        if (roleSelect) {
            roleSelect.id = `role-${newMemberCount}`;
            roleSelect.name = `role-${newMemberCount}`;
        }

        const characterNameInput = member.querySelector('[id^="character_name-"]');
        if (characterNameInput) {
            characterNameInput.id = `character_name-${newMemberCount}`;
            characterNameInput.name = `character_name-${newMemberCount}`;
        }

        // Zaktualizowanie przycisku "Usuń"
        const deleteButton = member.querySelector('a');
        if (deleteButton) {
            deleteButton.setAttribute('onclick', `deleteMember(${newMemberCount})`);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const memberCount = parseInt(document.getElementById('crew-members-count').value, 10);
    console.log(memberCount);
    for (let i = 1; i <= memberCount; i++) {
        const memberSelect = document.getElementById(`member-${i}`);
        if (memberSelect) {
            new TomSelect(`#member-${i}`);
        }
    }
});