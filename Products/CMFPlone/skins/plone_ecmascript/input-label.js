/* This looks for input fields with a title and the class "inputLabel". When
   the field is empty the title will be set as it's value and the class
   "inputLabel" will be replaced with the class "inputLabelActive" to make
   it styleable with css. When the field gets focus, the content is removed
   and the class "inputLabelActive" is removed. When the field looses focus,
   then the game starts again if the value is empty, if not then the field
   is left as is. When the form is submitted, the values are cleaned up
   before they are sent to the server.
*/

var ploneInputLabel = {
    focus: function() {
        var t = jq(this);
        if (t.hasClass('inputLabelActive') && t.val() == t.attr('title'))
            t.val('').removeClass('inputLabelActive');
    },

    blur: function() {
        var t = jq(this);
        if (!t.val())
            t.addClass('inputLabelActive').val(t.attr('title'));
    },

    submit: function() {
        jq('input[title].inputLabelActive').filter(function() {
            return jq(this).val() == this.title;
        }).val('').removeClass('inputLabelActive');
    }
};

jq(function() {
    jq('form:has(input[title].inputLabel)').submit(ploneInputLabel.submit);
    jq('input[title].inputLabel')
        .focus(ploneInputLabel.focus)
        .bind('blur.ploneInputLabel', ploneInputLabel.blur)
        .trigger('blur.ploneInputLabel'); // Apply the title
});
