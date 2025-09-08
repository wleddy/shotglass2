from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
        
class StarterTable(SqliteTable):
    """Handle some basic interactions this table"""

    TABLE_IDENTITY = 'sample' # so we can get the table name before the app starts up

    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = self.TABLE_IDENTITY
        self.order_by_col = 'lower(name)'
        self.defaults = {'rank':0,}
        
    def create_table(self):
        """Define and create a table"""
        
        sql = """
            'name' TEXT,
            'description' TEXT,
            -- FOREIGN KEY (sensor_id) REFERENCES sensor(id) ON DELETE CASCADE,
            'rank' INTEGER DEFAULT 0 
            """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        """
    
        # {'name':'a_column_name','definition':'A_DATA_TYPE_&_CONSTRAINTS',},
        column_list = []
        
        return column_list
    

def init_db(db):
    """Create Tables."""
    l = globals().copy()
    for n,o in l.items():
        if type(o) == type and \
            issubclass(o,SqliteTable) and \
            o != SqliteTable:
    
            o(db).init_table()
