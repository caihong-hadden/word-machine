import sqlite3
import time
from typing import List, Tuple, Optional, Dict

DB_PATH = "word_machine.db"

def _get_connection():
    # Enable foreign keys for SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Dictionaries
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Dictionaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            file_path TEXT,
            is_active INTEGER DEFAULT 0
        )
    ''')
    
    # Words
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dict_id INTEGER,
            word TEXT,
            ipa TEXT,
            meaning TEXT,
            sentences TEXT,
            order_index INTEGER,
            FOREIGN KEY (dict_id) REFERENCES Dictionaries (id) ON DELETE CASCADE
        )
    ''')
    
    # Progress
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Progress (
            dict_id INTEGER PRIMARY KEY,
            current_index INTEGER DEFAULT 0,
            last_update INTEGER,
            FOREIGN KEY (dict_id) REFERENCES Dictionaries (id) ON DELETE CASCADE
        )
    ''')
    
    # ReviewQueue
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ReviewQueue (
            word_id INTEGER PRIMARY KEY,
            next_review_timestamp INTEGER,
            review_count INTEGER DEFAULT 0,
            FOREIGN KEY (word_id) REFERENCES Words (id) ON DELETE CASCADE
        )
    ''')
    
    # Mistakes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Mistakes (
            word_id INTEGER PRIMARY KEY,
            add_timestamp INTEGER,
            FOREIGN KEY (word_id) REFERENCES Words (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def import_dictionary(dict_name: str, file_path: str, words_list: List[Tuple[str, str, str, str, int]]):
    """
    Imports a dictionary and its words.
    words_list: list of tuples (word, ipa, meaning, sentences, order_index)
    """
    conn = _get_connection()
    cursor = conn.cursor()
    
    try:
        # Insert dictionary
        cursor.execute('''
            INSERT INTO Dictionaries (name, file_path, is_active)
            VALUES (?, ?, 0)
        ''', (dict_name, file_path))
        
        dict_id = cursor.lastrowid
        
        # Prepare word records
        word_records = [
            (dict_id, w[0], w[1], w[2], w[3], w[4]) for w in words_list
        ]
        
        # Insert words
        cursor.executemany('''
            INSERT INTO Words (dict_id, word, ipa, meaning, sentences, order_index)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', word_records)
        
        # Initialize progress
        cursor.execute('''
            INSERT INTO Progress (dict_id, current_index, last_update)
            VALUES (?, 0, ?)
        ''', (dict_id, int(time.time())))
        
        conn.commit()
        return dict_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_active_dictionaries() -> List[Dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, file_path, is_active FROM Dictionaries WHERE is_active = 1')
    rows = cursor.fetchall()
    conn.close()
    
    return [{'id': r[0], 'name': r[1], 'file_path': r[2], 'is_active': r[3]} for r in rows]

def get_all_dictionaries() -> List[Dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, file_path, is_active FROM Dictionaries')
    rows = cursor.fetchall()
    conn.close()
    
    return [{'id': r[0], 'name': r[1], 'file_path': r[2], 'is_active': r[3]} for r in rows]

def set_active_dictionaries(dict_ids: List[int]):
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Deactivate all first
    cursor.execute('UPDATE Dictionaries SET is_active = 0')
    
    # Activate specified
    if dict_ids:
        placeholders = ','.join('?' * len(dict_ids))
        cursor.execute(f'UPDATE Dictionaries SET is_active = 1 WHERE id IN ({placeholders})', dict_ids)
        
    conn.commit()
    conn.close()

def get_next_new_word(active_dict_ids: List[int]) -> Optional[Dict]:
    if not active_dict_ids:
        return None
        
    conn = _get_connection()
    cursor = conn.cursor()
    
    # Get the word from the first dictionary that has available words based on progress
    placeholders = ','.join('?' * len(active_dict_ids))
    
    query = f'''
        SELECT w.id, w.dict_id, w.word, w.ipa, w.meaning, w.sentences, w.order_index, p.current_index
        FROM Dictionaries d
        JOIN Progress p ON d.id = p.dict_id
        JOIN Words w ON d.id = w.dict_id AND w.order_index >= p.current_index
        WHERE d.id IN ({placeholders})
        ORDER BY d.id, w.order_index
        LIMIT 1
    '''
    
    cursor.execute(query, active_dict_ids)
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'dict_id': row[1],
            'word': row[2],
            'ipa': row[3],
            'meaning': row[4],
            'sentences': row[5],
            'order_index': row[6],
            'current_index': row[7]
        }
    return None

def update_progress(dict_id: int, index: int):
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE Progress 
        SET current_index = ?, last_update = ?
        WHERE dict_id = ?
    ''', (index, int(time.time()), dict_id))
    
    conn.commit()
    conn.close()

def _enforce_review_queue_limit(cursor):
    cursor.execute('SELECT COUNT(*) FROM ReviewQueue')
    count = cursor.fetchone()[0]
    if count > 5000:
        excess = count - 5000
        # Delete oldest by next_review_timestamp
        cursor.execute('''
            DELETE FROM ReviewQueue 
            WHERE word_id IN (
                SELECT word_id FROM ReviewQueue 
                ORDER BY next_review_timestamp ASC 
                LIMIT ?
            )
        ''', (excess,))

def add_to_review(word_id: int, is_correct: bool):
    # Simple Ebbinghaus intervals in seconds: 
    # 0s, 5m(300s), 30m(1800s), 12h(43200s), 1d(86400s), 2d(172800s), 4d, 7d, 15d
    intervals = [0, 300, 1800, 43200, 86400, 172800, 345600, 604800, 1296000]
    
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT review_count FROM ReviewQueue WHERE word_id = ?', (word_id,))
    row = cursor.fetchone()
    
    current_time = int(time.time())
    
    if not row:
        # New to review queue
        new_count = 1 if is_correct else 0
        next_review_time = current_time + intervals[min(new_count, len(intervals)-1)]
        cursor.execute('''
            INSERT INTO ReviewQueue (word_id, next_review_timestamp, review_count)
            VALUES (?, ?, ?)
        ''', (word_id, next_review_time, new_count))
    else:
        # Update existing
        current_count = row[0]
        if is_correct:
            new_count = current_count + 1
        else:
            new_count = 0 # reset on failure
            
        next_review_time = current_time + intervals[min(new_count, len(intervals)-1)]
        cursor.execute('''
            UPDATE ReviewQueue 
            SET next_review_timestamp = ?, review_count = ?
            WHERE word_id = ?
        ''', (next_review_time, new_count, word_id))
        
    _enforce_review_queue_limit(cursor)
    
    conn.commit()
    conn.close()

def get_due_reviews(limit: int = 50) -> List[Dict]:
    conn = _get_connection()
    cursor = conn.cursor()
    
    current_time = int(time.time())
    
    cursor.execute('''
        SELECT w.id, w.dict_id, w.word, w.ipa, w.meaning, w.sentences, w.order_index, r.review_count
        FROM ReviewQueue r
        JOIN Words w ON r.word_id = w.id
        WHERE r.next_review_timestamp <= ?
        ORDER BY r.next_review_timestamp ASC
        LIMIT ?
    ''', (current_time, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        'id': r[0],
        'dict_id': r[1],
        'word': r[2],
        'ipa': r[3],
        'meaning': r[4],
        'sentences': r[5],
        'order_index': r[6],
        'review_count': r[7]
    } for r in rows]

def _enforce_mistakes_limit(cursor):
    cursor.execute('SELECT COUNT(*) FROM Mistakes')
    count = cursor.fetchone()[0]
    if count > 5000:
        excess = count - 5000
        # Delete oldest by add_timestamp
        cursor.execute('''
            DELETE FROM Mistakes 
            WHERE word_id IN (
                SELECT word_id FROM Mistakes 
                ORDER BY add_timestamp ASC 
                LIMIT ?
            )
        ''', (excess,))

def add_to_mistakes(word_id: int):
    conn = _get_connection()
    cursor = conn.cursor()
    
    current_time = int(time.time())
    
    cursor.execute('''
        INSERT OR REPLACE INTO Mistakes (word_id, add_timestamp)
        VALUES (?, ?)
    ''', (word_id, current_time))
    
    _enforce_mistakes_limit(cursor)
    
    conn.commit()
    conn.close()

def clear_cache():
    """TRUNCATE equivalent for ReviewQueue."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM ReviewQueue')
    
    conn.commit()
    conn.close()

def reset_all():
    """Drops all tables and recreates them."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS Mistakes')
    cursor.execute('DROP TABLE IF EXISTS ReviewQueue')
    cursor.execute('DROP TABLE IF EXISTS Progress')
    cursor.execute('DROP TABLE IF EXISTS Words')
    cursor.execute('DROP TABLE IF EXISTS Dictionaries')
    
    conn.commit()
    conn.close()
    
    # Recreate tables
    init_db()

def set_db_path(path: str):
    """Allows setting a custom DB path for testing."""
    global DB_PATH
    DB_PATH = path
