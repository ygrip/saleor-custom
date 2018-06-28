import Vue from 'vue'
import StarRating from 'vue-star-rating'
Vue.component('star-rating', StarRating)

console.log('rating module loaded')

$( document ).ready(function() {
	new Vue({
		el: '#app-products',
		methods : {
			setRating: function(rating) {
		      this.rating = "you have selected "+rating;
		      console.log(this.rating);
		    },
		    showCurrentRating: function(rating) {
		      this.currentRating = (rating === 0) ? this.currentSelectedRating :  rating;
		    },
		    setCurrentSelectedRating: function(rating) {
		      this.currentSelectedRating =  rating;
		      console.log("selected "+rating);
		    }
		},
		data: {
		    rating: "",
		    currentRating: "",
		    currentSelectedRating: "",
		    boundRating: 5,
		}
	});
    $('.vue-star-rating div').each(function(index){
    	$(this).css('margin','0 auto')
    });
});