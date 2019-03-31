/*
    Some optional scripts to use with the anytime date-time picker objrects
*/

/* From the docs... The "on-demand" picker
    Allow direct input until button is clicked

    <input type="text" id="ButtonCreationDemoInput"/>
      <button id="ButtonCreationDemoButton">
        <img src="calendar.png" alt="[calendar icon]"/>
        </button>
      <script>

*/
$('#ButtonCreationDemoButton').click(
  function(e) {
    $('#start_date').AnyTime_noPicker().AnyTime_picker({format: "%m/%d/%y"}).focus();
    e.preventDefault();
    } );


/* From the docs... The "Tab-over" function

    Start cursor here: <input type="text"/>
    Optional picker: <input type="text" id="tabOverDemoInput"/>
    <input type="button" id="tabOverDemoClear" value="Clear"/>
    Tab to here: <input type="text"/>
    <script>

*/
(function tabOverDemoSetup() {
$('#tabOverDemoInput').
  click( function(e) { $(this).off('click').AnyTime_picker().focus(); } ).
  keydown(
    function(e) {
      var key = e.keyCode || e.which;
      if ( ( key != 16 ) && ( key != 9 ) ) { // shift, del, tab
        $(this).off('keydown').AnyTime_picker().focus();
        e.preventDefault();
        }
      } );
$('#tabOverDemoClear').
  click(
    function() {
      $('#tabOverDemoInput').AnyTime_noPicker().val('');
      tabOverDemoSetup();
      } );
})();


