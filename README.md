# Engagement Letter System (ELS)

This is a Flask application for an Engagement Letter System. This application processes engagement letters by rolling them over to the next year. I added a front-end to a previous engagement letter project and updated how each engagement letter is processed.

This project is a direct successor to my previous engagemnt letter project found here: https://github.com/sbacky/Proc-Engagement-Letters/tree/main.

Previously, to process Engagement Letters, the user had to run the script on the command line using Powershell. Now, the user can run the FLask Application, open up a web browser (preferably Chrome or Edge), and go to localhost:5000/ to begin processing engagement letters.

DO NOT STORE IMPORTANT FILES IN 'temp/' DIRECTORY!!

## Setup and Usage

Recommended Browser: Chrome or Edge

Selecting files might not work as intended if you do not use Chrome or Edge. This is because the application uses webkitdirectory to take advantage of the browsers ability to easily navigate a users file directory and select files.

Additionally, you should have python 3.10.6+ and git 2.41.0+ installed.

1. Clone this repository.

```console
git clone https://github.com/sbacky/ProcessEngagementLetters.com.git
```

2. Create a .env file and set the SECRET_KEY. Use the provided sample .env file '.env.sample' in the projects root directory for an example. Place your .env file in the same directory as the sample env file.

3. Run 'els.bat'. The batch file will handle creating and activating the virtual environment, installing dependancies from requirements.txt, setting environment variables, pulling latest version from GitHub and launching the application.

## Settings

Settings can be configured on the settings page in the application or by directly modifying the user-config.json file. Each setting has the following properties:

* id: The ID of the setting
* name: The name of the setting
* config_name: The configuration name of the setting
* description: The description of the setting
* type: The type of setting's value
* value: The value of the setting

### Processed Engagement Letters Directory

Set the directory where processed engagement letters will be saved. By default, all processed files are saved to 'temp/complete'.

* type: string
* default: temp/complete

### Cache Type

Set what cache type Flask uses. By default, FileSystemCache is used.

* type: string
* default: FileSystemCache

### Daily Limit

Set the daily rate limit for requests to the Flask backend. By default, this is set to 1000 per day.

* type: number
* default: 1000

### Hourly Limit

Set the hourly rate limit for requests to the Flask backend. By default, this is set to 240 per hour.

* type: number
* default: 240

## Available Cache Types

Below are the built in cache types available in Flask Caching. By default, this application supports FileSystemCache. If you want to use any other Cache Type, you must define the configurations in _cache_config.json and then change 'CACHE_TYPE' in settings.py. Once the configuration has been added, this setting can be changed on the settings page.

* NullCache (default; old name is null)
* SimpleCache (old name is simple)
* FileSystemCache (old name is filesystem)
* RedisCache (redis required; old name is redis)
* RedisSentinelCache (redis required; old name is redissentinel)
* RedisClusterCache (redis required; old name is rediscluster)
* UWSGICache (uwsgi required; old name is uwsgi)
* MemcachedCache (pylibmc or memcache required; old name is memcached or gaememcached)
* SASLMemcachedCache (pylibmc required; old name is saslmemcached)
* SpreadSASLMemcachedCache (pylibmc required; old name is spreadsaslmemcached)

## SocketIO Events

This application uses SocketIO to send real time updates between the server and the frontend. Below are the types of events used and there formats.

* [process-start](#process-start)
* [processing](#processing)
* [progress](#progress)
* [complete](#complete)
* [process-result](#process-result)
* [process-error](#process-error)
* [csrf](#csrf)

### process-start

The server will send this type of event to communicate with the frontend that a process has been started. This event is used to communicate to the frontend to setup for a running process.

```python
{
    'type': 'process-start', 
    'detail': message
}
```

### processing

The server will send this type of event to communicate with the frontend that a process is currently running. This event is used to communicate to the frontend what process is currently running.

```python
{
    'type': 'processing', 
    'detail': {
        "process": process,
        "method": method,
        "message": message
    }
}
```

### progress

The server will send this type of event to communicate with the frontend updates for the currently running process. This event is used to update a progress bar.

```python
{
    'type': 'progress',
    'detail': {
        "process": process,
        "value": value
    }
}
```

### complete

The server will send this type of event to communicate with the frontend that the currently running process has completed. This event is used to initiate post processing clean up.

```python
{
    'type': 'complete',
    'detail': message
}
```

### process-result

The server will send this type of event to communicate with the frontend the current running process' results.

```python
{
    'type': 'process-result',
    'detail': {
        'process': process,
        'status': status,
        'filename': filename
    }
}
```

### process-error

The server will send this type of event to communicate with the frontend any errors that occur during a running process.

```python
{
    'type': 'process-error',
    'detail': {
        "error": error,
        "message": message,
        "process": process,
        "method": method
    }
}
```

### csrf

The server will send this type of event to communicate with the frontend a csrf token.

```python
{
    'type': 'csrf',
    'detail': {
        'process': process,
        'token': self.csrf._get_csrf_token()
    }
}
```

## License

This software is licensed under the GNU GPL version 3. The full details of the license can be found under the LICENSE file.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.