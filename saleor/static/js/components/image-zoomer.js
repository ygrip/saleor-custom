import "ez-plus"
import "lightgallery"
import "lg-thumbnail"
import "lg-fullscreen"

alert("outside")

$(function() {
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
	});

    console.log('loaded')
	
});

$("#lightgallery").lightGallery({
		thumbnail:true
	});