# backend/migrations/add_csf_tables.py
"""
Migración para agregar tablas de CSF (Cédula de Identificación Fiscal)
"""
from sqlalchemy import text

def upgrade_csf_tables(engine):
    """Crea tablas para CSF en la base de datos"""
    
    # Tabla csf_records - Registros principales de CSF
    create_csf_records = """
    CREATE TABLE IF NOT EXISTS csf_records (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        rfc VARCHAR(13) NOT NULL,
        curp VARCHAR(18),
        nombre_completo VARCHAR(255) NOT NULL,
        primer_apellido VARCHAR(100),
        segundo_apellido VARCHAR(100),
        denominacion_razon_social VARCHAR(255),
        codigo_postal VARCHAR(5),
        calle VARCHAR(255),
        numero_exterior VARCHAR(50),
        numero_interior VARCHAR(50),
        colonia VARCHAR(255),
        localidad VARCHAR(255),
        municipio VARCHAR(255),
        estado VARCHAR(100),
        pais VARCHAR(100) DEFAULT 'MEXICO',
        regimen_fiscal VARCHAR(100),
        regimen_fiscal_key VARCHAR(3),
        estatus VARCHAR(20) DEFAULT 'active',
        fecha_inicio_operaciones DATE,
        ultima_actualizacion_sat TIMESTAMP,
        cedula_pdf_path VARCHAR(500),
        cedula_qr_content TEXT,
        cedula_xml_content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP,
        is_verified BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """
    
    # Tabla csf_validation_cache - Cache de validaciones
    create_csf_validation_cache = """
    CREATE TABLE IF NOT EXISTS csf_validation_cache (
        id INTEGER PRIMARY KEY,
        rfc VARCHAR(13) NOT NULL,
        validation_type VARCHAR(50),
        result JSON,
        is_valid BOOLEAN,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    );
    """
    
    # Tabla csf_history - Historial de cambios
    create_csf_history = """
    CREATE TABLE IF NOT EXISTS csf_history (
        id INTEGER PRIMARY KEY,
        csf_record_id INTEGER NOT NULL,
        rfc VARCHAR(13),
        field_name VARCHAR(100),
        old_value TEXT,
        new_value TEXT,
        change_reason VARCHAR(255),
        changed_by_user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (csf_record_id) REFERENCES csf_records (id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by_user_id) REFERENCES users (id)
    );
    """
    
    # Índices para performance
    create_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_csf_records_user_id ON csf_records(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_csf_records_rfc ON csf_records(rfc);",
        "CREATE INDEX IF NOT EXISTS idx_csf_records_created_at ON csf_records(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_csf_validation_cache_rfc ON csf_validation_cache(rfc);",
        "CREATE INDEX IF NOT EXISTS idx_csf_validation_cache_expires_at ON csf_validation_cache(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_csf_history_record_id ON csf_history(csf_record_id);",
        "CREATE INDEX IF NOT EXISTS idx_csf_history_created_at ON csf_history(created_at);"
    ]
    
    with engine.connect() as conn:
        # Crear tablas
        conn.execute(text(create_csf_records))
        conn.execute(text(create_csf_validation_cache))
        conn.execute(text(create_csf_history))
        
        # Crear índices
        for index_sql in create_indexes:
            conn.execute(text(index_sql))
        
        # Para PostgreSQL, también necesitamos actualizar la secuencia
        if engine.dialect.name == 'postgresql':
            conn.execute(text("SELECT setval('csf_records_id_seq', COALESCE(MAX(id), 1)) FROM csf_records;"))
            conn.execute(text("SELECT setval('csf_validation_cache_id_seq', COALESCE(MAX(id), 1)) FROM csf_validation_cache;"))
            conn.execute(text("SELECT setval('csf_history_id_seq', COALESCE(MAX(id), 1)) FROM csf_history;"))
        
        conn.commit()
    
    print("✅ Tablas CSF creadas exitosamente")

def downgrade_csf_tables(engine):
    """Elimina tablas CSF (rollback)"""
    
    drop_tables = [
        "DROP TABLE IF EXISTS csf_history;",
        "DROP TABLE IF EXISTS csf_validation_cache;",
        "DROP TABLE IF EXISTS csf_records;"
    ]
    
    with engine.connect() as conn:
        for drop_sql in drop_tables:
            conn.execute(text(drop_sql))
        conn.commit()
    
    print("⏪ Tablas CSF eliminadas (rollback)")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.database import engine
    
    print("🔄 Ejecutando migración de CSF...")
    upgrade_csf_tables(engine)
    print("✅ Migración CSF completada")