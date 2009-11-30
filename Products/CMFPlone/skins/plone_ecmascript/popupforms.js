/******
    Standard popups
******/
jq(function(){
    // login form
    jq('#portal-personaltools a[href$=/login], #portal-personaltools a[href$=/login_form]').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*',
            formselector: 'form#login_form',
            noform: 'reload'
        }
    );

    // contact form
    jq('#siteaction-contact a').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*',
            formselector: 'form',
            noform: 'close'
        }
    );

    // display: select content item / change content item
    jq('#contextSetDefaultPage, #folderChangeDefaultPage').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*',
            formselector: 'form',
            noform: 'reload'
        }
    );

    // advanced state
    jq('dl#plone-contentmenu-workflow a#advanced').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*',
            formselector: 'form',
            noform: 'reload',
            closeselector: '[name=form.button.Cancel]'
        }
    );
    
    // delete / rename confirmation dialog
    jq('#plone-contentmenu-actions a#delete, #plone-contentmenu-actions a#rename').prepOverlay(
        {
            subtype:'ajax',
            filter: '#content>*',
            closeselector: '[name=form.button.Cancel]'
        }
    );

    // registration
    jq('#portal-personaltools a[href$=/@@register]').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*',
            formselector: 'form.kssattr-formname-register',
        }
    );

    // add new user
    jq('form[name=users_add]').prepOverlay(
        {
            subtype: 'ajax',
            filter: '#content>*',
            formselector: 'form.kssattr-formname-new-user',
            noform: 'close'
        }
    );

});

