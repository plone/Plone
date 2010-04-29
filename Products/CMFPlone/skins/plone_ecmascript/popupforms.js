/******
    Standard popups
******/

var common_content_filter = '#content>*:not(div.configlet),dl.portalMessage.error,dl.portalMessage.info';

jQuery(function($){
    
    // method to show error message in a noform
    // situation.
    function noformerrorshow(el, noform) {
        var o = $(el);
        var emsg = o.find('dl.portalMessage.error');
        if (emsg.length) {
            o.children().replaceWith(emsg);
            return false;
        } else {
            return noform;
        }
    }

    // After deletes we need to redirect to the target page.
    function redirectbasehref(el, responseText) {
        var mo = responseText.match(/<base href="(.+?)"/i);
        if (mo.length === 2) {
            return mo[1];
        }
        return location;
    }

    // login form
    $('#portal-personaltools a[href$=/login], #portal-personaltools a[href$=/login_form], .discussion a[href$=/login_form]').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form#login_form',
            noform: function () {
                if (location.href.search(/pwreset_finish$/) >= 0) {
                    return 'redirect';
                } else {
                    return 'reload';
                }
            },
            redirect: function () {
                var href = location.href;
                if (href.search(/pwreset_finish$/) >= 0) {
                    return href.slice(0, href.length-14) + 'logged_in';
                } else {
                    return href;
                }
            }
        }
    );

    // contact form
    $('#siteaction-contact a').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form',
            noform: function(el) {return noformerrorshow(el, 'close');}
        }
    );

    // display: select content item / change content item
    $('#contextSetDefaultPage, #folderChangeDefaultPage').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form[name="default_page_form"]',
            noform: function(el) {return noformerrorshow(el, 'reload');},
            closeselector: '[name=form.button.Cancel]',
            width:'40%'
        }
    );

    // advanced state
    $('dl#plone-contentmenu-workflow a#advanced').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form',
            noform: function(el) {return noformerrorshow(el, 'reload');},
            closeselector: '[name=form.button.Cancel]'
        }
    );
    
    // Delete dialog
    $('dl#plone-contentmenu-actions a#delete').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form',
            noform: function(el) {return noformerrorshow(el, 'redirect');},
            redirect: redirectbasehref,
            closeselector: '[name=form.button.Cancel]',
            width:'50%'
        }
    );

    // Rename dialog
    $('dl#plone-contentmenu-actions a#rename').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            closeselector: '[name=form.button.Cancel]',
            width:'40%'
        }
    );

    // Select default view dialog
    $('dl#plone-contentmenu-display a#contextSetDefaultPage').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form',
            noform: function(el) {return noformerrorshow(el, 'reload');},
            closeselector: '[name=form.button.Cancel]'
        }
    );

    // registration
    $('#portal-personaltools a[href$=/@@register]').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form.kssattr-formname-register'
        }
    );

    // add new user, group
    $('form[name=users_add], form[name=groups_add]').prepOverlay(
        {
            subtype: 'ajax',
            filter: common_content_filter,
            formselector: 'form.kssattr-formname-new-user, form[name="groups"]',
            noform: function(el) {return noformerrorshow(el, 'redirect');},
            redirect: function () {return location.href;}
        }
    );

    // Content history popup
    $('#content-history a').prepOverlay({
       subtype: 'ajax', 
       urlmatch: '@@historyview',
       urlreplace: '@@contenthistorypopup'
    });

});

