'use strict';
function modalShown(event) {
    let button = event.relatedTarget;
    let userId = button.dataset.userId;
    let userName = button.dataset.userName;
    let modal = document.getElementById('deleteModal');

    modal.querySelector('.modal-body').textContent =
        `Вы уверены, что хотите удалить пользователя ${userName}?`;

    let form = document.getElementById('deleteModalForm');
    form.action = `/lab4/users/${userId}/delete`;
}

document.addEventListener('DOMContentLoaded', function() {
    let modal = document.getElementById('deleteModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', modalShown);
    }
});