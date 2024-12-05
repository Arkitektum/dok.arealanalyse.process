import logging
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from uuid import UUID
from pydantic import ValidationError
from cachetools import cached, TTLCache
from ..models.exceptions import DokAnalysisException
from ..models.config.dataset_config import DatasetConfig
from ..models.config.quality_config import QualityConfig
from ..models.config.quality_indicator import QualityIndicator
from ..utils.helpers.common import get_env_var

_LOGGER = logging.getLogger(__name__)


def get_dataset_configs() -> List[DatasetConfig]:
    dataset_configs, _ = _load_config()

    return dataset_configs


def get_dataset_config(dataset_id: UUID) -> DatasetConfig:
    dataset_configs, _ = _load_config()

    config = next(
        (conf for conf in dataset_configs if conf.dataset_id == dataset_id), None)

    return config


def get_quality_indicator_configs(dataset_id: UUID) -> List[QualityIndicator]:
    _, quality_configs = _load_config()
    indicators: List[QualityIndicator] = []

    for config in quality_configs:
        id: UUID = config.dataset_id

        if not id or id == dataset_id:
            indicators.extend(config.indicators)

    return indicators


@cached(cache=TTLCache(maxsize=1024, ttl=300))
def _load_config() -> Tuple[List[DatasetConfig], List[QualityConfig]]:
    config_dir = get_env_var('DOKANALYSE_CONFIG_DIR')

    if config_dir is None:
        raise DokAnalysisException(
            'The environment variable "DOKANALYSE_CONFIG_DIR" is not set')

    path = Path(config_dir)

    if not path.is_dir():
        raise DokAnalysisException(
            f'The "DOKANALYSE_CONFIG_DIR" path ({path}) is not a directory')

    glob = path.glob('*.yml')
    files = [path for path in glob if path.is_file()]

    if len(files) == 0:
        raise DokAnalysisException(
            f'The "DOKANALYSE_CONFIG_DIR" path ({path}) contains no YAML files')

    return _create_configs(files)


def _create_configs(files: List[Path]) -> Tuple[List[DatasetConfig], List[QualityConfig]]:
    dataset_configs: List[DatasetConfig] = []
    quality_configs: List[QualityConfig] = []

    for file_path in files:
        with open(file_path, 'r') as file:
            results = yaml.safe_load_all(file)
            result: dict

            for result in results:
                type = result.get('type')

                if type == 'dataset':
                    config = _create_dataset_config(result)

                    if config is not None:
                        dataset_configs.append(config)
                elif type == 'quality':
                    config = _create_quality_config(result)

                    if config is not None:
                        quality_configs.append(config)

    if len(dataset_configs) == 0:
        raise DokAnalysisException(
            f'Could not create any dataset configurations from the files in "DOKANALYSE_CONFIG_DIR"')

    return dataset_configs, quality_configs


def _create_dataset_config(data: Dict) -> DatasetConfig:
    try:
        return DatasetConfig(**data)
    except ValidationError as error:
        _LOGGER.error(error)
        return None


def _create_quality_config(data: Dict) -> QualityConfig:
    try:
        return QualityConfig(**data)
    except ValidationError as error:
        _LOGGER.error(error)
        return None


__all__ = [
    'get_dataset_configs',
    'get_dataset_config',
    'get_quality_indicator_configs'
]
