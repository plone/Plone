// To avoid conflicts, use the 'jq' variable instead of the $ variable
var jq = jQuery.noConflict();

// If cssQuery is not defined (loaded earlier), redefine it in terms of jQuery
// For everything but corner cases, this is good enough
if (typeof cssQuery == 'undefined') {
    function cssQuery(s, f) { return jq.makeArray(jq(s, f)) };
};

// load jQuery Plone plugins on load
(function($) {
    $(function() {
        // Highlight search results, but ignore referrals from our own domain
        // when displaying search results.
        $('#region-content,#content').highlightSearchTerms({
            includeOwnDomain: $('dl.searchResults').length == 0
        });
    });
})(jQuery);
