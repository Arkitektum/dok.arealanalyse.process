import logging
from os import path
import json
from jsonschema import validate

_LOGGER = logging.getLogger(__name__)

_FILENAME = 'resources/no.geonorge.dokanalyse.analysisinput.v0.1.schema.json'
_DIR_PATH = path.dirname(path.realpath(__file__))
_FILE_PATH = path.abspath(path.join(_DIR_PATH, '../..', _FILENAME))


def request_is_valid(data):
    with open(_FILE_PATH, 'r') as file:
        schema = json.load(file)

    try:
        validate(instance=data, schema=schema)
        return True
    except Exception as error:
        _LOGGER.error(str(error))
        return False
