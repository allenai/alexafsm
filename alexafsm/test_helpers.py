import hashlib
import pickle
import json
import inspect


def recordable(record_dir_function, is_playback, is_record):
    """
    Record results of functions that depend on external resources

    record_dir_function is a function specifying which directory to save results to/read results
    from

    Pass record=True to the function to save results
    Pass playback=True to the function call to load saved results
    """

    def real_decorator(external_resource_function):
        def cache_filename(args, kwargs):
            args_as_str = str(args).encode('utf8')
            kwargs_as_str = str(sorted(kwargs.items())).encode('utf8')
            hashed_args = hashlib.md5(f"{args_as_str}{kwargs_as_str}").hexdigest()
            return f'{external_resource_function.__name__}_{hashed_args}.pickle'

        def wrapper(*args, **kwargs):
            # handle default kwargs where some kwarg may or may not be set with default values
            fullargspec = inspect.getfullargspec(external_resource_function)
            arguments, defaults = fullargspec.args, fullargspec.defaults
            default_kwargs = {k: v for k, v in zip(arguments[-len(defaults):], defaults)}

            full_kwargs = {**default_kwargs, **kwargs}
            filename = f'{record_dir_function()}/{cache_filename(args, full_kwargs)}'
            if is_playback():
                # pickle should already exist, read from disk
                with open(filename, 'rb') as pickle_file:
                    return pickle.load(pickle_file)
            elif is_record():
                # pickle doesn't yet exist, cache it
                result = external_resource_function(*args, **kwargs)
                with open(filename, 'wb') as pickle_file:
                    pickle.dump(result, pickle_file)
                return result
            else:
                return external_resource_function(*args, **kwargs)

        return wrapper

    return real_decorator


def get_requests_responses(record_file: str):
    """
    Return the (json) requests and expected responses from previous recordings.
    These are returned in the same order they were recorded in.
    """
    with open(record_file) as f:
        lines = f.readlines()
    return [tuple(json.loads(line)) for line in lines]
