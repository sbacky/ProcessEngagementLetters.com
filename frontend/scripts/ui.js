/**
 * @class AlertModal
 */
export class AlertModal {

    constructor(header, message, id) {
        this.modalOverlay = this.createModal(header, message, id);
    }
    /**
     * Creates a modal element with header, message, and close functionality
     * @param {string} header The header text for the modal
     * @param {string} message The message text to display in the modal
     * @param {string} id The id of the modal and modal overlay
     * @returns {HTMLElement} The modal wrapper element
     */
    createModal(header, message, id) {
        const overlay = document.getElementById(`${id}-overlay`);

        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = id;

        const headerEl = document.createElement('div');
        headerEl.className = 'modal-header';
        headerEl.textContent = header;

        const messageEl = document.createElement('div');
        messageEl.className = 'modal-body';
        messageEl.textContent = message;

        const closeButton = document.createElement('button');
        closeButton.className = 'modal-close';
        closeButton.textContent = '×';
        closeButton.onclick = () => this.hideModal();

        modal.appendChild(headerEl);
        modal.appendChild(messageEl);
        modal.appendChild(closeButton);
        overlay.appendChild(modal);

        // Close modal on outside click
        overlay.addEventListener('click', (event) => {
            if (event.target === overlay) {
                this.hideModal();
            }
        });

        return overlay;
    }

    showModal() {
        this.modalOverlay.style.display = 'flex';
    }
    
    hideModal() {
        this.modalOverlay.style.display = 'none';
    }

    deleteModal() {
        this.modalOverlay.remove();
    }
}

/**
 * @class AlertStatus
 */
export class AlertStatus {
    constructor() {
        this.alert = null;
    }

    /**
     * Creates an alert message element and appends it to the body.
     * @param {string} message The message text to display.
     * @param {string[]} classes Array of classes to style the alert.
     */
    createAlert(message, classes) {
        this.alert = document.createElement('div');
        this.alert.textContent = message;
        this.alert.classList.add(['alert']);
        if (classes) {
            this.alert.classList.add(classes);
        }
    }

    /**
     * Return created alert element
     * @returns alert
     */
    getAlert() {
        return this.alert;
    }

    /**
     * Shows the alert message.
     */
    showAlert() {
        if (this.alert) {
            this.alert.style.display = 'block';
        }
    }

    /**
     * Hides the alert message.
     */
    hideAlert() {
        if (this.alert) {
            this.alert.style.display = 'none';
        }
    }

    /**
     * Deletes the alert message from the document.
     */
    deleteAlert() {
        if (this.alert) {
            this.alert.remove();
            this.alert = null;
        }
    }
}
  