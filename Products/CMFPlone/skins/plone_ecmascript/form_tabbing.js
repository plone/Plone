/*
 * This is the code for the tabbed forms. It assumes the following markup:
 *
 * <form class="enableFormTabbing">
 *   <fieldset id="fieldset-[unique-id]">
 *     <legend id="fieldsetlegend-[same-id-as-above]">Title</legend>
 *   </fieldset>
 * </form>
 *
 * or the following
 *
 * <dl class="enableFormTabbing">
 *   <dt id="fieldsetlegend-[unique-id]">Title</dt>
 *   <dd id="fieldset-[same-id-as-above]">
 *   </dd>
 * </dl>
 *
 */

// TODO: selection lists not yet updated

var ploneFormTabbing = {
        // standard jQueryTools configuration options for all form tabs
        jqtConfig:{effect:'fade',current:'selected'}
    };

ploneFormTabbing._buildTabs = function(container, legends) {
    var threshold = legends.length > 6;
    var panel_ids, tab_ids = [], tabs = '';

    for (var i=0; i < legends.length; i++) {
        var className, tab, legend = legends[i], lid = legend.id;
        tab_ids[i] = '#' + lid;

        switch (i) {
            case (0):
                className = 'class="formTab firstFormTab"';
                break;
            case (legends.length-1):
                className = 'class="formTab lastFormTab"';
                break;
            default:
                className = 'class="formTab"';
                break;
        }

        if (threshold) {
            tab = '<option '+className+' id="'+lid+'" value="'+lid+'">';
            tab += jq(legend).text()+'</option>';
        } else {
            tab = '<li '+className+'><a href="#'+lid+'"><span>';
            tab += jq(legend).text()+'</span></a></li>';
        }

        tabs += tab;
        jq(legend).hide();
    }

    tab_ids = tab_ids.join(',');
    panel_ids = tab_ids.replace(/#fieldsetlegend-/g, "#fieldset-");

    if (threshold) {
        tabs = jq('<select class="formTabs">'+tabs+'</select>');
    } else {
        tabs = jq('<ul class="formTabs">'+tabs+'</ul>');
    }

    return tabs.get(0);
};


ploneFormTabbing.initializeDL = function() {
    var ftabs = jq(ploneFormTabbing._buildTabs(this, jq(this).children('dt')));
    var targets = jq(this).children('dd');
    jq(this).before(ftabs);
    targets.addClass('formPanel');
    ftabs.tabs(targets, ploneFormTabbing.jqtConfig);
};


ploneFormTabbing.initializeForm = function() {
    var fieldsets = jq(this).children('fieldset');

    if (!fieldsets.length) {return;}

    var ftabs = ploneFormTabbing._buildTabs(
        this, fieldsets.children('legend'));
    jq(this).prepend(ftabs);
    fieldsets.addClass("formPanel");


    // The fieldset.current hidden may change, but is not content
    jq(this).find('input[name=fieldset.current]').addClass('noUnloadProtection');

    jq(this).find('.formPanel:has(div.field span.fieldRequired)').each(function() {
        var id = this.id.replace(/^fieldset-/, "#fieldsetlegend-");
        jq(id).addClass('required');
    });

    // set the initial tab
    var initialIndex = 0;
    var count = 0;
    var found = false;
    jq(this).find('.formPanel').each(function() {
        if (!found && jq(this).find('div.field.error, input[name=fieldset.current][value^=#]')) {
            initialIndex = count;
            found = true;
        }
        count += 1;
    });

    jq(this).children('ul.formTabs')
        .tabs('form.enableFormTabbing fieldset', ploneFormTabbing.jqtConfig || {'initialIndex':initialIndex});

    jq("#archetypes-schemata-links").addClass('hiddenStructure');
    jq("div.formControls input[name=form.button.previous]," +
      "div.formControls input[name=form.button.next]").remove();

};

jq(function() {
    jq("form.enableFormTabbing,div.enableFormTabbing").each(ploneFormTabbing.initializeForm);
    jq("dl.enableFormTabbing").each(ploneFormTabbing.initializeDL);

    //Select tab if it's part of the URL
    if (window.location.hash) {
        var id = window.location.hash.replace(/^#fieldset-/, "#fieldsetlegend-");
        jq(".enableFormTabbing .formtab a[href='" + id + "']").click();
    }
});
