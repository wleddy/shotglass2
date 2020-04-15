<script>
    $(document).ready(function(){   
        {#
        filters:[{< DOM id of input element>:{'kind':<'text' | 'date'>,'field_name':<field name>,'value':< filter value >,'start':<start date>,'end':< end date>},{...},],
        orders:[{< DOM id of field>,'field_name':<field name>,'direction':<int>},{...},],

        Session field constants:
        sf.HEADER_NAME = 'table_filters'
        sf.FILTERS_NAME = 'filters'
        sf.FIELD_NAME = 'field_name'
        sf.DOM_ID = 'id'
        sf.VALUE = 'value'
        sf.TYPE = 'kind'
        sf.DATE_START = 'start'
        sf.DATE_END = 'end'
        sf.ORDERS_NAME = 'orders'
        sf.DIRECTION = 'direction'
        #}
        
      {% set table_search_column =  '' %}
      {% set table_search_text =  '' %}
      {% set table_name = data.table.table_name %}
      {% set id_prefix = ''%}
      {% set sf = session_fields %}
      // {{ table_name }}
      {% if sf.HEADER_NAME in session %}
      // has table_filters
          {% set table_search = session[sf.HEADER_NAME] %}
          {% if table_name in table_search %}
              {% set search_data = table_search[table_name][sf.FILTERS_NAME] %}
              {% for k,v in search_data.items() %}
                  {% set id_prefix =  k %}
                  {% if sf.FIELD_NAME in v %}
                      {% set table_search_column =  v[sf.FIELD_NAME] %}
                  {% endif %}
                  {% if sf.VALUE in v %}
                     {% set table_search_text =  v[sf.VALUE] %}
                  {% endif %}
                  {% if sf.DATE_START in v %}
                     {% set start =  v[sf.DATE_START] %}
                  {% endif %}
                  {% if sf.DATE_END in v %}
                     {% set end =  v[sf.DATE_END] %}
                  {% endif %}
                  {% if sf.TYPE in v %}
                     {% set kind =  v[sf.TYPE] %}
                  {% endif %}
                  {% if kind == 'date'%}
                  $('#'+'{{id_prefix}}'+'start_date').val('{{ start }}'); 
                  $('#'+'{{id_prefix}}'+'end_date').val('{{ end }}'); 
                  {% else %}
                  $('#'+'{{id_prefix}}'+'col_select').val('{{ table_search_column }}'); 
                  $('#'+'{{id_prefix}}'+'search_input').val('{{ table_search_text }}').focus(); 
                  {% endif %}
              {% endfor %}
          {% endif %}
      {% endif %}

    })
</script>