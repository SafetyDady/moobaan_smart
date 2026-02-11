"""
CSV Parser Service for Bank Statement Import
Supports auto-detection of header row and normalization of bank CSV formats
"""
import csv
import hashlib
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from io import StringIO


class CSVParserDiagnostics:
    """Container for parser diagnostics"""
    def __init__(self):
        self.total_rows = 0
        self.detected_delimiter = ','
        self.header_row_index = None
        self.detected_columns = []
        self.expected_columns = ['date', 'description', 'debit/credit', 'balance']
        self.parsed_rows = 0
        self.skipped_rows = 0
        self.skip_reasons = {}  # reason -> count
        self.csv_date_range = {'start': None, 'end': None}
        
    def add_skip_reason(self, reason: str):
        """Track why a row was skipped"""
        self.skip_reasons[reason] = self.skip_reasons.get(reason, 0) + 1
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        # Convert datetime objects to ISO format for JSON serialization
        csv_date_range = {
            'start': self.csv_date_range['start'].isoformat() if self.csv_date_range['start'] and hasattr(self.csv_date_range['start'], 'isoformat') else self.csv_date_range['start'],
            'end': self.csv_date_range['end'].isoformat() if self.csv_date_range['end'] and hasattr(self.csv_date_range['end'], 'isoformat') else self.csv_date_range['end'],
        }
        
        return {
            'total_rows': self.total_rows,
            'detected_delimiter': self.detected_delimiter,
            'header_row_index': self.header_row_index,
            'detected_columns': self.detected_columns,
            'expected_columns': self.expected_columns,
            'parsed_rows': self.parsed_rows,
            'skipped_rows': self.skipped_rows,
            'skip_reasons': self.skip_reasons,
            'csv_date_range': csv_date_range,
        }


class CSVParserService:
    """Service for parsing bank statement CSV files"""
    
    # Common column names in Thai and English (expanded)
    DATE_COLUMNS = ['วันที่', 'date', 'transaction date', 'วัน ที่', 'txn date', 'trans date']
    TIME_COLUMNS = ['เวลา', 'time', 'transaction time', 'txn time', 'time/ eff.date', 'time/eff.date']
    DATETIME_COLUMNS = ['เวลา/ วันที่มีผล', 'เวลา/วันที่มีผล', 'วันที่และเวลา', 'datetime', 'transaction datetime', 'effective date time', 'effective datetime']
    DESCRIPTION_COLUMNS = ['รายการ', 'description', 'descriptions', 'รายการธุรกรรม', 'desc', 'particular', 'details', 'รายละเอียด']
    DEBIT_COLUMNS = ['ถอนเงิน', 'debit', 'withdraw', 'withdrawal', 'ถอน', 'จ่าย', 'dr', 'ออก']
    CREDIT_COLUMNS = ['ฝากเงิน', 'credit', 'deposit', 'รับ', 'ฝาก', 'cr', 'เข้า']
    BALANCE_COLUMNS = ['ยอดคงเหลือ', 'balance', 'outstanding balance', 'remaining', 'คงเหลือ', 'bal', 'amount']
    CHANNEL_COLUMNS = ['ช่องทาง', 'channel', 'type', 'ชนิด', 'txn type']
    
    @staticmethod
    def detect_delimiter(file_content: str) -> str:
        """Detect CSV delimiter (comma or semicolon)"""
        # Try first few non-empty lines
        lines = [line for line in file_content.split('\n')[:10] if line.strip()]
        
        comma_count = sum(line.count(',') for line in lines)
        semicolon_count = sum(line.count(';') for line in lines)
        
        # Return delimiter with more occurrences
        return ';' if semicolon_count > comma_count else ','
    
    @staticmethod
    def normalize_column_name(column: str) -> str:
        """Normalize column name by replacing newlines with spaces, collapsing whitespace, and converting to lowercase"""
        # Replace newlines/tabs with spaces, then collapse multiple spaces
        normalized = column.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        normalized = ' '.join(normalized.split())  # collapse whitespace
        return normalized.strip().lower()
    
    @classmethod
    def detect_header_row(cls, rows: List[List[str]]) -> Tuple[int, Dict[str, int]]:
        """
        Detect which row contains the table header
        Returns: (header_row_index, column_mapping)
        """
        for idx, row in enumerate(rows):
            # Normalize all columns in this row
            normalized_cols = [cls.normalize_column_name(col) for col in row]
            
            # Check if this row contains the required columns
            # Use scoring system to select best datetime column
            date_col_scores = {}
            datetime_col = None
            time_col = None
            desc_col = None
            debit_col = None
            credit_col = None
            balance_col = None
            channel_col = None
            
            for col_idx, col_name in enumerate(normalized_cols):
                # Check datetime columns (these could be time-only columns like "เวลา/ วันที่มีผล")
                if any(cls.normalize_column_name(dc) == col_name for dc in cls.DATETIME_COLUMNS):
                    # If this looks like a time column, treat it as time instead
                    if 'เวลา' in col_name:
                        time_col = col_idx
                    else:
                        datetime_col = col_idx
                
                # Check time columns
                elif any(cls.normalize_column_name(tc) == col_name for tc in cls.TIME_COLUMNS):
                    time_col = col_idx
                
                # Score date columns (only if no datetime column found)
                for dc in cls.DATE_COLUMNS:
                    if cls.normalize_column_name(dc) == col_name:
                        score = 100  # Base score
                        # Bonus for exact "date" match
                        if col_name in ['วันที่', 'date']:
                            score += 50
                        date_col_scores[col_idx] = score
                        break
                
                # Check description column (prefer 'description'/'descriptions' over 'details')
                if any(cls.normalize_column_name(dc) == col_name for dc in cls.DESCRIPTION_COLUMNS):
                    # Only overwrite if we haven't found a better match yet
                    if desc_col is None or col_name in ['description', 'descriptions', 'รายการ']:
                        desc_col = col_idx
                
                # Check debit column
                if any(cls.normalize_column_name(dc) == col_name for dc in cls.DEBIT_COLUMNS):
                    debit_col = col_idx
                
                # Check credit column
                if any(cls.normalize_column_name(cc) == col_name for cc in cls.CREDIT_COLUMNS):
                    credit_col = col_idx
                
                # Check balance column
                if any(cls.normalize_column_name(bc) == col_name for bc in cls.BALANCE_COLUMNS):
                    balance_col = col_idx
                
                # Check channel column
                if any(cls.normalize_column_name(cc) == col_name for cc in cls.CHANNEL_COLUMNS):
                    channel_col = col_idx
            
            # Select best date column based on score (only if no datetime column)
            date_col = None
            if datetime_col is None and date_col_scores:
                best_date_col = max(date_col_scores, key=date_col_scores.get)
                if date_col_scores[best_date_col] > 0:  # Only if positive score
                    date_col = best_date_col
            
            # Use datetime column if available, otherwise date column
            effective_date_col = datetime_col if datetime_col is not None else date_col
            
            # A valid header must have at least (datetime or date), description, and (debit or credit)
            if effective_date_col is not None and desc_col is not None and (debit_col is not None or credit_col is not None):
                column_mapping = {
                    'date': effective_date_col,  # Can be datetime or date column
                    'time': time_col,  # Separate time column (if exists)
                    'description': desc_col,
                    'debit': debit_col,
                    'credit': credit_col,
                    'balance': balance_col,
                    'channel': channel_col,
                }
                return idx, column_mapping
        
        raise ValueError("Could not detect header row in CSV file. Please ensure the file contains proper column headers.")
    
    @staticmethod
    def parse_datetime(date_str: str, time_str: str = '') -> Optional[datetime]:
        """
        Parse datetime from date string and optional separate time string
        Supports Thai Buddhist Era and various formats
        
        Priority:
        1. If date_str contains full datetime → parse directly
        2. If date_str is date-only:
           a) AND time_str has time → combine date + time
           b) AND time_str empty → use 00:00
        3. If date_str is time-only AND time_str has date → swap and combine
        """
        if not date_str or not date_str.strip():
            return None
        
        date_str = date_str.strip()
        time_str = time_str.strip() if time_str else ''
        
        # Helper function to check if string is time-only (HH:MM or HH:MM:SS)
        def is_time_only(s: str) -> bool:
            """Check if string contains only time (no date component)"""
            time_only_patterns = [
                r'^\d{1,2}:\d{2}$',           # 07:49
                r'^\d{1,2}:\d{2}:\d{2}$',     # 07:49:30
            ]
            return any(re.match(pattern, s) for pattern in time_only_patterns)
        
        # CASE 1: If date_str is actually time-only, swap with time_str
        if is_time_only(date_str) and time_str and not is_time_only(time_str):
            # Swap: date_str should be date, time_str should be time
            date_str, time_str = time_str, date_str
        
        # Convert Buddhist Era if present
        year_match = re.search(r'\d{4}', date_str)
        if year_match:
            year = int(year_match.group())
            if year >= 2400:  # Buddhist Era
                date_str = date_str.replace(str(year), str(year - 543))
        
        # CASE 2: Try parsing date_str as full datetime (contains both date and time)
        datetime_formats = [
            '%d/%m/%Y %H:%M',       # 01/12/2025 14:30
            '%d/%m/%Y %H:%M:%S',    # 01/12/2025 14:30:00
            '%d-%m-%Y %H:%M',       # 01-12-2025 14:30
            '%d-%m-%Y %H:%M:%S',    # 01-12-2025 14:30:00
            '%d/%m/%y %H:%M',       # 01/12/25 14:30
            '%d-%m-%y %H:%M',       # 01-12-25 14:30
            '%H:%M %d/%m/%Y',       # 14:30 01/12/2025 (time first)
            '%H:%M:%S %d/%m/%Y',    # 14:30:00 01/12/2025
        ]
        
        # Only try datetime formats if date_str contains space or time pattern
        if ' ' in date_str or ':' in date_str:
            for fmt in datetime_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        
        # CASE 3: Parse date_str as date-only
        date_formats = [
            '%d-%m-%y',      # 01-12-25 (KBank format)
            '%d/%m/%y',      # 01/12/25
            '%d-%m-%Y',      # 01-12-2025
            '%d/%m/%Y',      # 01/12/2025
            '%Y-%m-%d',      # 2025-12-01 (ISO format)
            '%d.%m.%Y',      # 01.12.2025
            '%d %b %Y',      # 01 Dec 2025
            '%d %B %Y',      # 01 December 2025
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            # If still can't parse date, return None
            return None
        
        # CASE 4: Combine parsed date with separate time string
        if time_str and not is_time_only(date_str):  # Ensure we don't double-process
            time_formats = ['%H:%M', '%H:%M:%S']
            for time_fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(time_str, time_fmt).time()
                    return datetime.combine(parsed_date.date(), parsed_time)
                except ValueError:
                    continue
        
        # CASE 5: Return date with 00:00 time (fallback)
        return parsed_date
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        DEPRECATED: Use parse_datetime instead
        Legacy method for backward compatibility
        """
        return CSVParserService.parse_datetime(date_str, '')
    
    @staticmethod
    def parse_number(value: str) -> Optional[Decimal]:
        """Parse number string with support for Thai baht symbol, parentheses for negative"""
        if not value or not value.strip():
            return None
        
        cleaned = value.strip()
        
        # Handle empty or dash
        if not cleaned or cleaned == '-':
            return None
        
        # Check for negative amount in parentheses: (1,200.00)
        is_negative = False
        if cleaned.startswith('(') and cleaned.endswith(')'):
            is_negative = True
            cleaned = cleaned[1:-1]
        
        # Remove Thai baht symbol
        cleaned = cleaned.replace('฿', '').replace('฿', '')
        
        # Remove commas and whitespace
        cleaned = cleaned.replace(',', '').replace(' ', '')
        
        if not cleaned or cleaned == '-':
            return None
        
        # Remove any non-numeric characters except decimal point and minus sign
        cleaned = ''.join(c for c in cleaned if c.isdigit() or c in '.-')
        
        if not cleaned or cleaned in ['-', '.']:
            return None
        
        try:
            amount = Decimal(cleaned)
            return -amount if is_negative else amount
        except (ValueError, TypeError, Exception):
            return None
    
    @staticmethod
    def is_summary_row(description: str) -> bool:
        """Detect if row is a summary/total/balance row that should be skipped"""
        if not description or not description.strip():
            return False
        
        desc_lower = description.lower().strip()
        
        # Thai and English summary keywords
        summary_keywords = [
            'ยอดยกมา', 'ยอดรวม', 'รวม', 'ยอดปิด',
            'total', 'balance forward', 'opening balance', 
            'closing balance', 'summary', 'subtotal',
            'grand total', 'sum'
        ]
        
        return any(keyword in desc_lower for keyword in summary_keywords)
    
    @classmethod
    def parse_csv(cls, file_content: str, enable_diagnostics: bool = True) -> Dict:
        """
        Parse CSV content and return structured data with diagnostics
        Returns: {
            'header_row_index': int,
            'metadata_rows': List[str],  # Rows before header
            'transactions': List[Dict],
            'column_mapping': Dict,
            'diagnostics': CSVParserDiagnostics (if enabled),
        }
        """
        # Initialize diagnostics
        diagnostics = CSVParserDiagnostics() if enable_diagnostics else None
        
        # Detect delimiter
        delimiter = cls.detect_delimiter(file_content)
        if diagnostics:
            diagnostics.detected_delimiter = delimiter
        
        # Read all rows from CSV with detected delimiter
        csv_reader = csv.reader(StringIO(file_content), delimiter=delimiter)
        all_rows = list(csv_reader)
        
        if not all_rows:
            raise ValueError("CSV file is empty")
        
        if diagnostics:
            diagnostics.total_rows = len(all_rows)
        
        # Detect header row
        header_idx, column_mapping = cls.detect_header_row(all_rows)
        
        if diagnostics:
            diagnostics.header_row_index = header_idx
            # Get detected column names
            header_row = all_rows[header_idx]
            diagnostics.detected_columns = [col.strip() for col in header_row if col.strip()]
        
        # Extract metadata rows (rows before header)
        metadata_rows = all_rows[:header_idx]
        
        # Parse data rows
        transactions = []
        data_rows = all_rows[header_idx + 1:]  # Skip header row itself
        
        for row_idx, row in enumerate(data_rows):
            # Skip empty rows
            if not any(cell.strip() for cell in row):
                if diagnostics:
                    diagnostics.skipped_rows += 1
                    diagnostics.add_skip_reason('Empty row')
                continue
            
            # Extract values based on column mapping
            description = row[column_mapping['description']] if column_mapping['description'] is not None and column_mapping['description'] < len(row) else ''
            
            # Skip summary rows BEFORE parsing (semantic detection)
            if cls.is_summary_row(description):
                if diagnostics:
                    diagnostics.skipped_rows += 1
                    diagnostics.add_skip_reason('Summary row (ยอดยกมา/Total)')
                continue
            
            date_str = row[column_mapping['date']] if column_mapping['date'] is not None and column_mapping['date'] < len(row) else ''
            time_str = row[column_mapping['time']] if column_mapping.get('time') is not None and column_mapping['time'] < len(row) else ''
            debit_str = row[column_mapping['debit']] if column_mapping['debit'] is not None and column_mapping['debit'] < len(row) else ''
            credit_str = row[column_mapping['credit']] if column_mapping['credit'] is not None and column_mapping['credit'] < len(row) else ''
            balance_str = row[column_mapping['balance']] if column_mapping['balance'] is not None and column_mapping['balance'] < len(row) else ''
            channel_str = row[column_mapping['channel']] if column_mapping['channel'] is not None and column_mapping['channel'] < len(row) else ''
            
            # DEBUG: Log first few rows to understand data format
            if diagnostics and diagnostics.parsed_rows + diagnostics.skipped_rows < 3:
                print(f"DEBUG Row {row_idx}: date_str='{date_str}', time_str='{time_str}'")
            
            # Parse datetime (combine date + time if separate columns exist)
            effective_at = cls.parse_datetime(date_str, time_str)
            if not effective_at:
                # Skip rows without valid dates (might be totals or summary rows)
                if diagnostics:
                    diagnostics.skipped_rows += 1
                    diagnostics.add_skip_reason('Invalid/missing date')
                continue
            
            debit = cls.parse_number(debit_str)
            credit = cls.parse_number(credit_str)
            balance = cls.parse_number(balance_str)
            
            # Skip if no transaction amount
            if debit is None and credit is None:
                if diagnostics:
                    diagnostics.skipped_rows += 1
                    diagnostics.add_skip_reason('No debit/credit amount')
                continue
            
            transaction = {
                'effective_at': effective_at,
                'description': description.strip(),
                'debit': debit,
                'credit': credit,
                'balance': balance,
                'channel': channel_str.strip() if channel_str else None,
                'raw_row': row,  # Store original row
            }
            
            transactions.append(transaction)
            
            if diagnostics:
                diagnostics.parsed_rows += 1
                # Track date range (store datetime objects, convert to ISO in to_dict())
                if diagnostics.csv_date_range['start'] is None:
                    diagnostics.csv_date_range['start'] = effective_at
                elif effective_at < diagnostics.csv_date_range['start']:
                    diagnostics.csv_date_range['start'] = effective_at
                    
                if diagnostics.csv_date_range['end'] is None:
                    diagnostics.csv_date_range['end'] = effective_at
                elif effective_at > diagnostics.csv_date_range['end']:
                    diagnostics.csv_date_range['end'] = effective_at
        
        result = {
            'header_row_index': header_idx,
            'metadata_rows': metadata_rows,
            'transactions': transactions,
            'column_mapping': column_mapping,
        }
        
        if diagnostics:
            result['diagnostics'] = diagnostics
        
        return result
    
    @staticmethod
    def generate_fingerprint(bank_account_id: str, transaction: Dict) -> str:
        """
        Generate deterministic fingerprint for duplicate detection
        Based on: bank_account + date + debit + credit + balance + normalized description
        """
        # Normalize description: remove extra spaces, convert to lowercase
        normalized_desc = ' '.join(transaction['description'].lower().split())
        
        # Create fingerprint string
        fingerprint_parts = [
            str(bank_account_id),
            transaction['effective_at'].isoformat(),
            str(transaction['debit']) if transaction['debit'] else '',
            str(transaction['credit']) if transaction['credit'] else '',
            str(transaction['balance']) if transaction['balance'] else '',
            normalized_desc,
        ]
        
        fingerprint_str = '|'.join(fingerprint_parts)
        
        # Generate SHA256 hash
        return hashlib.sha256(fingerprint_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def extract_balance_info(metadata_rows: List[List[str]], transactions: List[Dict]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Extract opening and closing balance from metadata or transactions
        Returns: (opening_balance, closing_balance)
        """
        opening_balance = None
        closing_balance = None
        
        # Try to find balance in metadata
        for row in metadata_rows:
            row_text = ' '.join(row).lower()
            
            # Look for opening balance keywords
            if any(keyword in row_text for keyword in ['opening balance', 'ยอดยกมา', 'balance forward']):
                for cell in row:
                    amount = CSVParserService.parse_number(cell)
                    if amount is not None:
                        opening_balance = amount
                        break
            
            # Look for closing balance keywords
            if any(keyword in row_text for keyword in ['closing balance', 'ยอดปิด', 'ending balance']):
                for cell in row:
                    amount = CSVParserService.parse_number(cell)
                    if amount is not None:
                        closing_balance = amount
                        break
        
        # If not found in metadata, use first and last transaction balances
        if transactions:
            if opening_balance is None and transactions[0]['balance'] is not None:
                # Opening balance = first transaction balance - first transaction amount
                first_txn = transactions[0]
                if first_txn['credit']:
                    opening_balance = first_txn['balance'] - first_txn['credit']
                elif first_txn['debit']:
                    opening_balance = first_txn['balance'] + first_txn['debit']
            
            if closing_balance is None and transactions[-1]['balance'] is not None:
                closing_balance = transactions[-1]['balance']
        
        return opening_balance, closing_balance
