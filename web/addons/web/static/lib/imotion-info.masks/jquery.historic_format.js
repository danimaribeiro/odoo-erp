(function($) {
	$.fn.historicMask = function(options) {

		var defaults = {
			limitBefore : 2,
			limitAfter : 2
		};

		var options = $.extend(defaults, options);

		return this.each(function() {
			var obj = $(this);
			var is_number = /[0-9]/;

			var separator = '.';
			var limitBefore = options.limitBefore;
			var limitAfter = options.limitAfter;

			function to_numbers(str) {

				var formatted = '';
				for ( var i = 0; i < (str.length); i++) {
					char_ = str.charAt(i);

					if (formatted.length == 0 && char_ == 0)
						char_ = false;

					if (char_ && char_.match(is_number)) {
						formatted = formatted + char_;
					}
				}
				return formatted;
			}

			function fill_with_zeroes(str) {
				while (str.length < (limitBefore + limitAfter))
					str = '0' + str;
				return str;
			}

			function historic_format(str) {

				var formatted = fill_with_zeroes(to_numbers(str));

				var afterVal = formatted.substr(formatted.length - limitAfter,
						limitAfter);
				var beforeVal = formatted.substr(0, limitBefore);

				formatted = beforeVal + separator + afterVal;

				return formatted;

			}

			function key_check(e) {

				var code = (e.keyCode ? e.keyCode : e.which);

				var typed = String.fromCharCode(code);

				var functional = false;
				var str = obj.val();
				var newValue = historic_format(str + typed);

				if ((code >= 48 && code <= 57) || (code >= 96 && code <= 105))
					functional = true;

				// check Backspace, Tab, Enter, Delete, and left/right arrows
				if (code == 8)
					functional = true;
				if (code == 9)
					functional = true;
				if (code == 13)
					functional = true;
				if (code == 46)
					functional = true;
				if (code == 37)
					functional = true;
				if (code == 39)
					functional = true;
				if (code == 189 || code == 109)
					functional = true; // dash as well

				if (!functional) {
					e.preventDefault();
					e.stopPropagation();
					if (str != newValue)
						obj.val(newValue);
				}
			}

			function format_it() {
				var str = obj.val();
				var format = historic_format(str);
				if (str != format)
					obj.val(format);
			}

			$(this).bind('keydown', key_check);
			$(this).bind('keyup', format_it);

			if ($(this).val().length > 0) {
				format_it();
			}
		});
	};

})(jQuery);

var widgetControlForm = function(obj) {
	var views = {
		fields : [ 'formatohistorico.tree' ]
	}
	var result = false;
	$.each(views, function(index, value) {
		result = value.toString() === obj.name;
	});

	if (result)
		$(".oe_vm_switch_form").css("display", "none");
};
