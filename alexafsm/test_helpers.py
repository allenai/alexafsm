import glob
import hashlib
import pickle
import json

from dateutil import parser


def recordable(record_dir_function):
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

        def wrapper(playback: bool = False, record: bool = False, **kwargs):
            filename = f'{record_dir_function()}/{cache_filename(kwargs)}'
            if playback:
                # pickle should already exist, read from disk
                with open(filename, 'rb') as pickle_file:
                    return pickle.load(pickle_file)
            elif record:
                # pickle doesn't yet exist, cache it
                result = external_resource_function(**kwargs)
                with open(filename, 'wb') as pickle_file:
                    pickle.dump(result, pickle_file)
                return result
            else:
                return external_resource_function(**kwargs)

        return wrapper

    return real_decorator


def get_requests_responses(record_dir: str):
    """
    Return the (json) requests and expected responses from previous recordings.
    These are sorted by requests' timestamps
    """
    requests = get_timesorted_requests(record_dir)
    expected_responses = []
    for request in requests:
        request_id = request['request']['requestId']
        expected_responses.append(get_json_from_file(output_response_file(record_dir, request_id)))
    return zip(requests, expected_responses)


def get_timesorted_requests(record_dir: str):
    """
    Return json requests from recorded directory, stored in *.input files
    """
    requests = [get_json_from_file(input_file)
                for input_file in glob.iglob(f"{record_dir}/*.input")]
    return sorted(requests, key=lambda r: parser.parse(r['request']['timestamp']))


def get_json_from_file(filename: str):
    """
    Get and parse contents of JSON file
    """
    text = '\n'.join(open(filename).readlines())
    return json.loads(text)


def input_request_file(record_dir, request_id):
    return f"{record_dir}/{request_id}.input"


def output_response_file(record_dir, request_id):
    return f"{record_dir}/{request_id}.output"
