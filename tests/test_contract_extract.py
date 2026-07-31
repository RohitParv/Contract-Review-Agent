import pytest

from tools.contract_extract import load_contract_text


def test_load_contract_text_reads_txt_file(sample_lease_text):
    assert "RESIDENTIAL LEASE AGREEMENT" in sample_lease_text


def test_load_contract_text_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_contract_text("/no/such/file.txt")
