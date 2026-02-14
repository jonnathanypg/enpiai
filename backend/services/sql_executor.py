"""
SQL Execution Service
Resiliently executes raw SQL queries with retry logic for 'MySQL Gone Away' errors.
Inspired by KindiCoreAI architecture.
"""
import logging
import time
from decimal import Decimal
from datetime import date, datetime, time as time_obj
from sqlalchemy import text
from extensions import db

logger = logging.getLogger("SQLExecutor")

class SQLExecutor:
    """
    Executes SQL statements with security checks and automatic retry logic.
    """
    
    FORBIDDEN_KEYWORDS = ["drop ", "alter ", "truncate ", "grant ", "revoke "]
    
    @staticmethod
    def execute_query(sql_query: str, params: dict = None, allowed_actions: list = None) -> dict:
        """
        Execute SQL query with retry logic and security validation.
        
        Args:
            sql_query: The SQL string to execute
            params: Dictionary of parameters for binding
            allowed_actions: List of allowed SQL verbs (e.g., ['select', 'insert'])
            
        Returns:
            Dictionary with 'success', 'data', and 'count'
        """
        if params is None:
            params = {}
        if allowed_actions is None:
            allowed_actions = ['select']
            
        # 1. Basic Cleaning
        clean_sql = "\n".join([line for line in sql_query.splitlines() if not line.strip().startswith('--')]).strip()
        if not clean_sql:
            return {"success": False, "error": "No executable SQL statements found."}
            
        # 2. Security Check (Broad)
        if any(kw in clean_sql.lower() for kw in SQLExecutor.FORBIDDEN_KEYWORDS):
            logger.error(f"SECURITY: Blocked forbidden keyword in query: {clean_sql}")
            return {"success": False, "error": "Query contains forbidden DDL/DCL operations."}
            
        # 3. Execution with Retry
        max_retries = 1
        attempt = 0
        
        while attempt <= max_retries:
            try:
                # Resolve primary action
                statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
                results_list = []
                total_affected = 0
                
                for statement in statements:
                    first_word = statement.split()[0].lower()
                    # Treat 'with' as 'select'
                    effective_action = 'select' if first_word == 'with' else first_word
                    
                    if effective_action not in allowed_actions:
                        return {"success": False, "error": f"Action '{first_word.upper()}' is not authorized."}
                    
                    # Execute statement
                    res = db.session.execute(text(statement), params)
                    
                    if effective_action == 'select':
                        rows = [dict(row._mapping) for row in res]
                        results_list.extend(SQLExecutor._serialize_rows(rows))
                    else:
                        total_affected += res.rowcount
                
                # Commit if write operations occurred
                if total_affected > 0:
                    db.session.commit()
                    return {"success": True, "count": total_affected, "data": f"Success. {total_affected} rows affected."}
                
                return {"success": True, "count": len(results_list), "data": results_list}
                
            except Exception as e:
                db.session.rollback()
                is_gone_away = any(msg in str(e).lower() for msg in ['gone away', 'lost connection', '2006', '2013'])
                
                if is_gone_away and attempt < max_retries:
                    attempt += 1
                    logger.warning(f"DB CONNECTION LOST. Retry attempt {attempt}/{max_retries}...")
                    db.session.remove() # Clear pool and try fresh connection on next loop
                    time.sleep(0.5)
                    continue
                
                logger.error(f"SQL Execution Error: {str(e)}")
                return {"success": False, "error": f"Database Error: {str(e)}"}
        
        return {"success": False, "error": "Connection failed after retries."}

    @staticmethod
    def _serialize_rows(rows: list) -> list:
        """Serializes complex SQL types for JSON compatibility."""
        serialized = []
        for row in rows:
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, (date, datetime, time_obj)):
                    clean_row[k] = v.isoformat()
                elif isinstance(v, Decimal):
                    clean_row[k] = float(v)
                else:
                    clean_row[k] = v
            serialized.append(clean_row)
        return serialized
