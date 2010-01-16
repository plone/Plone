/* Scan all headlines in the #content area 
* add a generated anchor and link based on title 
*/

(function($) { $(function() {
  var content = getContentArea();
  if (!content) return;
    //find all headers in content area, filter matched set to remove any pre-existing anchors
    var headers =  $(content).find(':header').not(':header:has(a)'); 
    headers.each(function(){ 
        //clean text to strip illegal URL characters
        var friendly_title = $(this).text().trim().replace(/[\<\>!@#\$%^&\*,\s]/g,'-');
        $(this).wrapInner('<a class="link-anchor" href=#' + friendly_title + ' name=' + friendly_title + '></a>');
      }     
      );

}); })(jQuery);


