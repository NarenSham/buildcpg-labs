"""
DataInspector: Reusable utility for inspecting DuckDB databases
Used by all labs to check data quality, row counts, nulls, duplicates, etc.
"""
import duckdb
import pandas as pd
from datetime import datetime


class DataInspector:
    def __init__(self, db_path):
        """Initialize inspector with path to DuckDB database"""
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
    
    def get_all_schemas(self):
        """Get all schemas in database"""
        result = self.conn.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog')
            ORDER BY schema_name;
        """).fetchall()
        return [r[0] for r in result]
    
    def get_tables_by_schema(self, schema):
        """Get all tables in a specific schema"""
        result = self.conn.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema}'
            ORDER BY table_name;
        """).fetchall()
        return [r[0] for r in result]
    
    def get_table_stats(self, schema, table):
        """Get row count, column count, and column names"""
        try:
            row_count = self.conn.execute(f"""
                SELECT COUNT(*) FROM {schema}.{table}
            """).fetchall()[0][0]
            
            columns = self.conn.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{schema}' AND table_name = '{table}'
            """).fetchall()
            
            col_count = len(columns)
            col_names = [c[0] for c in columns]
            
            return {
                'rows': row_count,
                'cols': col_count,
                'col_names': col_names,
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_new_data_count(self, schema, table, days=1):
        """Get count of rows added in last N days"""
        try:
            # Try common date column names
            date_columns = ['order_date', 'ORDERDATE', 'created_at', 'date_added', 'timestamp']
            
            for date_col in date_columns:
                try:
                    result = self.conn.execute(f"""
                        SELECT COUNT(*) 
                        FROM {schema}.{table}
                        WHERE CAST({date_col} AS DATE) >= CURRENT_DATE - INTERVAL {days} DAY
                    """).fetchall()
                    return result[0][0]
                except:
                    continue
            
            return 0
        except Exception as e:
            return {'error': str(e)}
    
    def check_duplicates(self, schema, table, key_column):
        """Check for duplicate key values"""
        try:
            result = self.conn.execute(f"""
                SELECT {key_column}, COUNT(*) as cnt
                FROM {schema}.{table}
                GROUP BY {key_column}
                HAVING COUNT(*) > 1
            """).fetchall()
            return len(result)
        except Exception as e:
            return {'error': str(e)}
    
    def check_null_values(self, schema, table):
        """Check for NULL values in all columns"""
        try:
            columns = self.conn.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{schema}' AND table_name = '{table}'
            """).fetchall()
            
            null_counts = {}
            for col in columns:
                col_name = col[0]
                result = self.conn.execute(f"""
                    SELECT COUNT(*) 
                    FROM {schema}.{table}
                    WHERE {col_name} IS NULL
                """).fetchall()
                null_count = result[0][0]
                if null_count > 0:
                    null_counts[col_name] = null_count
            
            return null_counts
        except Exception as e:
            return {'error': str(e)}
    
    def get_quality_score(self, schema, table, key_column=None):
        """Calculate overall data quality score (0-100)"""
        try:
            score = 100
            
            # Check for duplicates
            if key_column:
                dup_count = self.check_duplicates(schema, table, key_column)
                if dup_count > 0:
                    score -= 10
            
            # Check for nulls
            null_dict = self.check_null_values(schema, table)
            stats = self.get_table_stats(schema, table)
            
            if 'cols' in stats:
                null_percentage = (len(null_dict) / stats['cols']) * 100
                score -= (null_percentage * 0.5)
            
            # Check row count
            if 'rows' in stats:
                if stats['rows'] == 0:
                    score = 0
            
            return max(0, min(100, int(score)))
        except:
            return 0
    
    def get_data_preview(self, schema, table, limit=5):
        """Get preview of table data"""
        try:
            df = self.conn.execute(f"""
                SELECT * FROM {schema}.{table} LIMIT {limit}
            """).fetchdf()
            return df
        except Exception as e:
            return pd.DataFrame({'error': [str(e)]})
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# Example usage:
if __name__ == "__main__":
    # This runs if you execute this file directly
    # Useful for testing
    inspector = DataInspector('lab1_sales_performance/data/lab1_sales_performance.duckdb')
    print("Schemas:", inspector.get_all_schemas())
    inspector.close()