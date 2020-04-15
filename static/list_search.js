// Handle the list search for new style search widget

function setDBsearch(table_name,which,session_save_URL,result_target_URL){
    // alert('boing!')
        var dom_id = $(which).attr('id_prefix')
        var kind = $(which).attr('kind');
        var field_name = $(which).attr('name');
        var startDate = '';
        var endDate = '';
        var value = '';
        if (kind == 'date'){
            startDate = $('#'+dom_id+'start_date').val();
            endDate = $('#'+dom_id+'end_date').val();
        } else {
        var value = $('#'+dom_id+'search_input').val();
        var field_name = $('#'+dom_id+'col_select').val();
        }

        $.ajaxSetup({async:false});
        $.post(session_save_URL,{ 'id': dom_id, 'value': value, 'table_name':table_name, 'field_name':field_name,'kind':kind,'start':startDate,'end':endDate })
       
        $.ajaxSetup({async:true});
        doDBsearch(result_target_URL);
    }
   
function doDBsearch(result_target_URL){
    // trigger a database search and have the results loaded into current page
    $("#sg-table-list").load(result_target_URL)
}

// add the clear imput icon to imput with class 'deletable'
$(document).ready(function() {
    $('input.deletable').wrap('<span class="deleteicon" />').after($('<span/>').click(function() {
        $(this).prev('input').val('').trigger('keyup').trigger('change');
    }));
});
