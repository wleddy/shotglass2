<script>
    $(document).ready(function(){
        resetOrderClasses();
        {#
        'orders':[{'id':< DOM id of column element>:[{'field_name':<field name>,'direction':<int>},{...},]

        Session field constants:
        sf.HEADER_NAME = 'table_filters'
        sf.ORDERS_NAME = 'orders'
        sf.DOM_ID = 'id'
        sf.DIRECTION = 'direction'
        #}
        
      {% set table_name = data.table.table_name %}
      {% set field_name = [""] %}
      {% set direction = [""] %}
      {% set dom_id = [""] %}
      {% set sf = session_fields %}
      {% if sf.HEADER_NAME in session %}
        {% set order_data = session[sf.HEADER_NAME] %}
        // {{ order_data }}
        {% if table_name in order_data %}
            {% set order_data = order_data[table_name][sf.ORDERS_NAME] %}
            // {{ order_data }}
            {% for row in order_data %}
                // {{ row }}
                {% for id in row.keys() %}
                    {% if sf.DIRECTION in row[id] %}
                        // {{ row[id][sf.DIRECTION] }}
                        $('#'+'{{id}}').attr('{{ sf.DIRECTION }}','{{ row[id][sf.DIRECTION] }}'); 
                        setOrderClasses('{{id}}','{{row[id][sf.DIRECTION]}}')
                     {% endif %}
                {% endfor %}
            {% endfor %}
        {% endif %}
      {% endif %}

    })
</script>