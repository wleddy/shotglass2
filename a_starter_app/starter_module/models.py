from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
        
class StarterTable(SqliteTable):
    """Handle some basic interactions with the role table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'sample'
        self.order_by_col = 'lower(name)'
        self.defaults = {'rank':0,}
        
    def create_table(self):
        """Define and create a table"""
        
        sql = """
            'name' TEXT,
            'description' TEXT,
            'rank' INTEGER DEFAULT 0 """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        """
    
        column_list = [
        # {'name':'expires','definition':'DATETIME',},
        ]
    
        return column_list

