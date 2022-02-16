function acceptModalForm(ev) {
    ev.preventDefault();
    const form = ev.target;
    let modal = form.closest("[name='root-element']");
    let func = modal.getAttribute('acceptHandler');
    window[func](modal, form);
}

function acceptModal(el) {
    let modal = el.closest("[name='root-element']");
    let func = modal.getAttribute('acceptHandler');
    window[func](modal);
}

function openModal(modalId, acceptHandler, { title, subtitle, acceptButton, cancelButton }, arguments) {
    const modal = document.getElementById(modalId);
    // Put dynamic parameters
    let titleElement = modal.querySelector("[name='title-text']");
    if(titleElement && title) titleElement.innerHTML = title;
    let subtitleElement = modal.querySelector("[name='subtitle-text']");
    if(subtitleElement && subtitle) subtitleElement.innerHTML = subtitle;
    let acceptButtonElement = modal.querySelector("[name='accept-button-text']");
    if(acceptButtonElement && acceptButton) acceptButtonElement.innerHTML = acceptButton;
    let cancelButtonElement = modal.querySelector("[name='cancel-button-text']");
    if(cancelButtonElement && cancelButton) cancelButtonElement.innerHTML = cancelButton;
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