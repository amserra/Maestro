function acceptModal(el) {
    let modal = el.closest("[name='root-element']");
    let func = modal.getAttribute('acceptHandler');
    window[func](modal);
}

function openModal(modalId, acceptHandler, { question, description }, arguments) {
    const modal = document.getElementById(modalId);
    // Put dynamic parameters
    let questionElement = modal.querySelector("[name='question-text']");
    questionElement.innerHTML = question;
    let descriptionElement = modal.querySelector("[name='description-text']");
    descriptionElement.innerHTML = description;
    // Append arguments to the modal
    Object.entries(arguments).forEach(
        ([key, value]) => modal.setAttribute(key, value)
    );
    modal.setAttribute('acceptHandler', acceptHandler.name);
    // Show modal
    modal.classList.remove("hidden");
}

function closeModal(el) {
    let modal = el.closest("[name='root-element']");
    modal.classList.add("hidden");
}