import "ez-plus"
import "lightgallery"
import "lg-thumbnail"
import "lg-fullscreen"
import "lg-autoplay"
import "lg-share"
var randomColor = require('randomcolor'); 

$(function() {
	var $count = 0;
	var $custom_item = $("#lightgallery");
    $('.carousel-item').each(function(i, obj) {
	    //test
		$count++;
	});	

	$('.image-details').ezPlus({
		zoomType: 'lens',
	    lensShape: 'round',
	    containLensZoom: true,
	    lensSize:150,
		scrollZoom: true,
		responsive: true
	}); 

    var baseColor = randomColor({hue:'blue'});
    var color = randomColor({'count':$count,luminosity: 'dark',format: 'rgba',hue:baseColor,alpha:0.3});

	$custom_item.lightGallery({
		thumbnail:true,
		animateThumb: false,
   		showThumbByDefault: false,
		mode: 'lg-fade'
	});

	$('.lg-outer').css({"transition": "background-color 600ms ease 0s"});

	$custom_item.on('onBeforeSlide.lg', function(event, prevIndex, index){
	    $('.lg-outer').css('background-color', color[index])
	});
});

