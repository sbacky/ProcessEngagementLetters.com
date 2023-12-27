# Copyright (C) 2023 - Neil Crum (nhc.crum@outlook.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from queue import Queue
import shutil
import tempfile
from typing import Any

from flask import Flask, Response, make_response, render_template, send_from_directory, redirect, jsonify, request, url_for
from flask_socketio import SocketIO
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename

from backend.utils.load_json import load_json_data
from backend.utils.path_utils import get_full_path, directory_check
from backend.processor import process_engagement_letter


class Server:
    """
    Server class to wrap around flask application. Handles configurations, routes, socketIO events, starting and stopping the server, and logging.
    """
    TEMPLATES_DIR = 'frontend/templates'
    CACHE_CONFIG_PATH = "_cache_config.json"
    USER_CONFIG_PATH = "user-config.json"

    def __init__(self):
        template_dir = get_full_path(self.TEMPLATES_DIR)
        # init flask app
        self.app = Flask(__name__, template_folder=template_dir)
        self.app.config.from_pyfile(get_full_path('settings.py'))
        self.app.secret_key = self.app.config.get('SECRET_KEY')
        # CSRF protection
        self.csrf = CSRFProtect(self.app)
        # SocketIO
        self.socketio = SocketIO(self.app)
        self.messages = Queue()

        # Setup caching
        cache_type = self.app.config.get('CACHE_TYPE', "FileSystemCache")
        self.cache = self._config_cache(cache_type)
        self.cache.init_app(self.app)

        # Setup rate-limiting
        self.limiter = self._config_limiter()

        # add flask and socketio routes
        self.add_routes()
        self.socketio_events()

        # initiate background tasks
        self.socketio.start_background_task(self.publish)

    def _load_user_config(self):
        """
        Load settings from user-config.json file.
        """
        try:
            # Load user settings
            user_config_path = get_full_path('user-config.json')
            settings = load_json_data(user_config_path)
            # Apply user settings
            for setting in settings:
                new_value = setting['value']
                self.app.config[setting['config_name']] = int(new_value) if setting['type'] == 'number' else new_value
        except Exception as e:
            print('Error loading user settings:', e)

    def _config_cache(self, cache_type: str="FileSystemCache") -> Cache:
        """
        Configure cache for Flask-Caching.

        :param cache_type: [Optional] pass cache type. Default is 'FileSystemCache'. See documentation for acceptable Cache Types.
        """
        cache_path = get_full_path(self.CACHE_CONFIG_PATH)
        config_data = load_json_data(cache_path)
        cache_config: dict[str, Any] = config_data.get(cache_type, {})

        cache_dir = get_full_path(cache_config.get('CACHE_DIR', '_cache'))
        if directory_check(cache_dir, True):
            cache_config.update({'CACHE_DIR': cache_dir})

        return Cache(app=self.app, config=cache_config)
    
    def _config_limiter(self) -> Limiter:
        """
        Configure rate limiting for Flask using flask-limiter.

        Daily and hourly limits configured in environment variables: DAILY_LIMIT, HOURLY_LIMIT
        """
        daily_limit = self.app.config.get('DAILY_LIMIT', 1000)
        hourly_limit = self.app.config.get('HOURLY_LIMIT', 240)

        return Limiter(
            key_func=get_remote_address,
            app=self.app,
            default_limits=[f'{daily_limit} per day', f'{hourly_limit} per hour']
        )

    def format_message(self, type: str, message: str|int|float|dict[str, Any]):
        """
        Format SocketIO message.
        """
        msg = {}
        msg['type'] = type
        msg['detail'] = message
        return msg
    
    def send_message(self, type: str, message: str|int|float|dict[str, Any]):
        """
        Send SocketIO message event to frontend.
        
        :param type: event type
        :param message: event message
        """
        msg = self.format_message(type, message)
        self.sync('message', msg)

    # Async producer
    def sync(self, event, data):
        self.messages.put((event, data))
    
    # Async consumer
    def publish(self):
        while True:
            try:
                message = self.messages.get()
                event, data = message
                self.socketio.emit(event, data)
            except Exception as e:
                self.app.logger.exception(f'Error in publish: {e}', stack_info=True)

    def add_routes(self):
        """
        Available routes and methods for Flask App.

        [GET] /styles.css
            - GET: Return stylesheet

        [GET] /scripts/<path/to/script.js>
            - GET: Return scripts from script directory

        [POST] /shutdown
            - POST: Process shutdown request

        [CSRFError] /CSRFError
            - CSRFError: Handle CSRF Errors for invalid CSRFs

        [Exception] /Exception
            - Exception: Handle uncaught exceptions.

        [GET] /
            - GET: Return home page with form to get required info to process engagement letters.

        [GET, POST] /settings
            - GET: Return settings page with form to update user specific settings.
            - POST: Process settings request to update settings in Flask and save user settings to user-config.json.

        [POST] /engagementLetters/document-rollover
            - POST: Process engagement letters using form fields as configurations
        """
        @self.app.route('/styles.css')
        def styles():
            response = make_response(send_from_directory('../frontend', 'styles.css'))
            response.headers['Cache-Control'] = 'public, max-age=300'
            return response
        
        @self.app.route('/scripts/<path:path>')
        def scripts(path):
            response = make_response(send_from_directory('../frontend/scripts', path))
            response.headers['Cache-Control'] = 'public, max-age=300'
            return response
        
        @self.app.route('/shutdown', methods=['POST'])
        def shutdown():
            # Add authentication or other security checks here
            self.shutdown_server()
            return 'Server shutting down...', 200
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            self.app.logger.exception(f'Unhandled Exception: {e}', stack_info=True)
            return jsonify(error=str(e)), 500
        
        @self.app.errorhandler(CSRFError)
        def handle_csrf_error(e):
            self.send_message("process-error", {
                "error": "CSRF Error",
                "message": "CSRF token missing or incorrect",
                "process": "formProcessing",
                "method": "POST"
            })
            self.app.logger.exception(f"CSRF token missing or incorrect: {e}", stack_info=True)

        @self.app.route("/", methods=["GET"])
        @self.cache.cached(timeout=300)
        def index():
            process = 'processEngagementLetters'
            # Send start-process event
            self.send_message("process-start", "Fetching home page...")
            if request.method == 'GET':
                method = 'GET'
                # Send processing event for GET method
                self.send_message('processing', {
                    "process": process,
                    "method": method,
                    "message": "Loading..."
                })
                # Send complete event
                self.send_message('complete', "Page loaded successfully!")
                return render_template('index.html')
            
        @self.app.route('/settings', methods=['GET', 'POST'])
        def settings():
            process = 'userSettings'
            self.send_message('process-start', 'Fetching user settings...')
            if request.method == 'GET':
                method = 'GET'
                # Send processing event to load settings
                self.send_message('processing', {
                    "process": process,
                    "method": method,
                    "message": "Loading..."
                })
                # Load existing settings
                try:
                    user_config_path = get_full_path(self.USER_CONFIG_PATH)
                    with open(user_config_path, 'r') as config_file:
                        settings = json.load(config_file)
                except (FileNotFoundError, json.JSONDecodeError):
                    self.send_message('process-error', {
                        "error": "Settings Error",
                        "message": "An error occurred while loading user settings",
                        "process": process,
                        "method": method
                    })
                    settings = {}
                # Send complete event
                self.send_message('complete', "User settings loaded successfully!")

                return render_template('settings.html', settings=settings)
            elif request.method == 'POST':
                method = 'POST'
                # Send processing event to save settings
                self.send_message('processing', {
                    "process": process,
                    "method": method,
                    "message": "Saving settings to user-config.json..."
                })
                # TODO: Implement logic to save new settings
                try:
                    # Get form data
                    form_data: list[dict[str, str|int]] = request.get_json()
                    # Load existing settings
                    user_config_path = get_full_path(self.USER_CONFIG_PATH)
                    settings: list[dict[str, str|int]] = load_json_data(user_config_path)
                    # Update settings with new values from the form
                    for setting in settings:
                        for form_setting in form_data:
                            if setting.get('config_name') == form_setting.get('config_name'):
                                new_value = form_setting.get('value')
                                setting['value'] = int(new_value) if form_setting.get('type') == 'number' else new_value

                    # Save updated settings
                    with open(user_config_path, 'w') as config_file:
                        json.dumps(settings, config_file, indent=4)

                    # Update app.config here if needed
                    for setting in settings:
                        self.app.config[setting['config_name']] = setting['value']

                    return jsonify({'status': 'success', 'redirect': '/settings'}), 200
                except Exception as e:
                    self.send_message('process-error', {
                        "error": "Settings Error",
                        "message": f"An error occurred while saving user settings: {e}",
                        "process": process,
                        "method": method
                    })
                    return jsonify({'status': 'error', 'message': f"An error occurred while saving user settings: {e}"}), 500

        @self.app.route('/engagementLetters/document-rollover', methods=['POST'])
        def process_engagement_letters():
            """
            form: path to directory containing engagement letters
            environment-variable: path to directory to move updated engagement letters to
            function: verify path exists and is a directory
            """
            process = 'processEngagementLetters'
            # Send start-process event
            self.send_message("process-start", "Processing engagement letters!")
            if request.method == 'POST':
                method = 'POST'
                
                current_year_files = request.files.getlist('currentYearDirectory')
                processed_files_directory = self.app.config.get('PROCESSED_FILES_DIRECTORY', get_full_path('temp/complete'))
                if not directory_check(processed_files_directory):
                    self.send_message('process-error', {
                        "error": "Letter Processing Error",
                        "message": f'The specified directory ( {processed_files_directory} ) does not exist. Configure in settings or in config file.',
                        "process": process,
                        "method": method
                    })
                    return jsonify(error=f'The specified directory ( {processed_files_directory} ) does not exist. Configure in settings or in config file.'), 400
                
                # Send processing event for POST method
                self.send_message('processing', {
                    "process": process,
                    "method": method,
                    "message": f'Processing...'
                })
                
                temp_dir = get_full_path('temp/processing')
                directory_check(temp_dir, True)

                try:
                    # TODO: Send progress event updates for number of files processed out o total files.
                    total_files = len(current_year_files)
                    for index, file in enumerate(current_year_files, 1):
                        filename: str = secure_filename(os.path.basename(file.filename))
                        # Move to next file if it is not a word document file ending in '.docx'.
                        if filename.startswith('~') or not filename.endswith('.docx'):
                            continue
                        
                        # Save temp file to 'temp/processing'
                        temp_file_path = os.path.join(temp_dir, filename)
                        file.save(temp_file_path)

                        processed_result, error = process_engagement_letter(temp_file_path, processed_files_directory)
                        # Log errors
                        if (error is not None):
                            # Send process-error event
                            self.send_message('process-error', {
                                "error": "Letter Processing Error",
                                "message": error,
                                "process": process,
                                "method": method
                            })
                            self.app.logger.error(error)
                        # Send results event to frontend
                        self.send_message('process-results',{
                            "process": process,
                            "status": "success" if processed_result is not None else "failed",
                            "filename": filename
                        })
                        # Send progress event to frontend
                        self.send_message('progress', {
                            'process': process,
                            'value': index/total_files
                        })

                    self.send_message('complete', 'Successfully processed engagement letters!')
                    return jsonify({'status': 'success', 'message': 'Successfully processed engagement letters!'})
                except Exception as e:
                    # Send process-error event
                    self.send_message('process-error', {
                        "error": "Letter Processing Error",
                        "message": f'An unexpected error has occurred while processing {filename}',
                        "process": process,
                        "method": method
                    })
                    self.app.logger.exception(f'An unexpected error has occurred while processing {filename}', stack_info=True)
                    return jsonify({'status': 'error', 'message': f'An unexpected error has occurred while processing {filename}'}), 500
                finally:
                    # Clear 'temp/processing' directory
                    shutil.rmtree(temp_dir)

    def socketio_events(self):
        """
        Define socketio events.
        """
        # Server connection events
        @self.socketio.on('connect')
        def connect_socketio():
            self.app.logger.info("Server connection established!")

        # Server disconnection events
        @self.socketio.on('disconnect')
        def disconnect_socketio():
            self.app.logger.info("Server disconnected!")

        # Frontend log events
        @self.socketio.on('log')
        def frontend_log(data: dict[str, str]):
            level = data.get('level')
            message = data.get('message')
            self.app.logger.log(getattr(logging, level.upper()), message)

    def run(self, host, port, debug=True):
        """
        Start the server.

        :param host: Pass a hostname or IP address
        :param port: Pass a port number for server to listen on
        :param debug: [Optional] debug flag. Default is True.
        """
        self.setup_logging(debug)
        self.app.run(host=host, port=port, debug=debug)

    def shutdown_server(self):
        """
        Shut down the server gracefully.
        """
        self.socketio.stop()  # Stop SocketIO if necessary
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        print("Server shutting down...")

    def setup_logging(self, debug: bool):
        """
        Setup logging for flask app.

        :param debug: Set log level as debug or not.
        """
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        
        # Create logging directory if it doesn't exist
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        log_dir = os.path.join(project_root.resolve(), 'logs')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        
        log_file = os.path.join(log_dir, "app.log")
        
        # Create a file handler
        handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=3, delay=True)
        
        # Create a logging format
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        self.app.logger.addHandler(handler)
        
        if debug:
            self.app.logger.setLevel(logging.DEBUG)
        else:
            self.app.logger.setLevel(logging.INFO)