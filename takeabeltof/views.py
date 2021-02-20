from flask import request, session, g, url_for, \
     render_template, render_template_string, redirect, flash, Response
from flask.views import View
from shotglass2.shotglass import get_site_config, is_ajax_request
from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.date_utils import date_to_string, local_datetime_now
from shotglass2.takeabeltof.utils import printException, cleanRecordID, DataStreamer
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.jinja_filters import plural, iso_date_string, local_date_string, excel_date_and_time_string
from datetime import date


class TableView:
    """A generic class based view for a table"""

    def __init__(self,table,db,**kwargs):
        # import pdb;pdb.set_trace()
        self.source = table # SqliteTable class
        self.db = db # Database connection
        self.table = self.source(self.db)
        self.display_name = self.table.display_name
        self.sql = None # may be used for a custom select
        self.recs = None

        self.list_fields = kwargs.get('list_fields',None) # define the fields (by name) to display in list
        if not self.list_fields:
            self.list_fields = self._set_default_list_fields() # set the defaults if needed
        self.has_search_fields = False # set to true if any fields have search == true
        
        # set options for export
        self.export_fields = kwargs.get('export_fields',None) # define the fields (by name) to display in list
        self.export_template = kwargs.get('export_temlate',None)
        self.export_title = kwargs.get('export_title',None)
        self.export_file_name = kwargs.get('export_file_name',None)
            
        # templates to use in the list view by default
        self.list_template = 'list_template.html'
        # These are includes in the main list template, so may want to point to a different file
        self.list_table_template = 'list_template_table.html'
        self.list_search_widget_template = 'list_search_widget.html'
        self.list_search_widget_extras_template = 'list_search_widget_extras.html'
        self.list_header_row_template = 'list_header_row.html'
        self.list_search_widget_ready_template = 'list_search_widget_ready.js'
        self.list_order_ready_temlate = 'list_order_ready.js'
        self.list_export_widget_template = 'list_export_widget.html'
        self.allow_record_addition = True #Set false to hide the 'add new record' link in the list page
        
        self.edit_template = 'edit_template.html'
        
        # set the page title root
        g.title = self.display_name
        
        # Include any text you want inserted into the page <head> section
        self.head = ''
            
        # import pdb;pdb.set_trace()
        self.path = [x for x in request.path.split('/') if x]
        if not self.path:
            self.path = ['/']
        self.root = self.path.pop(0)
        
        self.handlers = ['/','edit','delete','filter','order','export']
        
        self._ajax_request = is_ajax_request()
        
        
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
                        if self._ajax_request:
                            resp = 'success' if self.success else 'failue: {}'.format(self.result_text)
                            return resp
                            # redirect to clear the old path name in browser
                        return redirect(g.listURL)
                    if handler == 'filter':
                        return ListFilter()._save_list_filter()
                    if handler == 'order':
                        return ListFilter()._save_list_order()
                    if handler == 'export':
                        # export the currently selected records
                        return self.export()
                    
        return self.list(**kwargs)
        
        
    def export(self,**kwargs):
        """Export the current record selection as .csv file"""
        
        # import pdb;pdb.set_trace()
        
        # provide for case where recs are set extenally
        if not self.recs:
            self.select_recs(**kwargs)
        if self.recs:
            if self.export_file_name:
                filename = self.export_file_name
            else:
                filename = "{table_name}_report_{datetime}.csv".format(
                            table_name = self.table.display_name,
                            datetime = date_to_string(local_datetime_now(),'iso_datetime'),
                            ).replace(' ','_').lower()
                        
            if not self.export_fields:
                # include all fields by default
                self.export_fields = self._set_default_list_fields(include_all=True).copy()

            self.set_list_fields(self.export_fields)
            
            
            if self.export_template:
                result = render_template(self.export_template, data=self)
            else:
                # add a descriptive title row
                if self.export_title:
                    result = self.export_title.strip() + '\n'
                else:
                    result = "Export of table {} as of {}\n".format(self.table.table_name,excel_date_and_time_string(local_datetime_now()))
                        
                result += ','.join([x['label'] for x in self.export_fields]) + '\n'
                for rec in self.recs:
                    rec_row = []
                    for field in self.export_fields:
                        data = rec.__getattribute__(field['name'])
                        if field['type'].upper() == "DATE":
                            data = local_date_string(data)
                        elif field['type'].upper() == "DATETIME":
                            data = excel_date_and_time_string(data)
                        else:
                            # just text
                            data = str(data).strip()
                            
                            # replace double quotes with double-double quotes
                            data = data.replace('"','""') #double up on double quotes
                        
                            if "," in data:
                                # if any commas, wrap in quotes
                                data = '"' + data + '"'
                            
                            #replace returns
                            data = data.replace('\r\n',' -crnl- ')
                            data = data.replace('\n',' -nl- ')
                            data = data.replace('\r',' -rtn- ')

                        rec_row.append(data)
                        
                    result += ','.join([str(x) for x in rec_row]) + '\n'
                    
            return DataStreamer(result,filename,'text/csv').send()
        
        self.result_text = "No records selected"
        self.success = False
        
        flash(self.result_text)
        return self.list(**kwargs)
        
        
        
    def list(self,**kwargs):
        """Return the response text for flask request"""
        # import pdb;pdb.set_trace()
        g.title = "{} Record List".format(g.title)
                
        self.select_recs(**kwargs)
        
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
                        
    def _set_default_list_fields(self,include_all=False):
        """Set up the default fields for the list view if not provided
        
        if include_all, include all fields in list. Primarily for export list.
        """
        default_list_fields = []
        col_num = -1
        max_cols = 5 if not include_all else 99999
        
        for col in self.table.get_column_names():
            if len(default_list_fields) > max_cols:
                break
            
            if col[-3:].lower() == '_id' and not include_all:
                # foreign key
                continue
        
            col_num += 1
            
            default_list_fields.append({
                'name':'{}'.format(col),
                # limit the number of visible fields on small screen
                'class':'{}'.format('w3-hide-small' if len(default_list_fields) == 0 or len(default_list_fields) > 3  else ''),                
                })
                
        return default_list_fields
                    
                    
    def make_label(self,name):
        if not isinstance(name,str):
            return name
        else:
            return name.replace('_',' ').title()
            

    def get_list_filters(self):
        """return a ListFilter object populated with the query 'where' and 'order_by' sql strings"""
        # look in session for the saved search...
        filters = ListFilter()
        filters.get_list_filter(self.table)
        return filters
        
        
    def select_recs(self,**kwargs):
        """Make a selection of recs based on the current filters"""
        if self.sql:
            # self.sql is assumed to be a fully formed sql statement
            self.recs = self.table.query(self.sql)
        else:
            filters = self.get_list_filters()
            self.recs = self.table.select(where=filters.where,order_by=filters.order_by,**kwargs)
        

    def set_list_fields(self,fields):
        """Ensure that fields is a list of dicts and that the dicts have
        all the required keys
        
        6/16/20 - 
            Add 'list' attribute to determine if a field is to be included in list.
            Defaults to True. This allows you to include it in the search widget without
            displaying the field in the list.
        """
        # import pdb;pdb.set_trace()
        
        if not fields:
            fields = []
                
        list_fields_temp = [x for x in fields] # make a copy
            
        if not isinstance(fields,list):
            fields = [fields]
            
        for field in fields:
            if isinstance(field,str):
                # assume to be a field name
                field = {'name':field,'label':'{}'.format(self.make_label(field)),'class':'','search':True,'type':"TEXT",'list':True}
            if not isinstance(field,dict):
                continue # it must be a dict
            for x in range(len(list_fields_temp)-1,-1,-1): # turkey shoot loop
                default_field_dict = {'label':'','class':'','search':True}
                if not isinstance(list_fields_temp[x],dict) or 'name' not in list_fields_temp[x]:
                    # bad element got into fields somehow...
                    del list_fields_temp[x]
                    continue
                if list_fields_temp[x].get('name',False) == field.get('name',None):
                    default_field_dict = {'label':'','class':'','search':True,'type':'TEXT','default':'','list':True}
                    for k in default_field_dict.keys():
                        if k in field:
                            default_field_dict.update({k:field[k]})
                        elif k == 'type':
                            field_type = "TEXT"
                            try:
                                field_type = self.table.get_column_type(field['name'])
                            except KeyError:
                                # the field name may be defined in the query 
                                pass
                            default_field_dict.update({k:field_type})
                                
                    break
                        
            list_fields_temp[x].update(default_field_dict)
            list_fields_temp[x]['label'] = list_fields_temp[x]['label'] if list_fields_temp[x]['label'] else self.make_label(list_fields_temp[x]['name'])
            if list_fields_temp[x]['search']:
                self.has_search_fields = True
                
        fields = list_fields_temp
        
        
class EditView():
    """Generic handling of edit requests"""

    def __init__(self,table,db,rec_id=None,**kwargs):
        self.db = db
        self.table = table(self.db)
        self.success = True
        self.result_text = ''
        self.stay_on_form = False
        self.form_template = "edit_template.html"
        self.rec_id = rec_id
        self._validate_rec_id() # self.rec_id may have a value now
        self.get() # could be an empty (new) record, existing record or None
        self.edit_fields = kwargs.get('edit_fields',None) # define the fields (by name) to display in list
        if not self.edit_fields:
            self.edit_fields = self._set_default_edit_fields() # set the defaults if needed
        self._set_edit_fields() # ensure that all dictionaries are complete


    def after_get_hook(self):
        """ do anything you want here"""
        pass
        
        
    def before_commit_hook(self):
        # a place to put some code after the record is saved, but before it's committed
        pass
        
        
    def get(self):
        # Select an existing record or make a new one
        if not self.rec_id:
            self.rec = self.table.new()
        else:
            self.rec = self.table.get(self.rec_id)
        if not self.rec:
            self.result_text = "Unable to locate that record"
            flash(self.result_text)
            self.success = False

        self.after_get_hook()
            

    def render(self):
        self._set_edit_fields()
        return render_template(self.form_template, 
            data = self,
            )
            
            
    def save(self):
        try:
            self.table.save(self.rec)
            self.rec_id = self.rec.id
    
        except Exception as e:
            self.db.rollback()
            self.result_text = printException('Error attempting to save {} record.'.format(self.table.display_name),"error",e)
            flash(self.result_text)
            self.success = False
            return
    
        self.before_commit_hook() # anyting special you want to do
        if not self.success:
            self.db.rollback()
            if not self.result_text:
                self.result_text = "Unknown error in before_commit_hook"
            printException(self.result_text,'error')
            raise RuntimeError
            
        self.table.commit()


    def update(self,save_after_update=True):
        # import pdb;pdb.set_trace()
        if request.form:
            self.table.update(self.rec,request.form)
            if self.validate_form():
                if save_after_update:
                    self.save()
            else:
                self.success = False
                self.result_text = "Form Validation Failed"
        else:
            self.success = False
            self.result_text = "No input form provided"


    def validate_form(self):
        valid_form = True
        self._set_edit_fields()
        for field in self.edit_fields:
            if field['name'] in request.form and field['req']:
                val = self.rec.__getattribute__(field['name'])
                if isinstance(val,str):
                    val = val.strip()
                if not val:
                    self.result_text = "You must enter a value for {}".format(field['name'])
                    flash(self.result_text)
                    self.success = False
                    valid_form = False
                
        return valid_form


    def _set_edit_fields(self):
        """ensure that each dict in self.edit_list is complete
        """
        # Must always have the 'id' field
        has_id = False
        
        # import pdb;pdb.set_trace()
        
        for field in self.edit_fields:
            if not field['name']:
                raise ValueError("The 'name' property in edit_fields may not be empty ")
                break
            
            if field['name'] == 'id':
                has_id = True
                
            # special case
            if 'label' not in field or not field['label']:
                field['label'] = field['name'].replace('_',' ').title()
            
            for k, v in self._get_field_list_dict().items():
                if k not in field:
                    field[k] = v
                    
        if not has_id:
            #add an id field
            # import pdb;pdb.set_trace()
            id_field = self._get_field_list_dict()
            id_field.update({'name':'id','type':'hidden','default':0})
            self.edit_fields.append(id_field)
    

    def _get_field_list_dict(self):
        # ensure that all the required elements are in the field list dictionary
        return {'name':'',
                'label':None,
                'type':'text',
                'class':None, 
                'req':False,
                'default':'',
                'placeholder':None,
                'extras':None,
                }
            
            
    def _set_default_edit_fields(self):
        """Set up the default fields for the edit view if not provided
        """
        default_edit_fields = []

        for col in self.table.get_column_names():
            req = False
            if col[-3:].lower() == '_id':
                # foreign key
                req = True
                
            dict_template = self._get_field_list_dict()
            
            dict_template['name'] = '{}'.format(col)
            dict_template['label'] = '{}'.format(col).replace('_',' ').title()
            dict_template['type'] = 'text'
            try:
                dict_template['type'] = '{}'.format(self.table.get_column_type(col))
            except KeyError:
                pass
            dict_template['req'] = req
            
            default_edit_fields.append(dict_template)
    
        return default_edit_fields


    def _validate_rec_id(self):
        if not self.rec_id:
            self.rec_id = request.form.get('id',request.args.get('id',0))

        self.rec_id = cleanRecordID(self.rec_id)

        if self.rec_id < 0:
            self.result_text = "That is not a valid ID"
            self.success = False
            raise ValueError(self.result_text)


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
        self.where = '1'
        self.order_by = 'id'
        if not isinstance(table,SqliteTable):
            return
            
        # get the column names for the table
        table_column_names = table.get_column_names()
        
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
                    
                    # if the column name is a physical column in the primary table
                    #   prepend the column name with the table name to avoid ambiguous column names
                    if col in table_column_names and '.' not in col:
                        col = table.table_name + '.' + col
                        
                    if kind == 'date':
                        start = iso_date_string(start if start else self.BEGINNING_OF_TIME)
                        end = iso_date_string(end if end else self.END_OF_TIME)
                        # print(start,end)
                        where_list.append("""date({col}) >= date('{start}') and date({col}) <= date('{end}')""".format(col=col,start=start,end=end))
                        # print(where_list[-1])
                    else:
                        where_list.append("""{col} LIKE '%{val}%'""".format(col=col,val=str(val).lower()))
                        
                        
            # import pdb;pdb.set_trace()
            order_list = []
            for order_data in session_data[table.table_name][self.ORDERS_NAME]:
                for dom_id in order_data.keys():
                    col = order_data[dom_id].get(self.FIELD_NAME)
                    direction = int(order_data[dom_id].get(self.DIRECTION,0)) #direction will be -1,0 or 1
                    if col and direction:
                        
                        # if the column name is a physical column in the primary table
                        #   prepend the column name with the table name to avoid ambiguous column names
                        #   Same as above, but not sure it's really needed in order by...
                        if col in table_column_names and '.' not in col:
                            col = table.table_name + '.' + col

                        direction = 'DESC' if direction < 0 else 'ASC'
                        collate = ''
                        field_type = "TEXT"
                        try:
                            field_type = table.get_column_type(order_data[dom_id]['field_name'])
                        except KeyError:
                            # the field name may be defined in the query 
                            pass
                        if field_type.lower() == "text":
                            collate = 'COLLATE NOCASE'
                        order_list.append("""{col} {collate} {direction}""".format(col=col,collate=collate,direction=direction))
        
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
        
        