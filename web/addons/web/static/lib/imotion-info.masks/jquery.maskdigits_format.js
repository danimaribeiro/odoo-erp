(function($) {
	$.fn.maskDigits = function(options) {
		var defaults = {
			separator : ".",
			digits : [ 2, 2 ]
		};
		var options = $.extend(defaults, options);

		return this
				.each(function() {
					var obj = $(this);
					var is_number = /[0-9]/;
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
						var total = 0;

						$.each(options.digits, function(i, v) {
							total += v;
						});
						while (str.length < total) {
							str = '0' + str;
						}
						return str;
					}

					function digit_formatted(str) {

						var format = fill_with_zeroes(to_numbers(str));
						var formatted = [];
						var string = "";
						for ( var i = options.digits.length; i > 0; i--) {
							var start = format.length - options.digits[i - 1]
									- string.length;
							string += format.substr(start,
									options.digits[i - 1]);
							formatted.push(format.substr(start,
									options.digits[i - 1]));
						}

						return formatted.reverse().join(options.separator);
					}

					function key_check(e) {

						var code = (e.keyCode ? e.keyCode : e.which);

						var typed = String.fromCharCode(code);

						var functional = false;
						var str = obj.val();
						var newValue = digit_formatted(str + typed);

						if ((code >= 48 && code <= 57)
								|| (code >= 96 && code <= 105))
							functional = true;
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
							functional = true;

						if (!functional) {
							e.preventDefault();
							e.stopPropagation();
							if (str != newValue)
								obj.val(newValue);
						}
					}

					function format_it() {

						var str = obj.val();
						var formatted = digit_formatted(str);
						if (str != formatted)
							obj.val(formatted);
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
		$(".oe_vm_switch_list").css("display", "none");
};
