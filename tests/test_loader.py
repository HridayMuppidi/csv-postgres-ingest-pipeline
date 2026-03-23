import pytest
import os
import sys
from unittest.mock import MagicMock, patch, call
import psycopg2
#adds the src file path to system path to access the files to be tested
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import loader

#  FIXTURES 
 
@pytest.fixture
def sample_row():
    """A complete valid row matching CSV structure."""
    return {
        "Primary Number": "02-000570",
        "OTIS ID": "684249",
        "Property Number": "129121",
        "Name": "Test Property",
        "Aliases and Alias Types": "",
        "St Number": "550",
        "St Name": "Test Street",
        "City": "Test City",
        "County": "Alpine",
        "Zip": "95223",
        "Vicinity": "",
        "Other Geography": "",
        "Evaluation Info": "6Y, 05/15/2018, USFS_2018_0417_001",
        "District Elements": "",
        "Parent District": "",
        "Assoc Resources": "",
        "Parcel Num": "005-470-026-000",
        "MilePost": "",
        "Ownership": "",
        "Construction Year(s)": "1959",
        "oCode": "o37120e1",
        "Date Modified": "07/02/2019",
        "Export Date": "9/23/2022"
    }
 
 
@pytest.fixture
def mock_conn():
    """A mock database connection object."""
    return MagicMock()
 
 
# READ FILE TESTS 
 
def test_read_file_valid_csv():
    """Test that a valid CSV file returns a list of rows."""
    rows = loader.read_file("tests/sample.csv")
    assert isinstance(rows, list)
    assert len(rows) > 0
 
 
def test_read_file_returns_list_of_dicts():
    """Test that each row is a dictionary with expected keys."""
    rows = loader.read_file("tests/sample.csv")
    assert isinstance(rows[0], dict)
    assert "OTIS ID" in rows[0]
    assert "Name" in rows[0]
 
 
def test_read_file_not_found():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        loader.read_file("nonexistent_file.csv")
 
 
def test_read_file_empty_csv(tmp_path):
    """Test that an empty CSV returns an empty list."""
    # Create a temporary empty CSV with just headers
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("Primary Number,OTIS ID,Property Number,Name,Aliases and Alias Types,St Number,St Name,City,County,Zip,Vicinity,Other Geography,Evaluation Info,District Elements,Parent District,Assoc Resources,Parcel Num,MilePost,Ownership,Construction Year(s),oCode,Date Modified,Export Date\n")
    
    rows = loader.read_file(str(empty_csv))
    assert rows == []
 
 
# RECORD EXISTS TESTS
 
def test_record_exists_returns_true(mock_conn):
    """Test that record_exists returns True when record is found."""
    # Tell the mock cursor to return a row (record exists)
    mock_conn.cursor().fetchone.return_value = (1,)
    
    result = loader.record_exists(mock_conn, "684249")
    assert result == True
 
 
def test_record_exists_returns_false(mock_conn):
    """Test that record_exists returns False when record is not found."""
    # Tell the mock cursor to return None (record doesn't exist)
    mock_conn.cursor().fetchone.return_value = None
    
    result = loader.record_exists(mock_conn, "999999")
    assert result == False
 
 
# INSERT RECORD TESTS
 
def test_insert_record_success(mock_conn, sample_row):
    """Test that insert_record executes without errors for a valid row."""
    loader.insert_record(mock_conn, sample_row)
    
    # Verify commit was called — meaning insert was successful
    mock_conn.commit.assert_called_once()
 
 
def test_insert_record_rollback_on_error(mock_conn, sample_row):
    """Test that rollback is called when insert fails."""
    # Make execute raise an exception
    mock_conn.cursor().execute.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception):
        loader.insert_record(mock_conn, sample_row)
    
    # Verify rollback was called
    mock_conn.rollback.assert_called_once()
 
 
def test_insert_record_string_truncation(mock_conn, sample_row):
    """Test that StringDataRightTruncation gives a clear error message."""
    # Make execute raise a StringDataRightTruncation error
    mock_conn.cursor().execute.side_effect = psycopg2.errors.StringDataRightTruncation("value too long")
    
    with pytest.raises(psycopg2.errors.StringDataRightTruncation):
        loader.insert_record(mock_conn, sample_row)
    
    mock_conn.rollback.assert_called_once()
 
 
# ===== UPDATE RECORD TESTS =====
 
def test_update_record_success(mock_conn, sample_row):
    """Test that update_record executes without errors for a valid row."""
    loader.update_record(mock_conn, sample_row)
    
    # Verify commit was called — meaning update was successful
    mock_conn.commit.assert_called_once()
 
 
def test_update_record_rollback_on_error(mock_conn, sample_row):
    """Test that rollback is called when update fails."""
    mock_conn.cursor().execute.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception):
        loader.update_record(mock_conn, sample_row)
    
    mock_conn.rollback.assert_called_once()
 
 
# UPSERT ROW TESTS 
 
def test_upsert_row_inserts_when_record_does_not_exist(mock_conn, sample_row):
    """Test that upsert_row calls insert when record doesn't exist."""
    # Mock record_exists to return False
    with patch('loader.record_exists', return_value=False) as mock_exists:
        with patch('loader.insert_record') as mock_insert:
            result = loader.upsert_row(mock_conn, sample_row)
            
            mock_insert.assert_called_once_with(mock_conn, sample_row)
            assert result == False  # False means it was inserted
 
 
def test_upsert_row_updates_when_record_exists(mock_conn, sample_row):
    """Test that upsert_row calls update when record exists."""
    # Mock record_exists to return True
    with patch('loader.record_exists', return_value=True) as mock_exists:
        with patch('loader.update_record') as mock_update:
            result = loader.upsert_row(mock_conn, sample_row)
            
            mock_update.assert_called_once_with(mock_conn, sample_row)
            assert result == True  # True means it was updated
 
 
def test_upsert_row_duplicate_row(mock_conn, sample_row):
    """Test that duplicate rows are handled by updating not inserting."""
    with patch('loader.record_exists', return_value=True):
        with patch('loader.update_record') as mock_update:
            # Call upsert twice with same row
            loader.upsert_row(mock_conn, sample_row)
            loader.upsert_row(mock_conn, sample_row)
            
            # Update should be called twice, not insert
            assert mock_update.call_count == 2
 
 
def test_upsert_row_missing_otis_id(mock_conn):
    """Test that a row with missing OTIS ID raises a KeyError."""
    malformed_row = {
        "Primary Number": "",
        "OTIS ID": "",  # blank otis_id
        "Name": "Test"
    }
    
    with patch('loader.record_exists', side_effect=KeyError("OTIS ID")):
        with pytest.raises(KeyError):
            loader.upsert_row(mock_conn, malformed_row)
 