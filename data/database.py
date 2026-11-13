import os
import sqlite3


class GlossaryManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        # Ensure the directory containing the database exists before connecting
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS glossary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_term TEXT NOT NULL,
                    target_term TEXT NOT NULL,
                    context_notes TEXT
                )
            """)
            conn.commit()

    # ------------------------------------------------------------------
    # Legacy API (used by core/engine.py)
    # ------------------------------------------------------------------
    def add_term(self, source, target, notes=""):
        """Legacy method — adds a term with optional notes."""
        if not source or not target:
            return False
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO glossary (source_term, target_term, context_notes) VALUES (?, ?, ?)",
                (source, target, notes)
            )
            conn.commit()
        return True

    def delete_term(self, term_id):
        """Legacy method — deletes by integer id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM glossary WHERE id = ?", (term_id,))
            conn.commit()

    def get_all_terms(self):
        """Legacy method — returns list of dicts."""
        terms = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM glossary")
            for row in cursor:
                terms.append({
                    "id": row["id"],
                    "source": row["source_term"],
                    "target": row["target_term"],
                    "notes": row["context_notes"]
                })
        return terms

    def format_for_prompt(self, terms):
        """Formats the list of terms into a string for LLM injection."""
        if not terms:
            return ""
        lines = ["Glossary Constraints (Strictly follow these):"]
        for t in terms:
            if isinstance(t, dict):
                lines.append(f"- {t['source']} -> {t['target']}")
            else:
                lines.append(f"- {t[0]} -> {t[1]}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Modern API (used by ui/tabs/glossary_tab.py)
    # ------------------------------------------------------------------
    def add_entry(self, source, target):
        """Add a new term (no notes). Returns True on success."""
        return self.add_term(source, target, notes="")

    def delete_entry(self, term_id):
        """Delete a term by its integer id."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM glossary WHERE id = ?",
                (term_id,)
            )
            conn.commit()
        return True

    def get_all_entries(self):
        """Return list of dicts with id, source, target for the glossary table."""
        entries = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, source_term, target_term FROM glossary ORDER BY id"
            )
            for row in cursor:
                entries.append({
                    "id": row[0],
                    "source": row[1],
                    "target": row[2],
                })
        return entries