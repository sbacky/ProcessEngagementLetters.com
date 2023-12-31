/* Copyright (C) 2023 - Neil Crum (nhc.crum@outlook.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License */
import { api } from '../scripts/api.js';
import { AlertModal, AlertStatus } from '../scripts/ui.js';

class PELApp {
    static #instance

    constructor() {
        if (PELApp.#instance) {
            return PELApp.#instance;
        }
        PELApp.#instance = this;

        // Alert modal
        this.alertModal = null;
        // Alert status
        this.alertStatus = new AlertStatus();

        // format {"process": "process_name", "value": number}
        this.progress = null;
        // format {"process": "process_name", "method": "process_method", "message": "display_message"}
        this.runningProcess = null;
        // format {"error": "error_name", "message": "error_message", "process": "process_name", "method": "method_name"}
        this.lastExecutionError = null;

        // property names to inject into document
        this.propNames = [
            '--primary',
            '--secondary',
            '--accent',
            '--link',
            '--info',
            '--error',
            '--success',
            '--warning',
            '--gray'
        ];
    }

    /**
     * Set progress bar in container id to value
     */
    setProgress() {
        const progressBarContainer = document.getElementById(`${this.progress.process}-progressBarContainer`);
        if (progressBarContainer.hidden) {
            progressBarContainer.hidden = ! progressBarContainer.hidden;
        }
        const progressBar = progressBarContainer.querySelector('.progress-bar');

        progressBar.style.width = `${this.progress.value * 100}%`;
    }

    /**
     * Attach alert to element at id
     * @param {string} id element id to add alert to
     * @param {HTMLDivElement} alert HTMLDivElement of the alert
     */
    sendAlert(id, alert) {
        const alertPlaceholder = document.getElementById(id);
        alertPlaceholder.appendChild(alert);
    }

    /**
     * Add custom event listeners to handle socket io events.
     */
    #addSocketHandlers() {
        api.addCustomEventListener('process-start', (event) => {
            // format "detail": "message"
            this.runningProcess = null;
            this.lastExecutionError = null;
            this.progress = null;
        });

        api.addCustomEventListener('processing', (event) => {
            // format "detail": {"process": "process_name", "method": "process_method", "message": "display_message"}
            this.runningProcess = event.detail;

            // TODO: update alert modal
            if (this.alertStatus.alert !== null) {
                this.alertStatus.hideAlert();
                this.alertStatus.deleteAlert();
            }
            this.alertStatus.createAlert(`${event.detail.message}...`, ['alert-info']);
            this.sendAlert(`${event.detail.process}-alertPlaceholder`, this.alertStatus.getAlert());
            this.alertStatus.showAlert();
        });

        api.addCustomEventListener('complete', (event) => {
            // format "detail": "message"
            if (this.alertStatus.alert !== null) {
                this.alertStatus.deleteAlert();
            }
            this.alertStatus.createAlert(event.detail, ['alert-success']);
            this.sendAlert(`${this.runningProcess.process}-alertPlaceholder`, this.alertStatus.getAlert());
            this.alertStatus.showAlert();
        });

        api.addCustomEventListener('progress', (event) => {
            // format "detail": {"process": "process_name", "value": number}
            this.progress = event.detail;
            this.setProgress();
        });

        api.addCustomEventListener('process-error', (event) => {
            // format "detail": {"error": "error_name", "message": "error_message", "process": "process_name", "method": "method_name"}
            this.lastExecutionError = event.detail;
            // TODO: process error to locate where error occured
            // call modal factory to display error message
            if (this.alertStatus.alert !== null) {
                this.alertStatus.hideAlert();
                this.alertStatus.deleteAlert();
            }
            const message = `${event.detail.error}: ${event.detail.message}`;
            this.alertStatus.createAlert(message, ['alert-error']);
            const proc_name = this.runningProcess.process !== null ? this.runningProcess.process : event.detail.process;
            this.sendAlert(`${proc_name}-alertPlaceholder`, this.alertStatus.getAlert());
            this.alertStatus.showAlert();
        });

        api.addCustomEventListener('connected', (event) => {
            // format "detail": "message"
            if (this.alertModal !== null) {
                this.alertModal.hideModal();
            }
        });

        api.addCustomEventListener('disconnected', (event) => {
            // format "detail": "message"
            if (this.alertModal == null) {
                this.alertModal = new AlertModal('Disconnected', event.detail, 'alertModal');
            }
            this.alertModal.showModal();
        });

        api.addCustomEventListener('process-results', (event) => {
            const resultContainer = document.getElementById(`${event.detail.process}-results`);
            const fileStatus = event.detail.status;
            const filename = event.detail.filename;

            const listItem = document.createElement('li');
            listItem.className = fileStatus === 'success' ? 'success-text' : 'error-text';
            listItem.textContent = `${fileStatus === 'success' ? 'Processed' : 'Failed'}: ${filename}`;

            console.log(listItem);

            resultContainer.appendChild(listItem);
        });

        api.connectSocket();
    }

    #applySavedColors() {
        this.propNames.forEach((propertyName) => {
            const lightColor = localStorage.getItem(`${propertyName}-light`);
            const darkColor = localStorage.getItem(`${propertyName}-dark`);
            const rgbaColor = localStorage.getItem(`${propertyName}-rgb`);
    
            if (lightColor) document.documentElement.style.setProperty(`${propertyName}-light`, lightColor);
            if (darkColor) document.documentElement.style.setProperty(`${propertyName}-dark`, darkColor);
            if (rgbaColor) document.documentElement.style.setProperty(`${propertyName}-rgb`, rgbaColor);
        });
    }

    /**
     * Dynamically lighten and darken colors on document root.
     * 
     * Lighten: lightens the color passed by the percent passed
     * 
     * Darken: darkens the color passed by the percent passed
     */
    #addDynamicColors() {
        this.propNames.forEach((color) => {
            this.#adjustColor(color, 15);
        });
    }

    /**
     * Check if color string is a valid hexadecimal string
     * @param {string} color 
     * @returns {boolean} true if string is a hexidecimal, false otherwise.
     */
    #isValidHex(color) {
        return /^#([0-9A-F]{3}){1,2}$/i.test(color);
    }

    /**
     * Convert short hexidecimal strings to full hexidecimal
     * @param {string} hex 
     * @returns {string} full hxidecimal string
     */
    #convertShortHexToFull(hex) {
        if (hex.length === 4) {
            return '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
        }
        return hex;
    }

    /**
     * Add lighter and darker versions of color property passed to root element.
     * @param {string} propertyName property name string
     * @param {number} percent percent to lighten and darken color by
     */
    #adjustColor(propertyName, percent) {
        let color = getComputedStyle(document.documentElement).getPropertyValue(propertyName);

        if (!this.#isValidHex(color)) {
            api.logToServer('error', `Invalid hex color format: ${color}`)
            console.error("Invalid hex color format:", color);
            return color;
        }

        color = this.#convertShortHexToFull(color);

        const lighterColor = this.#lightenColor(color, percent);
        const darkerColor = this.#darkenColor(color, percent);
        const rgbaColor = this.#hexToRgba(color, 0.5);

        document.documentElement.style.setProperty(`${propertyName}-light`, lighterColor);
        document.documentElement.style.setProperty(`${propertyName}-dark`, darkerColor);
        document.documentElement.style.setProperty(`${propertyName}-rgb`, rgbaColor);

        // Save the new colors to local storage
        localStorage.setItem(`${propertyName}-light`, lighterColor);
        localStorage.setItem(`${propertyName}-dark`, darkerColor);
        localStorage.setItem(`${propertyName}-rgb`, rgbaColor);
    }

    /**
     * Lighten color passed by the percent passed
     * @param {string} color 
     * @param {number} percent 
     * @returns lightened color
     */
    #lightenColor(color, percent) {
        const num = parseInt(color.slice(1), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = ((num >> 8) & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;

        return "#" + (0x1000000 + Math.max(0, Math.min(255, R)) * 0x10000 + Math.max(0, Math.min(255, G)) * 0x100 + Math.max(0, Math.min(255, B))).toString(16).slice(1);
    }

    /**
     * Darken color passed by the percent passed
     * @param {string} color 
     * @param {number} percent
     * @returns darkened color 
     */
    #darkenColor(color, percent) {
        const num = parseInt(color.slice(1), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) - amt;
        const G = ((num >> 8) & 0x00FF) - amt;
        const B = (num & 0x0000FF) - amt;

        return "#" + (0x1000000 + Math.max(0, Math.min(255, R)) * 0x10000 + Math.max(0, Math.min(255, G)) * 0x100 + Math.max(0, Math.min(255, B))).toString(16).slice(1);
    }

    #hexToRgba(hex, alpha = 1) {
        // Ensure the hex string is valid and remove the '#' if present
        let validHex = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (!validHex) return null;
    
        // Convert each component from hex to decimal
        let r = parseInt(validHex[1], 16);
        let g = parseInt(validHex[2], 16);
        let b = parseInt(validHex[3], 16);
    
        // Return the RGBA color string
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    /**
     * Auto focus on the first focusable element for the given form ID
     * @param {string} focusId - The form ID to find first focusable element.
     */
    webForm_AutoFocus(focusId) {
        var targetControl;
        if (this.__nonMSDOMBrowser) {
            targetControl = document.getElementById(focusId);
        } else {
            targetControl = document.querySelector(`#${focusId}`);
        }
        var focused = targetControl;
        if (targetControl && (!this.webForm_CanFocus(targetControl))) {
            focused = this.webForm_FindFirstFocusableChild(targetControl);
        }
        if (focused) {
            try {
                focused.focus();
                if (this.__nonMSDOMBrowser) {
                    focused.scrollIntoView(false);
                }
                if (window.__smartNav) {
                    window.__smartNav.ae = focused.id;
                }
            } catch (e) {
            }
        }
    }

    /**
     * Check if passed element is focusable.
     * @param {HTMLElement} [element] - HTML element to check if focusable.
     * @returns {Boolean} true if element is focusable, false otherwise
     */
    webForm_CanFocus(element) {
        if (!element || !(element.tagName)) {
            return false;
        }
        const tagName = element.tagName.toLowerCase();
        return (!(element.disabled) && 
                (!(element.type) || element.type.toLowerCase() != 'hidden') && 
                this.webForm_IsFocusableTag(tagName) && 
                this.webForm_IsInvisibleContainer(element)
                );
    }

    /**
     * Recursively search for the first focusable element
     * @param {HTMLElement} [control] 
     * @returns {HTMLElement}
     */
    webForm_FindFirstFocusableChild(control) {
        if (!control || !(control.tagName)) {
            return null;
        }
        const tagName = control.tagName.toLowerCase();
        if (tagName == 'undefined') {
            return null;
        }
        const children = control.childNodes;
        if (children) {
            for (var i = 0; i < children.length; i++) {
                try {
                    if (this.webForm_CanFocus(children[i])) {
                        return children[i];
                    } else {
                        const focused = this.webForm_FindFirstFocusableChild(children[i]);
                        if (this.webForm_CanFocus(focused)) {
                            return focused;
                        }
                    }
                } catch (e) {
                }
            }
        }
    }

    /**
     * Returns true if tagName is focusable ie. input, textarea, select, button, a
     * @param {string} tagName the element tag name
     * @returns {Boolean}
     */
    webForm_IsFocusableTag(tagName) {
        return (tagName == "input" ||
                tagName == "textarea" ||
                tagName == "select" ||
                tagName == "button" ||
                tagName == "a");
    }

    /**
     * Do not focus on hidden or otherwise purposefully invisible elements.
     * @param {HTMLElement} [ctrl]
     * @returns {Boolean}
     */
    webForm_IsInvisibleContainer(ctrl) {
        const current = ctrl;
        while ((typeof(current) != 'undefined') && (current != null)) {
            if (current.disabled || 
                ( typeof(current.style) != 'undefined' && 
                ( ( typeof(current.style.display) != 'undefined' && 
                    current.style.display == 'none') || 
                    ( typeof(current.style.visibility) != 'undefined' && 
                    current.style.visibility == 'hidden') ) ) ) {
                return false;
            }
            if (typeof(current.parentNode) != 'undefined' && 
                    current.parentNode != null && 
                    current.parentNode != current && 
                    current.parentNode.tagName.toLowerCase() != 'body') {
                current = current.parentNode;
            } else {
                return true;
            }
        }
        return true;
    }

    /**
     * Setup the PELApp.
     * @param {string} [form] - form, if any, to autofocus on page load. 
     */
    async setup(form) {
        this.#applySavedColors();
        this.#addDynamicColors();
        if (form) {
            this.webForm_AutoFocus(form)
        }
        this.#addSocketHandlers();
    }

    /**
     * Get CSRF Token and send token and form data to api. Real time updates provided by socketIO.
     * @param {FormData} formData - the form data
     */
    async processEngagementLetters(formData) {
        const csrf = formData.get('csrf-token');
        formData.delete('csrf-token');
        api.processLetters(formData, csrf);
    }

    /**
     * Format and send settings data and csrf to frontend api
     * @param {NodeListOf<Element>} formElements - Node list of elements with class 'formElement'
     * @param {string} csrf - csrf token
     */
    async saveUserSettings(formElements, csrf) {
        const data = [];

        formElements.forEach((formElement) => {     
            let type = formElement.dataset.configType;
                   
            if (type === 'list') {
                let label = formElement.querySelector('label');
                let input = formElement.querySelector('.list-setting');
                let small = formElement.querySelector('small');
                // handle list type
                let names = Array.from(formElement.querySelectorAll('[name$="_name[]"]')).map(el => el.value);
                let rates = Array.from(formElement.querySelectorAll('[name$="_rate[]"]')).map(el => el.value);

                let listItems = names.map((name, index) => {
                    return {
                        name: name,
                        rate: rates[index]
                    };
                });

                let formattedData = Object.assign({}, {
                    id: input.id,
                    name: label.innerText,
                    config_name: input.dataset.configName,
                    description: small.innerText,
                    type: input.dataset.configType,
                    value: listItems
                });

                data.push(formattedData);
            } else {
                let label = formElement.querySelector('label');
                let input = formElement.querySelector('input');            
                let small = formElement.querySelector('small')

                let formattedData = Object.assign({}, {
                    id: input.id,
                    name: label.innerText,
                    config_name: input.name,
                    description: small.innerText,
                    type: input.type === 'text' ? 'string' : input.type,
                    value: input.value
                });

                data.push(formattedData);
            }
        });
        await api.saveSettings(data, csrf);
    }
}

const app = new PELApp();
export { app };