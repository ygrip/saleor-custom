import "ez-plus"
import "lightgallery"
import "lg-thumbnail"
import "lg-fullscreen"
var randomColor = require('randomcolor'); 

$(function() {
	var $count = 0;
	var $custom_item = $("#lightgallery");
    $('.carousel-item').each(function(i, obj) {
	    //test
	    $('#image-product-active-'+i).ezPlus({
			zoomType: 'lens',
		    lensShape: 'round',
		    containLensZoom: true,
		    lensSize:150,
			scrollZoom: true,
			responsive: true
		}); 
		console.log(i);
		$count++;
	});	

    var baseColor = randomColor({hue:'blue'});
    var color = randomColor({'count':$count,luminosity: 'dark',format: 'rgba',hue:baseColor,alpha:0.3});

    console.log(color);
	$custom_item.lightGallery({
		thumbnail:true,
		animateThumb: false,
   		showThumbByDefault: false,
		mode: 'lg-fade'
	});

	$custom_item.on('onBeforeSlide.lg', function(event, prevIndex, index){
	    $('.lg-outer').css('background-color', color[index])
	});

	$('.lg-outer').css({"transition": "background-color 600ms ease 0s"});
});

