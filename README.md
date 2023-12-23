# Process Engagement Letters 2.0

This project is a direct successor to my previous engagemnt letter project found here: https://github.com/sbacky/Proc-Engagement-Letters/tree/main.

Create a .env file and set the SECRET_KEY. Use the .env.sample file for an example.

DO NOT STORE IMPORTANT FILES IN 'temp/' DIRECTORY!!

## Available Cache Types

Below are the built in cache types available in Flask Caching. By default, this application supports FileSystemCache. If you want to use any other Cache Type, you must define the configurations in _cache_config.json and then change 'CACHE_TYPE' in _config.json or directly modify the environmental variable to your desired Cache Type.

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

The serveer will send this type of event to communicate with the frontend a csrf token.

```python
{
    'type': 'csrf',
    'detail': {
        'process': process,
        'token': self.csrf._get_csrf_token()
    }
}
```