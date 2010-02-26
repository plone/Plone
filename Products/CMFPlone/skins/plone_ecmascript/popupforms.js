/******
    Standard popups
******/
jq(function(){
    // login form
    jq('#portal-personaltools a[href$=/login], #portal-personaltools a[href$=/login_form]').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*:not(div.configlet),dl.portalMessage.error,dl.portalMessage.info',
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
    jq('#siteaction-contact a').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*:not(div.configlet),dl.portalMessage.error,dl.portalMessage.info',
            formselector: 'form',
            noform: 'close'
        }
    );

    // display: select content item / change content item
    jq('#contextSetDefaultPage, #folderChangeDefaultPage').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*:not(div.configlet),dl.portalMessage.error,dl.portalMessage.info',
            formselector: 'form[name="default_page_form"]',
            noform: 'reload',
            closeselector: '[name=form.button.Cancel]'
        }
    );

    // advanced state
    jq('dl#plone-contentmenu-workflow a#advanced').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*:not(div.configlet),dl.portalMessage.error,dl.portalMessage.info',
            formselector: 'form',
            noform: 'reload',
            closeselector: '[name=form.button.Cancel]'
        }
    );

    // registration
    jq('#portal-personaltools a[href$=/@@register]').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*:not(div.configlet),dl.portalMessage.error,dl.portalMessage.info',
            formselector: 'form.kssattr-formname-register'
        }
    );

    // add new user, group
    jq('form[name=users_add], form[name=groups_add]').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*:not(div.configlet),dl.portalMessage.error,dl.portalMessage.info',
            formselector: 'form.kssattr-formname-new-user, form[name="groups"]',
            noform: function (el) {
                var o = jQuery(el);
                var emsg = o.find('dl.portalMessage.error');
                if (emsg.length) {
                    o.children().replaceWith(emsg);
                    return false;
                } else {
                    return 'redirect';
                }
            },
            redirect: function () {
                return location.href;
            }
        }
    );

    // Content history popup
    jq('#content-history a').prepOverlay({
       subtype: 'ajax', 
       urlmatch: '@@historyview',
       urlreplace: '@@contenthistorypopup'
    });

});

