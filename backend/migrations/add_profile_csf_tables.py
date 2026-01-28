# backend/migrations/add_profile_csf_tables.py
"""
Migración para agregar tablas de CSF en perfiles de usuario
"""
from sqlalchemy import text

def upgrade_profile_csf_tables(engine):
    """Crea tablas para CSF en perfiles"""
    
    # Tabla csf_documents - Documentos CSF subidos
    create_csf_documents = """
    CREATE TABLE IF NOT EXISTS csf_documents (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        filename VARCHAR(255),
        original_filename VARCHAR(255),
        file_path VARCHAR(500),
        file_size INTEGER,
        extracted_data JSON,
        extraction_method VARCHAR(20) DEFAULT 'ocr_pdf',
        confidence_score REAL DEFAULT 0.0,
        extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT FALSE,
        status VARCHAR(20) DEFAULT 'processing',
        validation_errors JSON,
        validation_warnings JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """
    
    # Tabla csf_profile_history - Historial de cambios
    create_csf_profile_history = """
    CREATE TABLE IF NOT EXISTS csf_profile_history (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        csf_document_id INTEGER,
        profile_data_before JSON,
        profile_data_after JSON,
        operation_type VARCHAR(20) DEFAULT 'apply',
        operation_reason VARCHAR(255),
        was_modified_by_user BOOLEAN DEFAULT FALSE,
        user_notes TEXT,
        applied_by_user_id INTEGER,
        applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (csf_document_id) REFERENCES csf_documents (id) ON DELETE CASCADE,
        FOREIGN KEY (applied_by_user_id) REFERENCES users (id)
    );
    """
    
    # Índices para performance
    create_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_csf_documents_user_id ON csf_documents(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_csf_documents_active ON csf_documents(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_csf_documents_created_at ON csf_documents(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_csf_history_user_id ON csf_profile_history(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_csf_history_applied_date ON csf_profile_history(applied_date);",
        "CREATE INDEX IF NOT EXISTS idx_csf_history_document_id ON csf_profile_history(csf_document_id);"
    ]
    
    with engine.connect() as conn:
        # Crear tablas
        conn.execute(text(create_csf_documents))
        conn.execute(text(create_csf_profile_history))
        
        # Crear índices
        for index_sql in create_indexes:
            conn.execute(text(index_sql))
        
        # Para PostgreSQL, actualizar secuencias
        if engine.dialect.name == 'postgresql':
            conn.execute(text("SELECT setval('csf_documents_id_seq', COALESCE(MAX(id), 1)) FROM csf_documents;"))
            conn.execute(text("SELECT setval('csf_profile_history_id_seq', COALESCE(MAX(id), 1)) FROM csf_profile_history;"))
        
        conn.commit()
    
    print("✅ Tablas CSF de perfil creadas exitosamente")

def downgrade_profile_csf_tables(engine):
    """Elimina tablas CSF de perfil (rollback)"""
    
    drop_tables = [
        "DROP TABLE IF EXISTS csf_profile_history;",
        "DROP TABLE IF EXISTS csf_documents;"
    ]
    
    with engine.connect() as conn:
        for drop_sql in drop_tables:
            conn.execute(text(drop_sql))
        conn.commit()
    
    print("⏪ Tablas CSF de perfil eliminadas (rollback)")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.database import engine
    
    print("🔄 Ejecutando migración de CSF de perfil...")
    upgrade_profile_csf_tables(engine)
    print("✅ Migración CSF de perfil completada")