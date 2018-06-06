import 'slider-pro'

$(function() {
	$('#home-slider').sliderPro({
		'width' : '100%',
		'height' : 480,
		'arrows' : true,
		'autoplayOnHover': 'none',
		'waitForLayers' : true,
		'fade' : true,
		'autoplay' : true,
		'autoScaleLayers' : true,
		'keyboardOnlyOnFocus' : true,
		'imageScaleMode': 'contain',
		'centerImage': true,
		'orientation': 'horizontal',
		'loop' : true,
		'buttons': false,
		'thumbnailPointer': true,
		'thumbnailHeight' : 30,
		'breakpoints': {
			500: {
				'height'  : 550,
				'width' : '60%',
				'arrows' : false,
			}
		}
	});

	var count = $('.sp-bottom-thumbnails div').children('.sp-thumbnail').length;
	var dynamic_width = 100 / (count);

	$('.sp-thumbnail-container').width(dynamic_width+'%');
	console.log(dynamic_width);
});