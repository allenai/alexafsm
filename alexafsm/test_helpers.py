import hashlib
import pickle
import json


def recordable(record_dir_function, is_playback, is_record):
    """
    Record results of functions that depend on external resources

    record_dir_function is a function specifying which directory to save results to/read results
    from

    Pass record=True to the function to save results
    Pass playback=True to the function call to load saved results
    """

    def real_decorator(external_resource_function):
        def cache_filename(kwargs):
            kwargs_as_str = str(sorted(kwargs.items())).encode('utf8')
            kwargs_hash = hashlib.md5(kwargs_as_str).hexdigest()
            return f'{external_resource_function.__name__}_{kwargs_hash}.pickle'

        def wrapper(**kwargs):
            filename = f'{record_dir_function()}/{cache_filename(kwargs)}'
            if is_playback():
                # pickle should already exist, read from disk
                with open(filename, 'rb') as pickle_file:
                    return pickle.load(pickle_file)
            elif is_record():
                # pickle doesn't yet exist, cache it
                result = external_resource_function(**kwargs)
                with open(filename, 'wb') as pickle_file:
                    pickle.dump(result, pickle_file)
                return result
            else:
                return external_resource_function(**kwargs)

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
