// script to insert in head for mobile keypad widget
$().ready(function(){
    $('.keypad_input').css('touch-action','none').prop('readonly','readonly').focus(open_keypad)
})

function open_keypad(){
    value = this.value;
    $('#keypad_window #keypad_value').text(value);
    input_id = this.id;
    $('#keypad_window #input_id').text(input_id)
    label = $("#" + input_id ).attr('label')
    $('#keypad_window #keypad_header').text(label)
    $('#keypad_window').show();
}
function keypad_done() {
    value = $('#keypad_window #keypad_value').text();
    target_id = $('#keypad_window #input_id').text();
    $('#' + target_id).val((value));
    $('#keypad_window').hide();
}   

function keypad_cancel() {
    $('#keypad_window').hide();
}
function keypad_clear() {
    $('#keypad_window #keypad_value').text('');
}
function keypad_backspace() {
    value = $('#keypad_window #keypad_value').text();
    if (value.length > 0) {
        value = value.substr(0,value.length-1);
        $('#keypad_window #keypad_value').text(value);
    }
}
function keypad_value(which) {
    value = $('#keypad_window #keypad_value').text();
    $('#keypad_window #keypad_value').text(value + which.textContent);
}
