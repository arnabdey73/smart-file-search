-- SQLite schema for smart file search
-- Uses FTS5 for full-text search with optional vector storage

-- Files table - stores file metadata
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,  -- modification time as Unix timestamp
    ext TEXT NOT NULL,    -- file extension
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index on path for faster lookups
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_ext ON files(ext);
CREATE INDEX IF NOT EXISTS idx_files_mtime ON files(mtime);

-- Documents table with FTS5 - stores document chunks
CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
    file_id UNINDEXED,   -- Reference to files.id
    pointer UNINDEXED,   -- Chunk identifier (e.g., "chunk_0", "page_1")
    content,             -- Searchable text content
    content='docs_content',  -- External content table
    content_rowid='rowid'
);

-- External content storage for FTS5
CREATE TABLE IF NOT EXISTS docs_content (
    rowid INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    pointer TEXT NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Create indexes for docs_content
CREATE INDEX IF NOT EXISTS idx_docs_file_id ON docs_content(file_id);
CREATE INDEX IF NOT EXISTS idx_docs_pointer ON docs_content(file_id, pointer);

-- Optional vector embeddings table for semantic search
CREATE TABLE IF NOT EXISTS vecs (
    doc_rowid INTEGER PRIMARY KEY,
    vector BLOB,  -- Serialized vector embedding
    FOREIGN KEY (doc_rowid) REFERENCES docs_content(rowid) ON DELETE CASCADE
);

-- Triggers to keep FTS5 and content table in sync
CREATE TRIGGER IF NOT EXISTS docs_ai AFTER INSERT ON docs_content BEGIN
    INSERT INTO docs(rowid, file_id, pointer, content) 
    VALUES (new.rowid, new.file_id, new.pointer, new.content);
END;

CREATE TRIGGER IF NOT EXISTS docs_ad AFTER DELETE ON docs_content BEGIN
    INSERT INTO docs(docs, rowid, file_id, pointer, content) 
    VALUES('delete', old.rowid, old.file_id, old.pointer, old.content);
    DELETE FROM vecs WHERE doc_rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS docs_au AFTER UPDATE ON docs_content BEGIN
    INSERT INTO docs(docs, rowid, file_id, pointer, content) 
    VALUES('delete', old.rowid, old.file_id, old.pointer, old.content);
    INSERT INTO docs(rowid, file_id, pointer, content) 
    VALUES (new.rowid, new.file_id, new.pointer, new.content);
END;

-- Update trigger for files table
CREATE TRIGGER IF NOT EXISTS files_update_timestamp 
    AFTER UPDATE ON files
BEGIN
    UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Cleanup orphaned vectors when files are deleted
CREATE TRIGGER IF NOT EXISTS cleanup_vecs_on_file_delete
    AFTER DELETE ON files
BEGIN
    DELETE FROM vecs WHERE doc_rowid IN (
        SELECT rowid FROM docs_content WHERE file_id = OLD.id
    );
END;
