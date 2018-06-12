import 'slider-pro'
import * as Vibrant from 'node-vibrant'

$(function() {
	$('#home-slider').sliderPro({
		'width' : '100%',
		'height' : 480,
		'arrows' : true,
		'autoplayOnHover': false,
		'touchSwipe' : false,
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
		},
		init: function(event){
			var element = this.getSlideAt(0);
			var image_path = element.$mainImage['0'].dataset.default;
			console.log(image_path);
			var opts = {
				colorCount : 1,
				quality : 1,		
			}
			
			var v  = Vibrant.from(image_path,opts);
			v.getPalette((err,palette)=>setColor(palette.Muted._rgb.toString()));
		},
		gotoSlideComplete: function(event){
			console.log(event.index);
			var element = this.getSlideAt(event.index);
			var image_path = element.$mainImage['0'].dataset.default;
			console.log(image_path);
			var opts = {
				colorCount : 1,
				quality : 1,		
			}
			
			var v  = Vibrant.from(image_path,opts);
			v.getPalette((err,palette)=>setColor(palette.DarkVibrant._rgb.toString()));
		},
	});

	var count = $('.sp-bottom-thumbnails div').children('.sp-thumbnail').length;
	var dynamic_width = 100 / (count);

	$('.sp-thumbnail-container').width(dynamic_width+'%');
	console.log(dynamic_width);
});

function setColor(color){
	color = 'rgba('+color+',.9)';
	console.log(color);
	$('.sp-image-container').css('background',color);
}