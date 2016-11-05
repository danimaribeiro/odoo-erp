$.fn.priceformat = function() {
	this.priceFormat({
		prefix : '',
		centsSeparator : ',',
		thousandsSeparator : '.'
	});
}

fieldsmasks = function() {
	$(".field_phoneformat").mask("(999) 999-9999");
	$(".field_priceformat").mask("99.99");
}

$.fn.historicformat = function(options) {
	this.maskDigits(options);
}

$.fn.planocontaformat = function(options) {
	this.maskDigits(options);
}