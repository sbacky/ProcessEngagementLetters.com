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
import { io } from "https://cdn.socket.io/4.4.1/socket.io.esm.min.js";

/**
 * API class to connect to flask backend
 */
class PELApi {
    static #instance;
    #registered = new Set();

    constructor() {
        if (PELApi.#instance) {
            return PELApi.#instance;
        }
        PELApi.#instance = this;

        this.socket = null;

        this.host = location.host;
        this.base = `${location.protocol}//${location.hostname}${location.port ? ':' + location.port : ''}${location.pathname.split('/').slice(0, -1).join('/')}`;
    }

    /**
     * Return full API URL with endpoint
     * @param {string} endpoint 
     * @returns {string} base url + endpoint
     */
    apiURL(endpoint) {
        return this.base + endpoint;
    }

    /**
     * Add custom event listeners for event type, with callback function and options.
     * @param {string} type event type to listen for
     * @param {EventListenerOrEventListenerObject} callback function to call
     * @param {boolean | AddEventListenerOptions} [options] optional options
     */
    addCustomEventListener(type, callback, options) {
        document.addEventListener(type, callback, options);
        this.#registered.add(type)
    }

    /**
     * Connect to socket io server and listen for events
     */
    connectSocket() {
        if (this.socket) {
            return;
        }
        const protocol = window.location.protocol === "https:" ? "https" : "http";
        const url = `${protocol}://${this.host}`;

        console.log("Protocol:", protocol);
        console.log("URL:", url);

        this.socket = io.connect(url);

        this.socket.on('connect', () => {
            // Connection and reconnection
            console.log("Connected:", this.socket.connected);
            this.logToServer('info', 'Client successfully connected to server.');
            this.dispatchCustomEvent(new CustomEvent('connected', { detail: "Connection successful!" }));
        });

        this.socket.on('disconnect', (reason) => {
            if (reason === "io server disconnect") {
                // Manualy reconnect if server initiated disconnection
                this.socket = null;
                this.connectSocket();
                this.logToServer('info', 'Server initiated disconnection, attempting to manually reconnect to server.');
            } else {
                // Socket automatically tries to reconnect for every other reason
                this.logToServer('info', 'Disconnected, automatically attempting to reconnect to server.');
            }
            
            this.dispatchCustomEvent(new CustomEvent('disconnected', { detail: "Attempting to reconnect..." }));
        });

        this.socket.on('error', (error) => {
            // Namespace middleware error
            if (this.socket) {
                this.socket.close();
            }
            this.logToServer('error', `An error occurred: ${error}`);
        });

        // Listen for message socketio events
        this.socket.on('message', (msg) => {
            switch (msg.type) {
                case 'processing':
                    this.dispatchCustomEvent(new CustomEvent('processing', { detail: msg.detail }));
                    break;
                case 'process_start':
                    this.dispatchCustomEvent(new CustomEvent('process_start', { detail: msg.detail }));
                    break;
                case 'process_error':
                    // detail: {error: 'error_name', message: 'error_message', process: 'process_name_error', fieldname: 'form_fieldname' optional}
                    this.dispatchCustomEvent(new CustomEvent('process_error', { detail: msg.detail }));
                    break;
                case 'complete':
                    this.dispatchCustomEvent(new CustomEvent('complete', { detail: msg.detail }));
                    break;
                case 'progress':
                    this.dispatchCustomEvent(new CustomEvent('progress', { detail: msg.detail }));
                    break;
                default:
                    if (this.#registered.has(msg.type)) {
                        this.dispatchCustomEvent(new CustomEvent(msg.type, { detail: msg.detail }));
                    } else {
                        this.logToServer('error', `Unknown message type ${msg.type}`);
                        throw new Error(`Unknown message type ${msg.type}`)
                    }
                    break;
            }
        });
    }

    /**
     * Dispatch a new custom eevent
     * @param {CustomEvent} customEvent 
     */
    dispatchCustomEvent(customEvent) {
        // Check if customEvent is an instance of CustomEvent
        if (!(customEvent instanceof CustomEvent)) {
            this.logToServer('error', 'The provided argument is not a CustomEvent.')
            console.error("The provided argument is not a CustomEvent.");
            return;
        }
    
        // Dispatch the event on the document or any specific element as needed
        document.dispatchEvent(customEvent);
    }

    /**
     * Send log message with level to backend for logging.
     * @param {string} level log level
     * @param {string} message log message
     */
    logToServer(level, message) {
        if (this.socket) {
            this.sendToServer('log', {level, message});
        } else {
            console.warn("Socket not connected. Unable to log message to server.");
        }
    }

    /**
     * Send message to event handler in backend
     * @param {string} event event name
     * @param {Object} message message object
     */
    sendToServer(event, message) {
        if (this.socket) {
            this.socket.emit(event, message);
        } else {
            console.warn("Socket not connected. Unable to log message to server.");
        }
    }

    /**
     * Send uploaded files to backend to process engagement letters
     * @param {FormData} formData - Form data for processEngagementLetters form
     * @param {string} csrf - the CSRF token
     */
    async processLetters(formData, csrf) {
        const endpoint = '/engagementLetters/document-rollover';
        const url = this.apiURL(endpoint);
        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrf
                },
                body: formData
            });
            const respData = await resp.json();
            if (respData.status == 'success') {
                console.log(respData.message);
            } else if (respData.status == 'error') {
                console.error(respData.message);
            } else {
                console.error(`Unknown error: ${JSON.stringify(respData)}`);
            }
        } catch (error) {
            this.logToServer('error', `An error occurred while saving settings: ${error}`);
            console.error(`An error occurred while saving settings: ${error}`);
        }
    }

    /**
     * @typedef Setting
     * @type {object}
     * @property {string} id
     * @property {string} name
     * @property {string} config_name
     * @property {string} descritption
     * @property {string} type
     * @property {(string|number)} value
     */

    /**
     * Send user setting info to backend to update and save settings.
     * @param {Setting[]} formData - settings form data
     * @param {string} csrf - csrf token
     */
    async saveSettings(formData, csrf) {
        const endpoint = '/settings';
        const url = this.apiURL(endpoint);
        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrf,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            const respData = await resp.json();
            if (respData.status == 'success') {
                window.location.href = respData.redirect;
            } else if (respData.status == 'error') {
                console.error(respData.message);
            }
        } catch (error) {
            this.logToServer('error', `An error occurred while saving settings: ${error}`);
            console.error(`An error occurred while saving settings: ${error}`);
        }
    }

    /**
     * Send uploaded files to backend to extract entity information
     * @param {FormData} formData - Form data for entityChecker form
     * @param {string} csrf - the CSRF token
     */
    async checkEntities(formData, csrf) {
        const endpoint = '/entityChecker/check-entities';
        const url = this.apiURL(endpoint);
        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrf
                },
                body: formData
            });
            const respText = await resp.text();
            return respText.trim();
        } catch (error) {
            this.logToServer('error', `An error occurred while checking entities: ${error}`);
            console.error(`An error occurred while checking entities: ${error}`);
        }
    }

    /**
     * Send uploaded files to backend to be printed to pdf
     * @param {FormData} formData - Form data for pdfPrinter form
     * @param {string} csrf - the csrf token
     * @returns 
     */
    async printToPdf(formData, csrf) {
        const endpoint = '/pdfPrinter/print-to-pdf';
        const url = this.apiURL(endpoint);
        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrf
                },
                body: formData
            });
            const respData = await resp.json();
            return respData;
        } catch (error) {
            this.logToServer('error', `An error occurred while printing documents to pdf: ${error}`);
            console.error(`An error occurred while printing documents to pdf: ${error}`);
        }
    }

    /**
     * Send uploaded df files to have signatures added to them
     * @param {FormData} formData - the form data for pdfSignatures form data
     * @param {string} csrf - the csrf token
     * @returns response object
     */
    async addSignature(formData, csrf) {
        const endpoint = '/pdfSignatures/add-signatures';
        const url = this.apiURL(endpoint);
        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrf
                },
                body: formData
            });
            const respData = await resp.json();
            return respData;
        } catch (error) {
            this.logToServer('error', `An error occurred while printing documents to pdf: ${error}`);
            console.error(`An error occurred while printing documents to pdf: ${error}`);
        }
    }
}

const api = new PELApi();
export { api };