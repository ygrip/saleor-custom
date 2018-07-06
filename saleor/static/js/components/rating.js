import Vue from 'vue';
import StarRating from 'vue-star-rating';
import swal from 'sweetalert2';

Vue.component('star-rating', StarRating);

console.log('rating module loaded');

$(document).ready(() => {
  if ($('#app-products').length) {
    new Vue({
      el: '#app-products',
      methods: {
        setRating(rating) {
        	var product = document.getElementById('app-products');
	     	this.rating = rating;
	     	update_rating(product.dataset.product_id, rating)
	    },
	    showCurrentRating(rating) {
	     	this.currentRating = (rating === 0) ? this.currentSelectedRating : rating;
	    },
	    setCurrentSelectedRating(rating) {
	     	this.currentSelectedRating = rating;
	     	console.log(`selected ${rating}`);
	    },
      },
      data: {
	    rating: 0,
	    currentRating: '',
	    currentSelectedRating: '',
	    boundRating: 5,
      },
    });
	    $('.vue-star-rating div').each(function(index) {
	    	$(this).css('margin', '0 auto');
	    });
  }
});

function update_rating(product_id, value){
	var csrftoken = getCookie('csrftoken');
  $.ajax({

    type: 'POST',
    url: '/api/update/rating/',
    data: {
      product_id:product_id,
      value:value,
      csrfmiddlewaretoken: csrftoken,
    },
    crossDomain: 'true',
    success(response) {
    	console.log(response);
    	console.log(response.success);
      if(response.success==true){
      	location.reload();
      }else{
      	if('url' in response){
      		swal({
		        type: 'warning',
		        title: 'Authentication needed!',
		        html:
			    'Please click this </b>, ' +
			    '<a href="'+response.url+'">links</a> ' +
			    'to authenticate yourself',
		        text: response.message,
		        showCloseButton: true,
				showCancelButton: true,
				showConfirmButton: false,
		    })
      	}else{
	  		swal({
		        type: 'error',
		        title: 'Oops...',
		        text: response.message,
		        showCloseButton: true,
				showCancelButton: true,
				showConfirmButton: false,
		    })
      	}
      }
    },
    error (xhr, status) {
      swal({
        type: 'error',
        title: 'Oops...',
        text: 'Something went wrong! '+status,
      })
    },
});
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}