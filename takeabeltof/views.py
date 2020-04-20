from flask import request, session, g, url_for, \
     render_template, render_template_string
from flask.views import View
from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.jinja_filters import plural, iso_date_string
from datetime import date


class TableView:
    """A generic class based view for a table"""

    def __init__(self,table,db,**kwargs):
        # import pdb;pdb.set_trace()
        self.source = table # SqliteTable class
        self.db = db # Database connection
        self.table = self.source(self.db)
        self.display_name = self.table.display_name

        self.list_fields = kwargs.get('list_fields',None) # define the fields (by name) to display in list
        self._set_default_list_fields() # set the defaults if needed
        self.has_search_fields = False # set to true if any fields have search == true
        
        self.edit_fields = None # define the fields (by name) to display in edit form
        
        self.list_template = kwargs.get('list_template','list_template.html')
        self.list_table_template = kwargs.get('list_template','list_template_table.html')
        self.edit_template = kwargs.get('edit_template','edit_template.html')
        
        # set the exits
        g.listURL = url_for('.display')
        g.editURL = url_for('.display') + 'edit/'
        g.deleteURL = url_for('.display') + 'delete/'
        g.title = self.display_name
        
        # Include any text you want inserted into the page <head> section
        self.head = ''
            
        # import pdb;pdb.set_trace()
        self.path = [x for x in request.path.split('/') if x]
        if not self.path:
            self.path = ['/']
        self.root = self.path.pop(0)
        
        self.handlers = ['/','edit','delete','filter','order']
        
        self._ajax_request = request.headers.get('X-Requested-With') ==  'XMLHttpRequest'
        
        
        # set for success
        self.success = True
        self.result_text = ''
        
        """
        list: display a list of records
        
        edit: display and process a record

        delete: delete a record
        
        define_list: define the fields to display in a list
        define_edit: define the fields to display in edit
        
        templates: define templates to use for displays. If specified template does not exist,
        use a template defined here.
        list_template: Basic template for the list view
        list_table_template: template to use to render the <table> part of the list view
        
        edit_template:
        
        """
    def delete(self,*args,**kwargs):
        g.title = "Delete {} Record".format(self.display_name)
        
        record_identifier = None
        
        if len(self.path) > 1:
            record_identifier = self.path[1]
        
        ################################
        #### For some reason, passing commit keyword arg 
        #### fails for reasons I can't understand
        ###############################
        # import pdb;pdb.set_trace()
        # success = self.table.delete(record_identifier,commit=True)
            
        self.success = self.table.delete(record_identifier)
        if not self.success:
            self.result_text = 'Not able to delete that record.'
        else:
            self.db.commit()
            
    def dispatch_request(self,*args,**kwargs):
        # import pdb;pdb.set_trace()
        if self.path:
            for handler in self.handlers:
                if handler == self.path[0].lower():
                    if handler == 'edit':
                        return 'Edit Record'
                        break
                    if handler == 'delete':
                        self.delete()
                        # redirect to clear the old path name in browser
                        return redirect(g.listURL)
                    if handler == 'filter':
                        return ListFilter()._save_list_filter()
                    if handler == 'order':
                        return ListFilter()._save_list_order()
                    
        return self.list(**kwargs)
        
    def list(self,**kwargs):
        """Return the response text for flask request"""
        # import pdb;pdb.set_trace()
        g.title = "{} Record List".format(g.title)
                
        # look in session for the saved search...
        # ListFilter().clear_list_filter(self.table)
        filters = ListFilter()
        filters.get_list_filter(self.table)
        self.recs = self.table.select(where=filters.where,order_by=filters.order_by,**kwargs) # TODO filter and sort per self.list_filter and self.list_sort
        
        # ensure that the field list is complete
        self.has_search_fields = False #default state
        self.set_list_fields(self.list_fields)
        
        if self._ajax_request:
            self.list_template = self.list_table_template
                        
        return render_template(self.list_template,
                            data = self,
                            session_fields = ListFilter(), # provides the session field constants
                            **kwargs,
                        )
                        
    def _set_default_list_fields(self):
        """Set up the default fields for the list view if not provided"""
        if not self.list_fields:
            # make up a list of fields to display
            self.list_fields = []
            col_num = -1
            max_cols = 5
            for col in self.table.get_column_names():
                if len(self.list_fields) > max_cols:
                    break
                
                if col[:-3].lower() == '_id':
                    # foreign key
                    continue
            
                col_num += 1
                self.list_fields.append({
                    'name':'{}'.format(col),
                    'label':'{}'.format(self.make_label(col)),
                    # limit the number of visible fields on small screen
                    'class':'{}'.format('w3-hide-small' if len(self.list_fields) == 0 or len(self.list_fields) > 3  else ''),
                    })
                    
                    
    def make_label(self,name):
        if not isinstance(name,str):
            return name
        else:
            return name.replace('_',' ').title()
            
    def set_list_fields(self,fields):
        """Ensure that self.list_fields is a list of dicts and that the dicts have
        all the required keys
        """
        # import pdb;pdb.set_trace()
        
        if not self.list_fields:
            self.list_fields = []
                
        list_fields_temp = [x for x in self.list_fields] # make a copy
            
        if not isinstance(fields,list):
            fields = [fields]
            
        for field in fields:
            if isinstance(field,str):
                # assume to be a field name
                field = {'name':field,'label':'{}'.format(self.make_label(field)),'class':'','search':True}
            if not isinstance(field,dict):
                continue # it must be a dict
            for x in range(len(list_fields_temp)-1,-1,-1): # turkey shoot loop
                default_field_dict = {'label':'','class':'','search':True}
                if not isinstance(list_fields_temp[x],dict) or 'name' not in list_fields_temp[x]:
                    # bad element got into self.list_fields somehow...
                    del list_fields_temp[x]
                    continue
                if list_fields_temp[x].get('name',False) == field.get('name',None):
                    default_field_dict = {'label':'','class':'','search':True}
                    for k in default_field_dict.keys():
                        if k in field:
                            default_field_dict.update({k:field[k]})
                    break
                        
            list_fields_temp[x].update(default_field_dict)
            list_fields_temp[x]['label'] = list_fields_temp[x]['label'] if list_fields_temp[x]['label'] else self.make_label(list_fields_temp[x]['name'])
            if list_fields_temp[x]['search']:
                self.has_search_fields = True
                
        self.list_fields = list_fields_temp
        
        
class ListFilter:
    """A class to manage filtering and sort properties in conjunction with the TableView class
    
    Filtering and sorting data is stored in the session with a set for each database table.
    
    The layout within the session dict is:
        'table_filters':{
            {<table name 1>:
                filters:[{< id of input element>:{'type':<'text' | 'date'>,field_name':<field name>,'value':< filter value >}},{...},],
                'orders':[{'id':< DOM id of column element>:[{'field_name':<field name>,'direction':<int>},{...},]
            }
            {<table name 2>:
                'filters':[{'id':< DOM id of input element>,'type':<text | date>,'field_name:<field name>,'value':< filter value >},{...},],
                'orders':[{'id':< DOM id of column element>:[{'field_name':<field name>,'direction':<int>},{...},]
            }
        }
            The values for sort direction are -1 (descending), 0 (no sort), 1 (ascending)
    """
    
    def __init__(self):
    # some constants
        self.HEADER_NAME = 'table_filters'
        self.FILTERS_NAME = 'filters'
        self.FIELD_NAME = 'field_name'
        self.DOM_ID = 'id'
        self.VALUE = 'value'
        self.TYPE = 'kind'
        self.DATE_START = 'start'
        self.DATE_END = 'end'
        self.ORDERS_NAME = 'orders'
        self.DIRECTION = 'direction'
        self.BEGINNING_OF_TIME = iso_date_string(date(1971,1,1))
        self.END_OF_TIME = iso_date_string(date(2400,12,31))
        
        self.filter_dict = {self.DOM_ID:'',
                            self.TYPE:'text',
                            self.FIELD_NAME:None,
                            self.VALUE:'',
                            self.DATE_START:'',
                            self.DATE_END:'',
                            }
                            
        self.sort_dict = {self.FIELD_NAME:None,
                          self.DIRECTION:0,
                          }
    
    
    def clear_list_filter(self,*args,**kwargs):
        """Remove the list filters"""
        # import pdb;pdb.set_trace()
        if args:
            for arg in args:
                if isinstance(arg,SqliteTable):
                    try:
                        del session[self.HEADER_NAME][arg.table_name]
                    except Exception as e:
                        pass
                    break
        

    def _create_filter_session(self,table_name):
        """Create the session dict to hold the filter data if needed"""
        # import pdb;pdb.set_trace()
        if not self.HEADER_NAME in session:
            session[self.HEADER_NAME] = {}
        if not table_name in session[self.HEADER_NAME]:
            session[self.HEADER_NAME][table_name] = {self.FILTERS_NAME:{},self.ORDERS_NAME:[]}
            
        return session[self.HEADER_NAME][table_name]

        
    def get_list_filter(self,table=None,**kwargs):
        """Return a dict of items to use to filter the list"""
        # import pdb;pdb.set_trace()
        self.where = 1
        self.order_by = 'id'
        if not isinstance(table,SqliteTable):
            return
            
        self._create_filter_session(table.table_name) # ensure it exists
        
        where_list = []
        session_data = session.get(self.HEADER_NAME)
        if session_data and table.table_name in session_data:
            filter_data = session_data[table.table_name][self.FILTERS_NAME]
            for k,v in filter_data.items():
                col = v.get(self.FIELD_NAME)
                val = v.get(self.VALUE)
                kind = v.get(self.TYPE)
                start = v.get(self.DATE_START)
                end = v.get(self.DATE_END)
                if col and (val or start or end):
                    if kind == 'date':
                        start = iso_date_string(start if start else self.BEGINNING_OF_TIME)
                        end = iso_date_string(end if end else self.END_OF_TIME)
                        print(start,end)
                        where_list.append("""date({col}) >= date('{start}') and date({col}) <= date('{end}')""".format(col=col,start=start,end=end))
                        print(where_list[-1])
                    else:
                        where_list.append("""{col} LIKE '%{val}%'""".format(col=col,val=str(val).lower()))
                        
                        
            # import pdb;pdb.set_trace()
            order_list = []
            for order_data in session_data[table.table_name][self.ORDERS_NAME]:
                for dom_id in order_data.keys():
                    col = order_data[dom_id].get(self.FIELD_NAME)
                    direction = int(order_data[dom_id].get(self.DIRECTION,0)) #direction will be -1,0 or 1
                    if col and direction:
                        direction = 'DESC' if direction < 0 else 'ASC'
                        order_list.append("""{col} {direction}""".format(col=col,direction=direction))
        
        if where_list:
            self.where = ' and '.join(where_list)
        if order_list:
            self.order_by = ','.join(order_list)
        else:
            self.order_by = table.order_by_col #default order for this table
            
            
    def _save_list_order(self,*args,**kwargs):
        table_name = request.form.get('table_name')
        # import pdb;pdb.set_trace()
        if table_name:
            self._create_filter_session(table_name)
            order_data = session[self.HEADER_NAME][table_name][self.ORDERS_NAME]
            
            order_dict = self.sort_dict.copy()
            for k,v in self.sort_dict.items():
                order_dict[k] = request.form.get(k)
            
            column_id = request.form.get(self.DOM_ID)
            new_column_defs = []
            if column_id:
                # order_data should be a list
                if not order_data:
                    order_data.append({column_id:order_dict}) # session is set here...
                else:
                    for i in range(len(order_data)-1,-1,-1):
                        # row is a dict
                        if column_id in order_data[i]:
                            if not int(order_dict[self.DIRECTION]):
                                #dont sort on this column
                                del(order_data[i])
                                break
                            else:
                                order_data[i][column_id].update(order_dict)
                                break
                        else:
                            # add new sort col
                            new_column_defs.append({column_id:order_dict})
                        
                for col in new_column_defs:
                    # add new sort columns
                    order_data.append(col)
                    
                # session[self.HEADER_NAME][table_name][self.ORDERS_NAME] = order_data
        # always return something
        return 'Ok'
        
        
    def _save_list_filter(self,*args,**kwargs):
        """Save the user's list filter"""
        
        table_name = request.form.get('table_name')
        
        if table_name:
            session_data = self._create_filter_session(table_name)
            
            # import pdb;pdb.set_trace()
            filter_dict = self.filter_dict.copy()
            for k,v in self.filter_dict.items():
                filter_dict[k] = request.form.get(k)
            
            if request.form.get(self.DOM_ID):
                session[self.HEADER_NAME][table_name][self.FILTERS_NAME][request.form.get(self.DOM_ID)] = filter_dict
                
        return 'Ok' #always return something...
        
        