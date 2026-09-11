"""Tests for package dependencies.

This module tests that:
1. API → alg: API can import from alg.entrypoints
2. API → gateways: API can import from gateways packages
3. alg → gateways: alg package can internally import from gateways
"""

from alg.core.toponyms.pipelines.corroborate_hazard import corroborate
from alg.entrypoints.toponym_dataset import BuildOptions, build_toponym_dataset
from gateways.llm.connections import get_openai_client
from gateways.llm.operations.llm_operations import LLMOperations


def test_alg_import():
    """Test that API can import from alg.entrypoints.

    This verifies the API → alg dependency.
    """
    assert callable(build_toponym_dataset)

    options = BuildOptions(
        use_llm=False,
        use_network_geocoding=False,
        sample_hazard_zones=False,
        include_candidates=False,
        write_files=False,
    )
    assert options.use_llm is False
    assert options.paths.curated_dir.name == "curated"


def test_gateways_import():
    """Test that API can import from gateways packages.

    This verifies the API → gateways dependency.
    """
    assert callable(get_openai_client)
    assert LLMOperations is not None
    assert hasattr(LLMOperations, "generate")
    assert hasattr(LLMOperations, "generate_json")


def test_alg_to_gateways():
    """Test that the alg package can internally import from gateways.

    ``corroborate`` reaches the hazard tile service through gateways.gsi,
    which in turn uses the shared HTTP client in gateways.http.
    """
    assert callable(corroborate)
