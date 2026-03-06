import sqlite3
import os

class Database:
    def __init__(self, db_path="imgcraft.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Images table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE,
                    filename TEXT,
                    inspiration TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Tags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
            """)
            # Image tags mapping
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS image_tags (
                    image_id INTEGER,
                    tag_id INTEGER,
                    PRIMARY KEY (image_id, tag_id),
                    FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
                )
            """)
            conn.commit()

            # Folders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE,
                    name TEXT,
                    last_image_path TEXT,
                    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_folder(self, path):
        name = os.path.basename(path)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO folders (path, name) VALUES (?, ?)", (path, name))
            conn.commit()

    def update_folder_state(self, folder_path, last_image_path):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE folders SET last_image_path = ?, last_scanned = CURRENT_TIMESTAMP WHERE path = ?", (last_image_path, folder_path))
            conn.commit()

    def get_all_folders(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, path, last_image_path FROM folders ORDER BY last_scanned DESC")
            return cursor.fetchall()

    def add_image(self, path):
        filename = os.path.basename(path)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO images (path, filename) VALUES (?, ?)", (path, filename))
            conn.commit()
            cursor.execute("SELECT id FROM images WHERE path = ?", (path,))
            return cursor.fetchone()[0]

    def update_inspiration(self, image_id, inspiration):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE images SET inspiration = ? WHERE id = ?", (inspiration, image_id))
            conn.commit()

    def add_tag(self, tag_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            conn.commit()
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            return cursor.fetchone()[0]

    def tag_image(self, image_id, tag_name):
        tag_id = self.add_tag(tag_name)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO image_tags (image_id, tag_id) VALUES (?, ?)", (image_id, tag_id))
            conn.commit()

    def untag_image(self, image_id, tag_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM image_tags 
                WHERE image_id = ? AND tag_id = (SELECT id FROM tags WHERE name = ?)
            """, (image_id, tag_name))
            conn.commit()

    def get_image_data(self, path):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, inspiration FROM images WHERE path = ?", (path,))
            return cursor.fetchone()

    def get_image_tags(self, image_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN image_tags it ON t.id = it.tag_id
                WHERE it.image_id = ?
            """, (image_id,))
            return [row[0] for row in cursor.fetchall()]

    def get_all_tags(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM tags")
            return [row[0] for row in cursor.fetchall()]

    def clear_all(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM image_tags")
            cursor.execute("DELETE FROM tags")
            cursor.execute("DELETE FROM images")
            cursor.execute("DELETE FROM folders")
            conn.commit()

    def get_folder_by_path(self, path):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, last_image_path FROM folders WHERE path = ?", (path,))
            return cursor.fetchone()

    def add_images_batch(self, images):
        """Batch image insertion for speed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("INSERT OR IGNORE INTO images (path, filename) VALUES (?, ?)", 
                             [(p, os.path.basename(p)) for p in images])
            conn.commit()

    def get_all_images(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM images ORDER BY filename ASC")
            return [row[0] for row in cursor.fetchall()]

    def get_images_by_tag(self, tag_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.path FROM images i
                JOIN image_tags it ON i.id = it.image_id
                JOIN tags t ON t.id = it.tag_id
                WHERE t.name = ?
            """, (tag_name,))
            return [row[0] for row in cursor.fetchall()]

    def get_images_in_folder(self, folder_path):
        """Returns images starting with folder_path for speed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM images WHERE path LIKE ? ORDER BY path ASC", (folder_path + '%',))
            return [row[0] for row in cursor.fetchall()]
    
    def get_images_with_inspiration(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path, inspiration FROM images WHERE inspiration IS NOT NULL AND inspiration != ''")
            return cursor.fetchall()

    def get_untouched_images(self, folder_path=None):
        """Returns images with no tags AND no inspiration notes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT path FROM images 
                WHERE (inspiration IS NULL OR inspiration = '') 
                AND id NOT IN (SELECT image_id FROM image_tags)
            """
            params = []
            if folder_path:
                query += " AND path LIKE ?"
                params.append(folder_path + '%')
            
            query += " ORDER BY filename ASC"
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]
